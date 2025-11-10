"""
Класс AIPlayer - ИИ игрок с использованием паттерна Strategy
"""

from game_strategy import BalancedStrategy, GameStrategy
from player import Player
from property import Property


class AIPlayer(Player):
    def __init__(self, name: str, balance: int = 1500, strategy: GameStrategy = None):
        super().__init__(name, balance)
        self.strategy = strategy or BalancedStrategy()
        self.risk_tolerance: float = 0.5  # Уровень толерантности к риску

    def decide_purchase(self, property: Property) -> bool:
        decision = self.strategy.decide_purchase(self, property)

        if decision:
            print(f"   {self.name} (ИИ) решил купить '{property.name}'")
        else:
            print(f"   {self.name} (ИИ) решил не покупать '{property.name}'")

        return decision

    def evaluate_trade_offer(
        self,
        offered_properties: list,
        requested_properties: list,
        offered_money: int,
        requested_money: int,
    ) -> bool:
        return self.strategy.evaluate_trade_offer(
            self,
            offered_properties,
            requested_properties,
            offered_money,
            requested_money,
        )
