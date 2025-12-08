"""
Паттерн Strategy: Стратегии поведения AI
Обоснование использования: AI должен гибко переключать стратегию в зависимости от игровой ситуации
"""

from abc import ABC, abstractmethod
from typing import List

from models import Board, Player, PropertyCell


class AIStrategy(ABC):
    """Интерфейс стратегии ИИ"""

    @abstractmethod
    def should_purchase_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Решает, покупать ли недвижимость"""
        pass

    @abstractmethod
    def should_build_on_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Решает, строить ли на недвижимости"""
        pass

    @abstractmethod
    def should_accept_trade(
        self,
        player: Player,
        offered_properties: List[PropertyCell],
        requested_properties: List[PropertyCell],
        money_diff: int,
    ) -> bool:
        """Решает, принять ли торговое предложение"""
        pass

    @abstractmethod
    def should_mortgage_property(
        self, player: Player, property_cell: PropertyCell
    ) -> bool:
        """Решает, закладывать ли собственность"""
        pass

    def get_strategy_name(self) -> str:
        """Возвращает имя стратегии"""
        return self.__class__.__name__


class ConservativeAIStrategy(AIStrategy):
    """
    Консервативная стратегия: минимизирует риски
    - Покупает только дешёвую недвижимость
    - Сохраняет высокий резерв денег
    - Строит редко
    - Избегает рискованных сделок
    """

    def __init__(self):
        self.min_reserve = 500  # Минимальный резерв денег
        self.max_purchase_price = 200  # Максимальная цена покупки

    def should_purchase_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Покупает только дешёвые свойства при достаточном резерве"""
        if property_cell.price > self.max_purchase_price:
            print(
                f"  [Conservative AI] Отказ: цена {property_cell.price} > {self.max_purchase_price}"
            )
            return False

        remaining_balance = player.balance - property_cell.price
        if remaining_balance < self.min_reserve:
            print(
                f"  [Conservative AI] Отказ: резерв {remaining_balance} < {self.min_reserve}"
            )
            return False

        print(
            "  [Conservative AI] Одобрение покупки: дешёвая недвижимость, хороший резерв"
        )
        return True

    def should_build_on_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Строит только при большом запасе денег"""
        if not property_cell.can_build(board):
            return False

        remaining_balance = player.balance - property_cell.build_cost
        if remaining_balance < self.min_reserve * 2:  # Удвоенный резерв
            print("  [Conservative AI] Отказ строить: недостаточный резерв")
            return False

        print("  [Conservative AI] Одобрение строительства: большой резерв")
        return True

    def should_accept_trade(
        self,
        player: Player,
        offered_properties: List[PropertyCell],
        requested_properties: List[PropertyCell],
        money_diff: int,
    ) -> bool:
        """Принимает только очень выгодные сделки"""
        # Консервативная оценка: общая стоимость предложенных должна быть значительно выше запрашиваемых
        offered_value = sum(prop.price for prop in offered_properties) - money_diff
        requested_value = sum(prop.price for prop in requested_properties)

        if offered_value >= requested_value * 1.5:  # Требуем 50% премию
            print("  [Conservative AI] Одобрение сделки: очень выгодна")
            return True

        print("  [Conservative AI] Отказ от сделки: недостаточно выгодна")
        return False

    def should_mortgage_property(
        self, player: Player, property_cell: PropertyCell
    ) -> bool:
        """Закладывает только в критической ситуации"""
        if player.balance < 100:  # Критический баланс
            print(
                f"  [Conservative AI] Закладывает {property_cell.name}: критический баланс"
            )
            return True

        print("  [Conservative AI] Отказ закладывать: баланс приемлемый")
        return False


class AggressiveAIStrategy(AIStrategy):
    """
    Агрессивная стратегия: максимизирует контроль
    - Покупает всю доступную недвижимость
    - Активно строит на монополиях
    - Рискует оставаться с малым резервом
    - Агрессивно торгуется для монополий
    """

    def __init__(self):
        self.min_reserve = 50  # Минимальный резерв

    def should_purchase_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Покупает все доступные свойства"""
        remaining_balance = player.balance - property_cell.price
        if remaining_balance < self.min_reserve:
            print(
                f"  [Aggressive AI] Отказ: слишком низкий остаток {remaining_balance}"
            )
            return False

        print("  [Aggressive AI] Одобрение покупки: максимизация владений")
        return True

    def should_build_on_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Строит агрессивно на любой монополии"""
        if not property_cell.can_build(board):
            return False

        remaining_balance = player.balance - property_cell.build_cost
        if remaining_balance < self.min_reserve:
            print("  [Aggressive AI] Отказ строить: критический баланс")
            return False

        # Проверяем, есть ли монополия
        if board.has_monopoly(player, property_cell.group):
            print(
                f"  [Aggressive AI] Одобрение строительства: монополия группы {property_cell.group}"
            )
            return True

        return False

    def should_accept_trade(
        self,
        player: Player,
        offered_properties: List[PropertyCell],
        requested_properties: List[PropertyCell],
        money_diff: int,
    ) -> bool:
        """Принимает сделки, дающие монополию"""
        # Упрощённая логика: принимаем, если получаем больше свойств
        if len(offered_properties) > len(requested_properties):
            print("  [Aggressive AI] Одобрение сделки: получаем больше свойств")
            return True

        # Или если это приемлемый обмен по цене
        offered_value = sum(prop.price for prop in offered_properties) - money_diff
        requested_value = sum(prop.price for prop in requested_properties)

        if offered_value >= requested_value * 0.8:  # Допускаем 20% потерю для монополии
            print("  [Aggressive AI] Одобрение сделки: приемлемый обмен")
            return True

        print("  [Aggressive AI] Отказ от сделки: невыгодна")
        return False

    def should_mortgage_property(
        self, player: Player, property_cell: PropertyCell
    ) -> bool:
        """Закладывает для получения средств на строительство"""
        if player.balance < 200:
            print(f"  [Aggressive AI] Закладывает {property_cell.name}: нужны средства")
            return True

        return False


