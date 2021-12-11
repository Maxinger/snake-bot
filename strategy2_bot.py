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


def pathExists(move, length, occupation, mazeSize, visited=[]):
    distance = len(visited) + 1
    if move in visited:
        return False
    elif occupation[move.x][move.y] >= distance:
        return False
    elif distance == length:
        return True
    else:
        for n in neighbors(move, mazeSize):
            if pathExists(n, length, occupation, mazeSize, visited + [move]):
                return True
    return False


def allowedMoves(cell, mazeSize, occupation):
    for d in directions:
        move = cell.moveTo(d)
        if move.inBounds(mazeSize) and occupation[move.x][move.y] == 0:
            yield move


def simulateMove(move, snake, occupation):
    occupation[move.x][move.y] = len(snake)
    for i, c in enumerate(snake[::-1]):
        occupation[c.x][c.y] -= 1


def rollbackMove(move, snake, occupation):
    occupation[move.x][move.y] = 0
    for i, c in enumerate(snake[::-1]):
        occupation[c.x][c.y] += 1


def isMoveSafe(move, snake, opponent, occupation, mazeSize, depth, predefinedOpponentMove=None):
    if occupation[move.x][move.y] > 0:
        return False
    elif depth == 1:
        res = pathExists(move, len(snake), occupation, mazeSize)
        return res
    else:
        try:
            opponentMoves = [predefinedOpponentMove]\
                if predefinedOpponentMove\
                else [m for m in allowedMoves(opponent[0], mazeSize, occupation)]

            simulateMove(move, snake, occupation)

            if len(opponentMoves) == 1:
                if move == opponentMoves[0]:
                    return len(snake) > len(opponent)
            else:
                # check for possible heads collision
                if opponent[0].getDistance(move) == 1 and len(snake) <= len(opponent):
                    return False

            if not opponentMoves:
                # opponent has no moves (heads collision is considered above)
                return True
            else:
                for opponentMove in opponentMoves:
                    try:
                        simulateMove(opponentMove, opponent, occupation)

                        safeMoveExists = False
                        for nextMove in allowedMoves(move, mazeSize, occupation):
                            if isMoveSafe(nextMove, [move] + snake[:-1], [opponentMove] + opponent[:-1], occupation, mazeSize, depth - 1):
                                safeMoveExists = True
                                break
                        if not safeMoveExists:
                            return False
                    finally:
                        rollbackMove(opponentMove, opponent, occupation)
        finally:
            rollbackMove(move, snake, occupation)

    return True


# Detects losing and winning moves with given depth
class Bot(IBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseMaze = None
        self.apple = None
        self.mazeWithApple = None
        self.centeredMaze = None
        self.center = None
        self.lastMaze = None

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
        winning_cells = set()

        # avoid dead zones
        occupation = []
        for y in range(mazeSize.y):
            occupation.append([0 for _ in range(mazeSize.x)])
        for i, cell in enumerate(snake.body[::-1]):
            occupation[cell.x][cell.y] = i + 1
        for i, cell in enumerate(opponent.body[::-1]):
            occupation[cell.x][cell.y] = i + 1

        for move in allowedMoves(snake.head, mazeSize, occupation):
            if not isMoveSafe(move, snake.body, opponent.body, occupation, mazeSize, 3):
                cells_to_avoid.add(move)
                # for debug
                # if path_exists(neighbor, len(snake.body)) and len(snake.body) > len(opponent.body):
                #     isMoveSafe(neighbor, snake.body, opponent.body, occupation, mazeSize, 3)

        for move in allowedMoves(snake.head, mazeSize, occupation):
            if move not in cells_to_avoid:
                winning = True
                for opponentMove in allowedMoves(opponent.head, mazeSize, occupation):
                    if isMoveSafe(opponentMove, opponent.body, snake.body, occupation, mazeSize, 3, move):
                        winning = False
                if winning:
                    winning_cells.add(move)
                    # for debug
                    # if snake.head.getDistance(opponent.head) > 2:
                    #     pass

        possible_directions = []
        risky_directions = []
        safe_directions = []
        winning_directions = []

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
                if new_head in winning_cells:
                    winning_directions.append(direction_tuple)
                elif new_head in cells_to_avoid:
                    risky_directions.append(direction_tuple)
                else:
                    safe_directions.append(direction_tuple)

        if winning_directions:
            result = max(winning_directions, key=lambda d: d[1])[0]
        elif safe_directions:
            result = max(safe_directions, key=lambda d: d[1])[0]
        elif risky_directions:
            result = max(risky_directions, key=lambda d: d[1])[0]
        elif possible_directions:
            result = max(possible_directions, key=lambda d: d[1])[0]
        else:
            result = random.choice(directions)

        self.lastMaze = maze
        return result
