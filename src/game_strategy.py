"""
Паттерн Strategy - для стратегий принятия решений ИИ игроком
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player
    from property import Property


class GameStrategy(ABC):
    """Абстрактная стратегия принятия решений"""

    @abstractmethod
    def decide_purchase(self, player: "Player", property: "Property") -> bool:
        """Решить, покупать ли недвижимость"""
        pass

    @abstractmethod
    def evaluate_trade_offer(
        self,
        player: "Player",
        offered_properties: list,
        requested_properties: list,
        offered_money: int,
        requested_money: int,
    ) -> bool:
        """Оценить предложение о торговле"""
        pass


class AggressiveStrategy(GameStrategy):
    """Агрессивная стратегия - покупать все, что возможно"""

    def decide_purchase(self, player: "Player", property: "Property") -> bool:
        """Покупать, если есть деньги"""
        return player.balance >= property.price

    def evaluate_trade_offer(
        self,
        player: "Player",
        offered_properties: list,
        requested_properties: list,
        offered_money: int,
        requested_money: int,
    ) -> bool:
        """Принимать сделки, которые дают больше недвижимости"""
        return len(offered_properties) > len(requested_properties)


class ConservativeStrategy(GameStrategy):
    """Консервативная стратегия - покупать только дешевую недвижимость"""

    def decide_purchase(self, player: "Player", property: "Property") -> bool:
        """Покупать только если цена не более 30% баланса"""
        return (
            player.balance >= property.price and property.price <= player.balance * 0.3
        )

    def evaluate_trade_offer(
        self,
        player: "Player",
        offered_properties: list,
        requested_properties: list,
        offered_money: int,
        requested_money: int,
    ) -> bool:
        """Принимать только выгодные денежные сделки"""
        return offered_money > requested_money


class BalancedStrategy(GameStrategy):
    """Сбалансированная стратегия - умеренные решения"""

    def decide_purchase(self, player: "Player", property: "Property") -> bool:
        """Покупать, если останется достаточно денег для безопасности"""
        safety_reserve = 500  # Минимальный резерв денег
        return player.balance >= property.price + safety_reserve

    def evaluate_trade_offer(
        self,
        player: "Player",
        offered_properties: list,
        requested_properties: list,
        offered_money: int,
        requested_money: int,
    ) -> bool:
        """Оценивать сделку комплексно"""
        property_value = len(offered_properties) - len(requested_properties)
        money_value = offered_money - requested_money
        # Принимать, если общая выгода положительна
        return (property_value * 100 + money_value) > 0
