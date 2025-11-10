"""
Паттерн Observer - для уведомления о событиях в игре
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from property import Property


class GameObserver(ABC):
    """Абстрактный наблюдатель за событиями игры"""

    @abstractmethod
    def on_dice_rolled(
        self, player: "Player", dice_values: tuple, sum_value: int, is_double: bool
    ):
        """Уведомление о броске костей"""
        pass

    @abstractmethod
    def on_player_moved(self, player: "Player", old_position: int, new_position: int):
        """Уведомление о перемещении игрока"""
        pass

    @abstractmethod
    def on_property_bought(self, player: "Player", property: "Property", price: int):
        """Уведомление о покупке недвижимости"""
        pass

    @abstractmethod
    def on_rent_paid(
        self, tenant: "Player", owner: "Player", property: "Property", amount: int
    ):
        """Уведомление об оплате аренды"""
        pass

    @abstractmethod
    def on_balance_changed(self, player: "Player", old_balance: int, new_balance: int):
        """Уведомление об изменении баланса"""
        pass

    @abstractmethod
    def on_turn_changed(self, player: "Player"):
        """Уведомление о смене хода"""
        pass


class ConsoleGameObserver(GameObserver):
    def on_dice_rolled(
        self, player: "Player", dice_values: tuple, sum_value: int, is_double: bool
    ):
        double_msg = " (ДУБЛЬ!)" if is_double else ""
        print(
            f"{player.name} бросил кости: {dice_values[0]} и {dice_values[1]} = {sum_value}{double_msg}"
        )

    def on_player_moved(self, player: "Player", old_position: int, new_position: int):
        print(
            f"{player.name} переместился с позиции {old_position} на позицию {new_position}"
        )

    def on_property_bought(self, player: "Player", property: "Property", price: int):
        print(f"{player.name} купил '{property.name}' за {price}₽")

    def on_rent_paid(
        self, tenant: "Player", owner: "Player", property: "Property", amount: int
    ):
        print(
            f"{tenant.name} заплатил {owner.name} {amount}₽ аренды за '{property.name}'"
        )

    def on_balance_changed(self, player: "Player", old_balance: int, new_balance: int):
        change = new_balance - old_balance
        sign = "+" if change >= 0 else ""
        print(
            f"Баланс {player.name}: {old_balance}₽ → {new_balance}₽ ({sign}{change}₽)"
        )

    def on_turn_changed(self, player: "Player"):
        print(f"\n{'=' * 60}")
        print(f"Ход игрока: {player.name}")
        print(f"{'=' * 60}")


class GameSubject:
    """Субъект, за которым наблюдают Observer'ы"""

    def __init__(self):
        self._observers: list[GameObserver] = []

    def attach(self, observer: GameObserver):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: GameObserver):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_dice_rolled(
        self, player: "Player", dice_values: tuple, sum_value: int, is_double: bool
    ):
        for observer in self._observers:
            observer.on_dice_rolled(player, dice_values, sum_value, is_double)

    def notify_player_moved(
        self, player: "Player", old_position: int, new_position: int
    ):
        for observer in self._observers:
            observer.on_player_moved(player, old_position, new_position)

    def notify_property_bought(
        self, player: "Player", property: "Property", price: int
    ):
        for observer in self._observers:
            observer.on_property_bought(player, property, price)

    def notify_rent_paid(
        self, tenant: "Player", owner: "Player", property: "Property", amount: int
    ):
        for observer in self._observers:
            observer.on_rent_paid(tenant, owner, property, amount)

    def notify_balance_changed(
        self, player: "Player", old_balance: int, new_balance: int
    ):
        for observer in self._observers:
            observer.on_balance_changed(player, old_balance, new_balance)

    def notify_turn_changed(self, player: "Player"):
        for observer in self._observers:
            observer.on_turn_changed(player)
