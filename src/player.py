"""
Класс Player - представление игрока
"""

from typing import TYPE_CHECKING

from property import Property

if TYPE_CHECKING:
    from board import Board, Cell
    from game import Game


class Player:
    def __init__(self, name: str, balance: int = 1500):
        self.name = name
        self.balance = balance
        self.position: int = 0
        self.properties: list[Property] = []
        self.in_jail: bool = False
        self.jail_turns: int = 0
        self.is_bankrupt: bool = False

    def move(self, steps: int, board: "Board") -> "Cell":
        old_position = self.position
        self.position = (self.position + steps) % board.size

        # Проверка прохождения через старт (позиция 0)
        if self.position < old_position or (old_position + steps >= board.size):
            # Игрок прошел через старт - получает зарплату
            from game import Game

            game = Game.get_instance()
            salary = 200
            game.bank.transfer(None, self, salary)
            print(f"   {self.name} прошел через СТАРТ и получил {salary}₽")

        return board.get_cell(self.position)

    def pay_rent(self, property: Property, game: "Game") -> bool:
        if not property.owner or property.owner == self:
            return True

        rent_amount = property.calculate_rent(self)

        if rent_amount == 0:
            return True

        print(
            f"\n{self.name} должен заплатить {rent_amount}₽ аренды за '{property.name}'"
        )

        success = game.bank.transfer(self, property.owner, rent_amount)

        if success:
            game.notify_rent_paid(self, property.owner, property, rent_amount)
        else:
            # Недостаточно средств - банкротство
            print(f"   У {self.name} недостаточно средств для оплаты!")
            game.bank.handle_bankruptcy(self)

        return success

    def buy_property(self, property: Property, game: "Game") -> bool:
        if property.owner is not None:
            return False

        success = game.bank.transfer(self, None, property.price)

        if success:
            property.owner = self
            self.properties.append(property)
            game.notify_property_bought(self, property, property.price)

            # Проверка монополии
            if property.group and self._check_monopoly(property.group):
                print(
                    f"   {self.name} получил МОНОПОЛИЮ на группу '{property.group.name}'!"
                )

        return success

    def _check_monopoly(self, group) -> bool:
        for prop in group.properties:
            if prop.owner != self:
                return False
        return True

    def _set_balance(self, new_balance: int):
        old_balance = self.balance
        self.balance = new_balance

        # Уведомление об изменении баланса через игру
        from game import Game

        game = Game.get_instance()
        if game:
            game.notify_balance_changed(self, old_balance, new_balance)
