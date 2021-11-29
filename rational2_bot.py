from src.bot import IBot
from src.geometry import Direction, Coordinate, directions
from src.snake import Snake

import random
from copy import deepcopy
from collections import Counter

EDGE_PENALTY = -1
CORNER_PENALTIES = [-5, -4, -3, -2, -1]
OPPONENT_HEAD_PENALTIES = [0, -2, -1]
SNAKE_PENALTY = -10
APPLE_REWARD = list(range(15, 0, -1))


def setValuesAroundCell(maze, mazeSize, cell, values, accumulate=True):
    updated = {cell}
    queue = [(cell, 0)]  # (cell, distance)
    max_distance = len(values)

    while queue:
        current, distance = queue.pop(0)
        if accumulate:
            maze[current.x][current.y] += values[distance]
        else:
            maze[current.x][current.y] = values[distance]

        for d in directions:
            neighbor = current.moveTo(d)
            if distance + 1 < max_distance and neighbor not in updated and neighbor.inBounds(mazeSize):
                updated.add(neighbor)
                queue.append((neighbor, distance + 1))

    return updated


# Avoids dead zones
class Bot(IBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseMaze = None
        self.apple = None
        self.mazeWithApple = None

    def initMaze(self, mazeSize):
        self.baseMaze = []
        for y in range(mazeSize.y):
            self.baseMaze.append([0 for _ in range(mazeSize.x)])

        # penalize edges
        for y in range(mazeSize.y):
            self.baseMaze[0][y] += EDGE_PENALTY
            self.baseMaze[mazeSize.x - 1][y] += EDGE_PENALTY

        for x in range(1, mazeSize.x - 1):
            self.baseMaze[x][0] += EDGE_PENALTY
            self.baseMaze[x][mazeSize.y - 1] += EDGE_PENALTY

        # penalize corners
        setValuesAroundCell(self.baseMaze, mazeSize, Coordinate(0, 0), CORNER_PENALTIES, False)
        setValuesAroundCell(self.baseMaze, mazeSize, Coordinate(mazeSize.x - 1, 0), CORNER_PENALTIES, False)
        setValuesAroundCell(self.baseMaze, mazeSize, Coordinate(0, mazeSize.y - 1), CORNER_PENALTIES, False)
        setValuesAroundCell(self.baseMaze, mazeSize, Coordinate(mazeSize.x - 1, mazeSize.y - 1), CORNER_PENALTIES, False)


    def chooseDirection(self, snake: Snake, opponent: Snake, mazeSize: Coordinate, apple: Coordinate) -> Direction:
        if self.baseMaze is None:
            self.initMaze(mazeSize)

        if apple != self.apple:
            self.apple = apple
            self.mazeWithApple = deepcopy(self.baseMaze)
            # apple reward
            setValuesAroundCell(self.mazeWithApple, mazeSize, apple, APPLE_REWARD)

        maze = deepcopy(self.mazeWithApple)

        # opponent's potential moves
        setValuesAroundCell(maze, mazeSize, opponent.head, OPPONENT_HEAD_PENALTIES)

        # surroundings
        surroundings = Counter()
        for each in snake.body[1:-1] + opponent.body[1:-1]:
            for d in directions:
                neighbor = each.moveTo(d)
                if neighbor.inBounds(mazeSize):
                    surroundings.update({neighbor: 1})

        for each in surroundings:
            maze[each.x][each.y] -= surroundings[each] ** 2

        # snakes themselves
        for each in snake.elements:
            maze[each.x][each.y] = SNAKE_PENALTY
        for each in opponent.elements:
            maze[each.x][each.y] = SNAKE_PENALTY

        # just for visualisation
        maze[snake.head.x][snake.head.y] -= 1
        maze[opponent.head.x][opponent.head.y] -= 2

        cells_to_avoid = set()
        # prevent collision with opponent's head
        if len(snake.body) <= len(opponent.body):
            for d in directions:
                cells_to_avoid.add(opponent.head.moveTo(d))

        # avoid dead zones
        occupation = []
        for y in range(mazeSize.y):
            occupation.append([0 for _ in range(mazeSize.x)])
        for i, each in enumerate(snake.body[::-1]):
            occupation[each.x][each.y] = i + 1
        for i, each in enumerate(opponent.body[::-1]):
            occupation[each.x][each.y] = i + 1

        def path_exists(cell, length, visited=[]):
            move = len(visited) + 1
            # print('-' * move + '>' + str(cell))
            if not cell.inBounds(mazeSize):
                return False
            elif occupation[cell.x][cell.y] >= move:
                return False
            elif move == length:
                return True
            else:
                for d in directions:
                    if path_exists(cell.moveTo(d), length, visited + [cell]):
                        return True
            return False

        for d in directions:
            neighbor = snake.head.moveTo(d)
            if neighbor not in cells_to_avoid\
                    and neighbor.inBounds(mazeSize) \
                    and neighbor not in snake.elements \
                    and neighbor not in opponent.elements:
                    # and not path_exists(neighbor, len(snake.body)):
                # print('Exploration for length: ' + str(len(snake.body)))
                if not path_exists(neighbor, len(snake.body)):
                    cells_to_avoid.add(neighbor)

        possible_directions = []
        safe_directions = []

        for d in directions:
            new_head = snake.head.moveTo(d)

            if new_head.inBounds(mazeSize) \
                    and new_head not in snake.elements \
                    and new_head not in opponent.elements:
                possible_directions.append((d, maze[new_head.x][new_head.y]))
                if new_head not in cells_to_avoid:
                    safe_directions.append((d, possible_directions[-1]))

        if safe_directions:
            return max(possible_directions, key=lambda d: d[1])[0]
        elif possible_directions:
            return max(possible_directions, key=lambda d: d[1])[0]
        else:
            return random.choice(directions)
