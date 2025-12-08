"""
Базовые модели игры Монополия
Соответствуют DESC.md и диаграмме классов
"""

import random
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional


class CellType(Enum):
    """Типы клеток на игровом поле"""

    PROPERTY = "property"
    CARD = "card"
    TAX = "tax"
    JAIL = "jail"
    START = "start"
    FREE_PARKING = "free_parking"
    GO_TO_JAIL = "go_to_jail"


class Player:
    """
    Участник игры (человек или ИИ)
    Назначение: хранит состояние участника и интерфейс для действий
    """

    def __init__(self, player_id: str, name: str, is_ai: bool = False):
        self.id = player_id
        self.name = name
        self.is_ai = is_ai
        self.balance = 1500  # Стартовый капитал
        self.position = 0
        self.properties: List["PropertyCell"] = []
        self.cards: List["ActionCard"] = []
        self.in_jail = False
        self.jail_turns_left = 0
        self.bankrupt = False

    def move_to(self, position: int):
        """Устанавливает позицию игрока"""
        self.position = position

    def add_property(self, cell: "PropertyCell"):
        """Добавляет собственность игроку"""
        if cell not in self.properties:
            self.properties.append(cell)

    def remove_property(self, cell: "PropertyCell"):
        """Удаляет собственность у игрока"""
        if cell in self.properties:
            self.properties.remove(cell)

    def adjust_balance(self, delta: int) -> int:
        """Изменяет баланс локально"""
        self.balance += delta
        return self.balance

    def add_card(self, card: "ActionCard"):
        """Добавляет карточку в инвентарь"""
        self.cards.append(card)

    def use_card(self, card: "ActionCard") -> bool:
        """Использует карточку из инвентаря"""
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def __str__(self):
        return f"{self.name} ({'AI' if self.is_ai else 'Human'}): ${self.balance}, pos {self.position}"


class Cell(ABC):
    """
    Базовый тип клетки с общими полями
    """

    def __init__(self, cell_id: str, name: str, cell_type: CellType, position: int):
        self.id = cell_id
        self.name = name
        self.type = cell_type
        self.position = position

    @abstractmethod
    def on_land(self, player: Player, context: "TurnManager") -> Dict:
        """Точка входа обработки клетки"""
        pass


class PropertyCell(Cell):
    """
    Покупаемая клетка с владельцем, арендой, строительством и залогом
    """

    def __init__(
        self,
        cell_id: str,
        name: str,
        position: int,
        price: int,
        color_group: str,
        base_rent: int,
        house_cost: int = 50,
    ):
        super().__init__(cell_id, name, CellType.PROPERTY, position)
        self.price = price
        self.owner: Optional[Player] = None
        self.rent_table = {
            0: base_rent,
            1: base_rent * 2,
            2: base_rent * 4,
            3: base_rent * 6,
            4: base_rent * 8,
            5: base_rent * 10,
        }
        self.color_group = color_group
        self.build_level = 0  # 0-4 дома, 5 отель
        self.is_mortgaged = False
        self.house_cost = house_cost
        self.hotel_cost = house_cost
        self.base_rent = base_rent

    def has_monopoly(self, board: "Board") -> bool:
        """Проверяет полное владение группой"""
        if not self.owner:
            return False
        group_cells = board.get_group_cells(self.color_group)
        return all(cell.owner == self.owner for cell in group_cells)

    def calculate_rent(self) -> int:
        """Вычисляет аренду с учетом buildLevel, залога, монополии"""
        if self.is_mortgaged or not self.owner:
            return 0
        return self.rent_table.get(self.build_level, self.base_rent)

    def can_build(self, board: "Board") -> bool:
        """Проверяет возможность строительства"""
        if self.is_mortgaged or not self.has_monopoly(board):
            return False
        # Проверка равномерности
        group_cells = board.get_group_cells(self.color_group)
        min_level = min(cell.build_level for cell in group_cells)
        return self.build_level == min_level

    def can_sell_building(self, board: "Board") -> bool:
        """Проверяет возможность сноса"""
        if self.build_level == 0:
            return False
        group_cells = board.get_group_cells(self.color_group)
        max_level = max(cell.build_level for cell in group_cells)
        return self.build_level == max_level

    def mark_mortgaged(self):
        """Ставит флаг залога"""
        self.is_mortgaged = True

    def redeem_mortgage(self):
        """Снимает залог"""
        self.is_mortgaged = False

    def upgrade_building(self):
        """Увеличивает buildLevel"""
        if self.build_level < 5:
            self.build_level += 1

    def downgrade_building(self):
        """Уменьшает buildLevel"""
        if self.build_level > 0:
            self.build_level -= 1

    def on_land(self, player: Player, context: "TurnManager") -> Dict:
        """Обработка попадания на собственность"""
        if not self.owner:
            return {"action": "purchase_offer", "property": self}
        elif self.owner != player:
            return {"action": "pay_rent", "property": self, "owner": self.owner}
        else:
            return {"action": "own_property", "property": self}