class BalancedAIStrategy(AIStrategy):
    """
    Сбалансированная стратегия: баланс между риском и выгодой
    - Средний резерв денег
    - Покупает среднюю недвижимость
    - Строит при монополиях
    - Принимает справедливые сделки
    """

    def __init__(self):
        self.min_reserve = 300
        self.max_purchase_price = 350

    def should_purchase_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Покупает недвижимость среднего ценового диапазона"""
        if property_cell.price > self.max_purchase_price:
            print("  [Balanced AI] Отказ: цена слишком высокая")
            return False

        remaining_balance = player.balance - property_cell.price
        if remaining_balance < self.min_reserve:
            print("  [Balanced AI] Отказ: недостаточный резерв")
            return False

        # Предпочитаем покупку, если это даст монополию
        player_group_properties = [
            p
            for p in player.properties
            if isinstance(p, PropertyCell) and p.group == property_cell.group
        ]

        group_size = board.get_group_size(property_cell.group)
        if len(player_group_properties) == group_size - 1:
            print("  [Balanced AI] Одобрение покупки: дополнит монополию!")
            return True

        print("  [Balanced AI] Одобрение покупки: соответствует критериям")
        return True

    def should_build_on_property(
        self, player: Player, property_cell: PropertyCell, board: Board
    ) -> bool:
        """Строит на монополиях при достаточном резерве"""
        if not property_cell.can_build(board):
            return False

        remaining_balance = player.balance - property_cell.build_cost
        if remaining_balance < self.min_reserve:
            print("  [Balanced AI] Отказ строить: недостаточный резерв")
            return False

        if board.has_monopoly(player, property_cell.group):
            print("  [Balanced AI] Одобрение строительства: монополия + хороший резерв")
            return True

        return False

    def should_accept_trade(
        self,
        player: Player,
        offered_properties: List[PropertyCell],
        requested_properties: List[PropertyCell],
        money_diff: int,
    ) -> bool:
        """Принимает справедливые сделки"""
        offered_value = sum(prop.price for prop in offered_properties) - money_diff
        requested_value = sum(prop.price for prop in requested_properties)

        # Справедливый обмен: +/- 10%
        if 0.9 * requested_value <= offered_value <= 1.1 * requested_value:
            print("  [Balanced AI] Одобрение сделки: справедливый обмен")
            return True

        print("  [Balanced AI] Отказ от сделки: несправедливая")
        return False

    def should_mortgage_property(
        self, player: Player, property_cell: PropertyCell
    ) -> bool:
        """Закладывает при балансе ниже минимального резерва"""
        if player.balance < self.min_reserve:
            print(
                f"  [Balanced AI] Закладывает {property_cell.name}: резерв ниже нормы"
            )
            return True

        return False


class AIPlayer:
    """
    ИИ-игрок с возможностью смены стратегии
    Демонстрирует паттерн Strategy
    """

    def __init__(self, player: Player, strategy: AIStrategy):
        self.player = player
        self.strategy = strategy

    def set_strategy(self, strategy: AIStrategy):
        """Смена стратегии во время игры"""
        old_strategy = self.strategy.get_strategy_name()
        self.strategy = strategy
        new_strategy = self.strategy.get_strategy_name()
        print(
            f"🔄 {self.player.name} меняет стратегию: {old_strategy} → {new_strategy}"
        )

    def decide_purchase(self, property_cell: PropertyCell, board: Board) -> bool:
        """Принимает решение о покупке"""
        return self.strategy.should_purchase_property(self.player, property_cell, board)

    def decide_build(self, property_cell: PropertyCell, board: Board) -> bool:
        """Принимает решение о строительстве"""
        return self.strategy.should_build_on_property(self.player, property_cell, board)

    def decide_trade(
        self,
        offered_properties: List[PropertyCell],
        requested_properties: List[PropertyCell],
        money_diff: int,
    ) -> bool:
        """Принимает решение о торговле"""
        return self.strategy.should_accept_trade(
            self.player, offered_properties, requested_properties, money_diff
        )

    def decide_mortgage(self, property_cell: PropertyCell) -> bool:
        """Принимает решение о залоге"""
        return self.strategy.should_mortgage_property(self.player, property_cell)
