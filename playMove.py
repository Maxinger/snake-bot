from src.importsTools import import_bot
from src.geometry import Coordinate
from src.snake import Snake


def to_coordinate(string):
    x, y = string.split()
    return Coordinate(int(x), int(y))


mazeSize = Coordinate(14, 14)

snake_body = [to_coordinate(s) for s in
              ['4 9', '3 9', '3 8', '3 7', '2 7', '2 8', '2 9', '2 10', '2 11', '3 11', '4 11', '5 11']]
opponent_body = [to_coordinate(s) for s in
                 ['5 10', '5 9', '5 8', '5 7', '6 7', '6 8', '6 9', '7 9', '8 9', '8 8', '8 7']]

apple = Coordinate(13, 0)

snake = Snake(mazeSize, set(snake_body), snake_body)
opponent = Snake(mazeSize, set(opponent_body), opponent_body)

bot = import_bot('rational2_bot.py')
bot.chooseDirection(snake, opponent, mazeSize, apple)
