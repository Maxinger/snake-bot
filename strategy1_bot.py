from src.bot import IBot
from src.geometry import Direction, Coordinate, directions
from src.snake import Snake

import random
from copy import deepcopy

EDGE_PENALTY = -1
CORNER_PENALTIES = [-5, -4, -3, -2, -1]
OPPONENT_HEAD_PENALTIES = [0, -2, -1]
SNAKE_PENALTY = -11
APPLE_REWARDS = [10, 8, 6, 4, 2]
CENTER_REWARDS = [12, 10, 8, 6, 4, 2]


def neighbors(cell, mazeSize):
    for d in directions:
        neighbor = cell.moveTo(d)
        if neighbor.inBounds(mazeSize):
            yield neighbor


def setValuesToNeighbors(maze, mazeSize, updated, queue, values, accumulate):
    max_distance = len(values)

    while queue:
        current, distance = queue.pop(0)
        if accumulate:
            maze[current.x][current.y] += values[distance]
        else:
            maze[current.x][current.y] = values[distance]

        for neighbor in neighbors(current, mazeSize):
            if distance + 1 < max_distance and neighbor not in updated:
                updated.add(neighbor)
                queue.append((neighbor, distance + 1))

    return updated


def setValuesAroundCell(maze, mazeSize, cell, values, accumulate=True):
    updated = {cell}
    queue = [(cell, 0)]  # (cell, distance)
    return setValuesToNeighbors(maze, mazeSize, updated, queue, values, accumulate)


def setValuesAroundSquare(maze, mazeSize, topLeftCell, values, accumulate=True):
    updated = set()
    queue = []  # (cell, distance)
    for x in (topLeftCell.x, topLeftCell.x + 1):
        for y in (topLeftCell.y, topLeftCell.y + 1):
            cell = Coordinate(x, y)
            updated.add(cell)
            queue.append((cell, 0))

    return setValuesToNeighbors(maze, mazeSize, updated, queue, values, accumulate)


# Goes to the center if the opponent is going to reach the apple faster
class Bot(IBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseMaze = None
        self.apple = None
        self.mazeWithApple = None
        self.centeredMaze = None
        self.center = None

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

        self.centeredMaze = deepcopy(self.baseMaze)
        setValuesAroundSquare(self.centeredMaze, mazeSize, Coordinate(mazeSize.x // 2 - 1, mazeSize.y // 2 - 1), CENTER_REWARDS, False)

        self.center = Coordinate((mazeSize.x - 1) / 2, (mazeSize.y - 1) / 2)

    def chooseDirection(self, snake: Snake, opponent: Snake, mazeSize: Coordinate, apple: Coordinate) -> Direction:
        if self.baseMaze is None:
            self.initMaze(mazeSize)

        if apple != self.apple:
            self.apple = apple
            self.mazeWithApple = deepcopy(self.baseMaze)
            # apple reward
            setValuesAroundCell(self.mazeWithApple, mazeSize, apple, APPLE_REWARDS)

        concedeApple = snake.head.getDistance(apple) > opponent.head.getDistance(apple)

        maze = deepcopy(self.centeredMaze if concedeApple else self.mazeWithApple)

        # opponent's potential moves
        if len(snake.body) <= len(opponent.body):
            setValuesAroundCell(maze, mazeSize, opponent.head, OPPONENT_HEAD_PENALTIES)

        # snakes themselves
        for cell in snake.elements:
            maze[cell.x][cell.y] = SNAKE_PENALTY
        for cell in opponent.elements:
            maze[cell.x][cell.y] = SNAKE_PENALTY - 1

        # just for visualisation
        maze[snake.head.x][snake.head.y] -= 10
        maze[opponent.head.x][opponent.head.y] -= 10

        cells_to_avoid = set()

        # avoid dead zones
        occupation = []
        for y in range(mazeSize.y):
            occupation.append([0 for _ in range(mazeSize.x)])
        for i, cell in enumerate(snake.body[::-1]):
            occupation[cell.x][cell.y] = i + 1
        for i, cell in enumerate(opponent.body[::-1]):
            occupation[cell.x][cell.y] = i + 1

        def path_exists(cell, length, visited=[]):
            move = len(visited) + 1
            if cell in visited:
                return False
            elif occupation[cell.x][cell.y] >= move:
                return False
            elif move == length:
                return True
            else:
                for n in neighbors(cell, mazeSize):
                    if path_exists(n, length, visited + [cell]):
                        return True
            return False

        for neighbor in neighbors(snake.head, mazeSize):
            if neighbor not in cells_to_avoid\
                    and neighbor not in snake.elements\
                    and neighbor not in opponent.elements\
                    and not path_exists(neighbor, len(snake.body)):
                cells_to_avoid.add(neighbor)

        possible_directions = []
        risky_directions = []
        safe_directions = []

        opponent_moves = set(neighbors(opponent.head, mazeSize))

        for d in directions:
            new_head = snake.head.moveTo(d)

            if new_head.inBounds(mazeSize) \
                    and new_head not in snake.elements \
                    and new_head not in opponent.elements:

                value = maze[new_head.x][new_head.y]
                if concedeApple:
                    value += (1 - new_head.getMathDistance(self.center) / mazeSize.x)  # prefer cells closer to center
                else:
                    value += (1 - new_head.getDistance(apple) / mazeSize.x)  # prefer cells closer to apple
                direction_tuple = (d, value)
                possible_directions.append(direction_tuple)
                # prevent collision with opponent's head
                if new_head not in cells_to_avoid:
                    if len(snake.body) <= len(opponent.body) and new_head in opponent_moves:
                        risky_directions.append(direction_tuple)
                    else:
                        safe_directions.append(direction_tuple)

        if safe_directions:
            result = max(safe_directions, key=lambda d: d[1])[0]
        elif risky_directions:
            result = max(risky_directions, key=lambda d: d[1])[0]
        elif possible_directions:
            result = max(possible_directions, key=lambda d: d[1])[0]
        else:
            result = random.choice(directions)

        return result
