from src.bot import IBot
from src.geometry import Direction, Coordinate, directions
from src.snake import Snake

import random


class Bot(IBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.i = 0
        
    def chooseDirection(self, snake: Snake, opponent: Snake, mazeSize: Coordinate, apple: Coordinate) -> Direction:
        possible_directions = []

        for d in directions:
            new_head = snake.head.moveTo(d)

            if new_head.inBounds(mazeSize)\
                    and new_head not in snake.elements\
                    and new_head not in opponent.elements:

                possible_directions.append(d)

        return random.choice(possible_directions if possible_directions else directions)