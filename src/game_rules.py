"""
Класс GameRules - правила игры
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from property import Property, PropertyGroup


class GameRules:
    def __init__(
        self,
        start_money: int = 1500,
        salary_amount: int = 200,
        max_houses: int = 4,
        auction_enabled: bool = False,
        jail_fine: int = 50,
    ):
        self.start_money = start_money
        self.salary_amount = salary_amount
        self.max_houses = max_houses
        self.auction_enabled = auction_enabled
        self.jail_fine = jail_fine
        self.max_jail_turns = 3

    def check_monopoly(self, player: "Player", group: "PropertyGroup") -> bool:
        if not group:
            return False

        for property in group.properties:
            if property.owner != player:
                return False
        return True

    def can_build_house(self, property: "Property") -> bool:
        if not property.owner or not property.group:
            return False

        # Нужна монополия
        if not self.check_monopoly(property.owner, property.group):
            return False

        # Не должна быть заложена
        if property.mortgaged:
            return False

        # Не превышен лимит домов
        if property.houses >= self.max_houses:
            return False

        return True
