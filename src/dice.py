"""
Класс Dice - управление бросками костей
"""

import random


class Dice:
    def __init__(self):
        self.values: tuple[int, int] = (0, 0)
        self.is_double: bool = False
        self.double_count: int = 0

    def roll(self) -> tuple[int, int]:
        self.values = (random.randint(1, 6), random.randint(1, 6))
        self.is_double = self.values[0] == self.values[1]

        if self.is_double:
            self.double_count += 1
        else:
            self.double_count = 0

        return self.values

    def get_sum(self) -> int:
        return sum(self.values)

    def reset_double_count(self):
        self.double_count = 0
