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


# Quadratic penalties for surroundings
class Bot(IBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseMaze = None
        self.apple = None
        self.mazeWithApple = None

    def initMaze(self, mazeSize):
        self.baseMaze = []
        for y in range(mazeSize.y):
            self.baseMaze.append([0 for x in range(mazeSize.x)])

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

        possible_directions = []

        for d in directions:
            new_head = snake.head.moveTo(d)

            if new_head.inBounds(mazeSize) \
                    and new_head not in snake.elements \
                    and new_head not in opponent.elements:
                possible_directions.append((d, maze[new_head.x][new_head.y]))

        if possible_directions:
            return max(possible_directions, key=lambda d: d[1])[0]
        else:
            return random.choice(directions)
