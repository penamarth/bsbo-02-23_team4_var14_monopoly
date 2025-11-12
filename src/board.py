"""
Класс Board - управление игровым полем
"""

from typing import TYPE_CHECKING

from property import Property

if TYPE_CHECKING:
    from player import Player


class Cell:
    def __init__(self, name: str, position: int):
        self.name = name
        self.position = position

    def on_landing(self, player: "Player"):
        pass


class Board:
    def __init__(self, size: int = 40):
        self.size = size
        self.cells: list[Cell] = []
        self._initialize_cells()

    def _initialize_cells(self):
        from property import PropertyGroup

        # Создание цветовых групп
        brown_group = PropertyGroup("Коричневая", "brown")
        light_blue_group = PropertyGroup("Голубая", "lightblue")
        # pink_group = PropertyGroup("Розовая", "pink")
        # orange_group = PropertyGroup("Оранжевая", "orange")

        # Создание упрощенного поля (не все 40 клеток, только основные для демонстрации)
        cells_data = [
            (0, "Старт", None),
            (
                1,
                "Средиземноморский проспект",
                Property("Средиземноморский проспект", 1, 60, 2, brown_group),
            ),
            (2, "Шанс", None),
            (
                3,
                "Балтийский проспект",
                Property("Балтийский проспект", 3, 60, 4, brown_group),
            ),
            (4, "Подоходный налог", None),
            (5, "Вокзал Ридинг", Property("Вокзал Ридинг", 5, 200, 25)),
            (
                6,
                "Восточный проспект",
                Property("Восточный проспект", 6, 100, 6, light_blue_group),
            ),
            (7, "Общественная казна", None),
            (
                8,
                "Западный проспект",
                Property("Западный проспект", 8, 100, 6, light_blue_group),
            ),
            (
                9,
                "Южный проспект",
                Property("Южный проспект", 9, 120, 8, light_blue_group),
            ),
            (10, "Тюрьма", None),
        ]

        self.cells = []
        for position, name, property_or_none in cells_data:
            if property_or_none:
                self.cells.append(property_or_none)
            else:
                self.cells.append(Cell(name, position))

        # Добавляем пустые клетки до размера поля
        while len(self.cells) < self.size:
            pos = len(self.cells)
            self.cells.append(Cell(f"Клетка {pos}", pos))

    def get_cell(self, position: int) -> Cell:
        # Учет зацикленности поля
        position = position % self.size
        return self.cells[position]

    def process_cell_action(self, player: "Player", cell: Cell):
        from game import Game

        # Если клетка - недвижимость
        if isinstance(cell, Property):
            if cell.owner is None:
                # Предложить купить
                print(f"\n'{cell.name}' доступна для покупки за {cell.price}₽")

                # Получаем текущую игру для доступа к наблюдателям
                game = Game.get_instance()

                # Для человека - спросить
                # Для ИИ - использовать стратегию
                if hasattr(player, "strategy"):
                    # Это ИИ игрок
                    if player.decide_purchase(cell):
                        player.buy_property(cell, game)
                    else:
                        print(f"   {player.name} отказался от покупки")
                else:
                    # Для упрощения демонстрации - автоматическая покупка если есть деньги
                    if player.balance >= cell.price:
                        player.buy_property(cell, game)
                    else:
                        print(f"   У {player.name} недостаточно средств")

            elif cell.owner != player:
                # Оплатить аренду
                player.pay_rent(cell, Game.get_instance())
