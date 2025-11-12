"""
Класс Bank - управление денежными операциями
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from player import Player


class Bank:
    def __init__(self, available_money: int = 1000000):
        self.available_money = available_money
        self.transactions: list[dict] = []

    def transfer(
        self,
        from_player: Optional["Player"],
        to_player: Optional["Player"],
        amount: int,
    ) -> bool:
        # Проверка баланса отправителя
        if from_player and from_player.balance < amount:
            return False

        # Выполнение перевода
        if from_player:
            from_player._set_balance(from_player.balance - amount)
        else:
            # Банк отправляет деньги
            if self.available_money < amount:
                return False
            self.available_money -= amount

        if to_player:
            to_player._set_balance(to_player.balance + amount)
        else:
            # Банк получает деньги
            self.available_money += amount

        # Логирование транзакции
        self.transactions.append(
            {
                "from": from_player.name if from_player else "Bank",
                "to": to_player.name if to_player else "Bank",
                "amount": amount,
            }
        )

        return True

    def handle_bankruptcy(self, player: "Player"):
        print(f"\n{player.name} объявлен банкротом!")

        # Освободить всю недвижимость
        for property in player.properties[:]:  # Копия списка для безопасной итерации
            property.owner = None
            property.houses = 0
            property.mortgaged = False
            player.properties.remove(property)
            print(f"   Освобождена недвижимость: {property.name}")

        # Обнулить баланс
        player._set_balance(0)
        player.is_bankrupt = True