class StartCell(Cell):
    """Клетка Старт"""

    def __init__(self, position: int = 0):
        super().__init__("start", "Старт", CellType.START, position)
        self.pass_bonus = 200

    def on_land(self, player: Player, context: "TurnManager") -> Dict:
        return {"action": "start", "bonus": self.pass_bonus}


class TaxCell(Cell):
    """Клетка налога"""

    def __init__(self, cell_id: str, name: str, position: int, tax_amount: int):
        super().__init__(cell_id, name, CellType.TAX, position)
        self.tax_amount = tax_amount

    def on_land(self, player: Player, context: "TurnManager") -> Dict:
        return {"action": "pay_tax", "amount": self.tax_amount}


class JailCell(Cell):
    """Клетка тюрьмы"""

    def __init__(self, position: int):
        super().__init__("jail", "Тюрьма", CellType.JAIL, position)
        self.is_just_visiting = True

    def on_land(self, player: Player, context: "TurnManager") -> Dict:
        if player.in_jail:
            return {"action": "in_jail"}
        return {"action": "just_visiting"}


class GoToJailCell(Cell):
    """Клетка Иди в тюрьму"""

    def __init__(self, position: int):
        super().__init__("go_to_jail", "Иди в тюрьму", CellType.GO_TO_JAIL, position)

    def on_land(self, player: Player, context: "TurnManager") -> Dict:
        return {"action": "go_to_jail"}


class Board:
    """
    Хранит поле и вычисляет перемещения по циклу
    """

    def __init__(self):
        self.cells: List[Cell] = []
        self.size = 0
        self.start_index = 0
        self.group_map: Dict[str, List[PropertyCell]] = {}

    def add_cell(self, cell: Cell):
        """Добавляет клетку на доску"""
        self.cells.append(cell)
        self.size = len(self.cells)
        if isinstance(cell, PropertyCell):
            if cell.color_group not in self.group_map:
                self.group_map[cell.color_group] = []
            self.group_map[cell.color_group].append(cell)

    def get_cell(self, index: int) -> Cell:
        """Получить клетку по индексу"""
        return self.cells[index % self.size]

    def next_position(self, current: int, steps: int) -> int:
        """Вычисляет новую позицию с учетом цикличности"""
        return (current + steps) % self.size

    def get_group_cells(self, color: str) -> List[PropertyCell]:
        """Вернуть клетки группы"""
        return self.group_map.get(color, [])


class Dice:
    """
    Генератор значений кубиков
    """

    def __init__(self):
        self.last_roll = (0, 0)
        self.rng = random.Random()

    def roll(self) -> Dict:
        """Бросает два кубика"""
        die1 = self.rng.randint(1, 6)
        die2 = self.rng.randint(1, 6)
        self.last_roll = (die1, die2)
        return {
            "die1": die1,
            "die2": die2,
            "sum": die1 + die2,
            "is_double": die1 == die2,
        }
