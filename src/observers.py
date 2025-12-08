"""
Паттерн Observer: Наблюдатели за игровыми событиями
Обоснование использования: Слабое связывание между игровой логикой и системами логирования/статистики
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from models import Cell, Player, PropertyCell


class GameObserver(ABC):
    """Интерфейс наблюдателя игровых событий"""

    @abstractmethod
    def on_player_moved(
        self, player: Player, from_position: int, to_position: int, cell: Cell
    ):
        """Событие перемещения игрока"""
        pass

    @abstractmethod
    def on_property_purchased(
        self, player: Player, property_cell: PropertyCell, price: int
    ):
        """Событие покупки недвижимости"""
        pass

    @abstractmethod
    def on_rent_paid(
        self, payer: Player, receiver: Player, property_cell: PropertyCell, amount: int
    ):
        """Событие оплаты аренды"""
        pass

    @abstractmethod
    def on_player_jailed(self, player: Player):
        """Событие помещения в тюрьму"""
        pass

    @abstractmethod
    def on_building_built(
        self, player: Player, property_cell: PropertyCell, level: int
    ):
        """Событие постройки здания"""
        pass

    @abstractmethod
    def on_property_mortgaged(
        self, player: Player, property_cell: PropertyCell, amount: int
    ):
        """Событие оформления залога"""
        pass

    @abstractmethod
    def on_trade_completed(self, player1: Player, player2: Player, details: str):
        """Событие завершения торговли"""
        pass

    @abstractmethod
    def on_balance_changed(
        self, player: Player, old_balance: int, new_balance: int, reason: str
    ):
        """Событие изменения баланса"""
        pass


class ConsoleLoggerObserver(GameObserver):
    """
    Наблюдатель для вывода событий в консоль
    Обеспечивает видимость всех игровых действий
    """

    def __init__(self):
        self.event_count = 0

    def on_player_moved(
        self, player: Player, from_position: int, to_position: int, cell: Cell
    ):
        """Логирует перемещение"""
        self.event_count += 1
        print(
            f"📍 Событие #{self.event_count}: {player.name} переместился {from_position} → {to_position} ({cell.name})"
        )

    def on_property_purchased(
        self, player: Player, property_cell: PropertyCell, price: int
    ):
        """Логирует покупку"""
        self.event_count += 1
        print(
            f"🏠 Событие #{self.event_count}: {player.name} купил {property_cell.name} за ${price}"
        )

    def on_rent_paid(
        self, payer: Player, receiver: Player, property_cell: PropertyCell, amount: int
    ):
        """Логирует аренду"""
        self.event_count += 1
        print(
            f"💰 Событие #{self.event_count}: {payer.name} заплатил ${amount} аренды {receiver.name} за {property_cell.name}"
        )

    def on_player_jailed(self, player: Player):
        """Логирует тюрьму"""
        self.event_count += 1
        print(f"🚔 Событие #{self.event_count}: {player.name} отправлен в тюрьму")

    def on_building_built(
        self, player: Player, property_cell: PropertyCell, level: int
    ):
        """Логирует строительство"""
        self.event_count += 1
        building_type = "дом" if level < 5 else "отель"
        print(
            f"🏗️ Событие #{self.event_count}: {player.name} построил {building_type} на {property_cell.name} (уровень {level})"
        )

    def on_property_mortgaged(
        self, player: Player, property_cell: PropertyCell, amount: int
    ):
        """Логирует залог"""
        self.event_count += 1
        print(
            f"🏦 Событие #{self.event_count}: {player.name} заложил {property_cell.name} за ${amount}"
        )

    def on_trade_completed(self, player1: Player, player2: Player, details: str):
        """Логирует торговлю"""
        self.event_count += 1
        print(
            f"🤝 Событие #{self.event_count}: Торговля между {player1.name} и {player2.name}: {details}"
        )

    def on_balance_changed(
        self, player: Player, old_balance: int, new_balance: int, reason: str
    ):
        """Логирует изменение баланса"""
        self.event_count += 1
        diff = new_balance - old_balance
        symbol = "+" if diff > 0 else ""
        print(
            f"💵 Событие #{self.event_count}: Баланс {player.name}: ${old_balance} → ${new_balance} ({symbol}${diff}) [{reason}]"
        )


class StatisticsObserver(GameObserver):
    """
    Наблюдатель для сбора игровой статистики
    Отслеживает метрики для анализа игры
    """

    def __init__(self):
        self.stats = {
            "total_moves": 0,
            "total_purchases": 0,
            "total_rent_paid": 0,
            "total_jail_visits": 0,
            "total_buildings": 0,
            "total_mortgages": 0,
            "total_trades": 0,
            "player_stats": {},
        }

    def _ensure_player_stats(self, player: Player):
        """Инициализирует статистику игрока"""
        if player.id not in self.stats["player_stats"]:
            self.stats["player_stats"][player.id] = {
                "name": player.name,
                "moves": 0,
                "purchases": 0,
                "rent_paid": 0,
                "rent_received": 0,
                "jail_visits": 0,
                "buildings_built": 0,
                "mortgages": 0,
                "trades": 0,
                "balance_changes": [],
            }

    def on_player_moved(
        self, player: Player, from_position: int, to_position: int, cell: Cell
    ):
        """Учитывает перемещение"""
        self._ensure_player_stats(player)
        self.stats["total_moves"] += 1
        self.stats["player_stats"][player.id]["moves"] += 1

    def on_property_purchased(
        self, player: Player, property_cell: PropertyCell, price: int
    ):
        """Учитывает покупку"""
        self._ensure_player_stats(player)
        self.stats["total_purchases"] += 1
        self.stats["player_stats"][player.id]["purchases"] += 1

    def on_rent_paid(
        self, payer: Player, receiver: Player, property_cell: PropertyCell, amount: int
    ):
        """Учитывает аренду"""
        self._ensure_player_stats(payer)
        self._ensure_player_stats(receiver)
        self.stats["total_rent_paid"] += amount
        self.stats["player_stats"][payer.id]["rent_paid"] += amount
        self.stats["player_stats"][receiver.id]["rent_received"] += amount

    def on_player_jailed(self, player: Player):
        """Учитывает тюрьму"""
        self._ensure_player_stats(player)
        self.stats["total_jail_visits"] += 1
        self.stats["player_stats"][player.id]["jail_visits"] += 1

    def on_building_built(
        self, player: Player, property_cell: PropertyCell, level: int
    ):
        """Учитывает строительство"""
        self._ensure_player_stats(player)
        self.stats["total_buildings"] += 1
        self.stats["player_stats"][player.id]["buildings_built"] += 1

    def on_property_mortgaged(
        self, player: Player, property_cell: PropertyCell, amount: int
    ):
        """Учитывает залог"""
        self._ensure_player_stats(player)
        self.stats["total_mortgages"] += 1
        self.stats["player_stats"][player.id]["mortgages"] += 1

    def on_trade_completed(self, player1: Player, player2: Player, details: str):
        """Учитывает торговлю"""
        self._ensure_player_stats(player1)
        self._ensure_player_stats(player2)
        self.stats["total_trades"] += 1
        self.stats["player_stats"][player1.id]["trades"] += 1
        self.stats["player_stats"][player2.id]["trades"] += 1

    def on_balance_changed(
        self, player: Player, old_balance: int, new_balance: int, reason: str
    ):
        """Учитывает изменение баланса"""
        self._ensure_player_stats(player)
        self.stats["player_stats"][player.id]["balance_changes"].append(
            {
                "old": old_balance,
                "new": new_balance,
                "diff": new_balance - old_balance,
                "reason": reason,
            }
        )

    def get_summary(self) -> Dict:
        """Возвращает сводку статистики"""
        return self.stats

    def print_summary(self):
        """Выводит статистику в консоль"""
        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА ИГРЫ")
        print("=" * 60)
        print(f"Всего ходов: {self.stats['total_moves']}")
        print(f"Всего покупок: {self.stats['total_purchases']}")
        print(f"Всего аренды оплачено: ${self.stats['total_rent_paid']}")
        print(f"Посещений тюрьмы: {self.stats['total_jail_visits']}")
        print(f"Построено зданий: {self.stats['total_buildings']}")
        print(f"Оформлено залогов: {self.stats['total_mortgages']}")
        print(f"Совершено сделок: {self.stats['total_trades']}")

        print("\n" + "-" * 60)
        print("СТАТИСТИКА ИГРОКОВ:")
        print("-" * 60)
        for player_id, pstats in self.stats["player_stats"].items():
            print(f"\n{pstats['name']}:")
            print(f"  Ходов: {pstats['moves']}")
            print(f"  Покупок: {pstats['purchases']}")
            print(f"  Аренда оплачена: ${pstats['rent_paid']}")
            print(f"  Аренда получена: ${pstats['rent_received']}")
            print(f"  Тюрьма: {pstats['jail_visits']} раз")
            print(f"  Построено: {pstats['buildings_built']}")
            print(f"  Залогов: {pstats['mortgages']}")
            print(f"  Сделок: {pstats['trades']}")
        print("=" * 60 + "\n")


class GameEventPublisher:
    """
    Издатель игровых событий
    Управляет подпиской наблюдателей и уведомлениями
    """

    def __init__(self):
        self.observers: List[GameObserver] = []

    def attach(self, observer: GameObserver):
        """Подписать наблюдателя"""
        if observer not in self.observers:
            self.observers.append(observer)
            print(f"✓ Подписан наблюдатель: {observer.__class__.__name__}")

    def detach(self, observer: GameObserver):
        """Отписать наблюдателя"""
        if observer in self.observers:
            self.observers.remove(observer)
            print(f"✓ Отписан наблюдатель: {observer.__class__.__name__}")

    def notify_player_moved(
        self, player: Player, from_position: int, to_position: int, cell: Cell
    ):
        """Уведомить о перемещении"""
        for observer in self.observers:
            observer.on_player_moved(player, from_position, to_position, cell)

    def notify_property_purchased(
        self, player: Player, property_cell: PropertyCell, price: int
    ):
        """Уведомить о покупке"""
        for observer in self.observers:
            observer.on_property_purchased(player, property_cell, price)

    def notify_rent_paid(
        self, payer: Player, receiver: Player, property_cell: PropertyCell, amount: int
    ):
        """Уведомить об аренде"""
        for observer in self.observers:
            observer.on_rent_paid(payer, receiver, property_cell, amount)

    def notify_player_jailed(self, player: Player):
        """Уведомить о тюрьме"""
        for observer in self.observers:
            observer.on_player_jailed(player)

    def notify_building_built(
        self, player: Player, property_cell: PropertyCell, level: int
    ):
        """Уведомить о строительстве"""
        for observer in self.observers:
            observer.on_building_built(player, property_cell, level)

    def notify_property_mortgaged(
        self, player: Player, property_cell: PropertyCell, amount: int
    ):
        """Уведомить о залоге"""
        for observer in self.observers:
            observer.on_property_mortgaged(player, property_cell, amount)

    def notify_trade_completed(self, player1: Player, player2: Player, details: str):
        """Уведомить о торговле"""
        for observer in self.observers:
            observer.on_trade_completed(player1, player2, details)

    def notify_balance_changed(
        self, player: Player, old_balance: int, new_balance: int, reason: str
    ):
        """Уведомить об изменении баланса"""
        for observer in self.observers:
            observer.on_balance_changed(player, old_balance, new_balance, reason)
