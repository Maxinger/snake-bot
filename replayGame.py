from src.importsTools import import_bot
from src.geometry import Coordinate, Direction, UP, RIGHT, LEFT, DOWN
from src.game import Game


def to_coordinate(string):
    x, y = string.split()
    return Coordinate(int(x), int(y))


def overrideChooseDirection(bot, moves):
    originalMethod = bot.chooseDirection

    def chooseDirection(snake, opponent, mazeSize, apple):
        original = originalMethod(snake, opponent, mazeSize, apple)
        return moves.pop(0) if moves else original

    bot.chooseDirection = chooseDirection


head1 = Coordinate(7, 6)
tailDir1 = DOWN
moves1 = [RIGHT, RIGHT]

head2 = Coordinate(6, 9)
tailDir2 = UP
moves2 = [DOWN, DOWN]

apples = [to_coordinate(s) for s in
          ['3 11']]


class ReplayGame(Game):

    @property
    def randomNonOccupiedCell(self):
        return apples.pop(0) if apples else super().randomNonOccupiedCell


bot1 = import_bot('strategy1_bot.py')
bot2 = import_bot('random_bot.py')

overrideChooseDirection(bot1, moves1)
overrideChooseDirection(bot2, moves2)

game = ReplayGame(head1, tailDir1, head2, tailDir2, 3, Coordinate(14, 14), (bot1, bot2))

gameIter = game.__iter__()
for _ in gameIter:
    print(f"Snake1: {game.bot1_runner.lastMove} \tSnake2: {game.bot2_runner.lastMove}")

states = gameIter.getStates()
