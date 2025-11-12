"""
Класс Property - представление недвижимости
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from player import Player


class PropertyGroup:
    def __init__(self, name: str, color: str):
        self.name = name
        self.color = color
        self.properties: list["Property"] = []

    def add_property(self, property: "Property"):
        if property not in self.properties:
            self.properties.append(property)


class Property:
    def __init__(
        self,
        name: str,
        position: int,
        price: int,
        rent: int,
        group: Optional[PropertyGroup] = None,
    ):
        self.name = name
        self.position = position
        self.price = price
        self.rent = rent
        self.owner: Optional["Player"] = None
        self.mortgaged: bool = False
        self.group = group
        self.houses: int = 0

        if group:
            group.add_property(self)

    def calculate_rent(self, tenant: "Player") -> int:
        if self.mortgaged or not self.owner or self.owner == tenant:
            return 0

        rent_amount = self.rent

        # Проверка монополии (владелец владеет всеми объектами в группе)
        if self.group and self._check_monopoly():
            # Если нет домов, удвоить аренду за монополию
            if self.houses == 0:
                rent_amount *= 2
            else:
                # Если есть дома, увеличить аренду
                rent_amount *= 1 + self.houses

        return rent_amount

    def _check_monopoly(self) -> bool:
        if not self.group or not self.owner:
            return False

        for prop in self.group.properties:
            if prop.owner != self.owner:
                return False
        return True

    def mortgage(self) -> int:
        if not self.mortgaged and self.houses == 0:
            self.mortgaged = True
            return self.price // 2
        return 0

    def on_landing(self, player: "Player"):
        # Это метод для полиморфизма с Cell
        pass
