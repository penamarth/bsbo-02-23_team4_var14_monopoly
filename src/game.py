"""
Игровая логика: GameSession, TurnManager
Корневая сущность агрегата: GameSession
"""

from typing import Dict, List, Optional

from ai_strategy import (
    AggressiveAIStrategy,
    AIPlayer,
    BalancedAIStrategy,
    ConservativeAIStrategy,
)
from finance import Auction, Bank, TradeManager
from models import Board, Cell, Dice, Player, PropertyCell
from observers import ConsoleLoggerObserver, GameEventPublisher, StatisticsObserver


class TurnManager:
    """
    Управляет шагами внутри хода
    Оркестрирует ход игрока согласно диаграммам последовательности
    """

    def __init__(
        self,
        board: Board,
        bank: Bank,
        dice: Dice,
        trade_manager: TradeManager,
        game_session: "GameSession",
    ):
        self.current_player_index = 0
        self.dice = dice
        self.board = board
        self.bank = bank
        self.trade_manager = trade_manager
        self.double_roll_count = 0
        self.game_session = game_session
        self.auction = Auction()

    def start_turn(self, player: Player):
        """Инициирует ход игрока"""
        self.double_roll_count = 0
        print(f"\n{'=' * 50}")
        print(f"Ход игрока: {player.name}")
        print(f"Баланс: ${player.balance}, Позиция: {player.position}")

        if player.in_jail:
            print(f"{player.name} в тюрьме. Осталось ходов: {player.jail_turns_left}")
            player.jail_turns_left -= 1
            if player.jail_turns_left <= 0:
                player.in_jail = False
                print(f"{player.name} освобождён из тюрьмы!")
            return

    def roll_dice(self) -> Dict:
        """Бросает кубики"""
        result = self.dice.roll()
        print(f"Бросок кубиков: {result['die1']} + {result['die2']} = {result['sum']}")
        if result["is_double"]:
            print("Дубль!")
            self.double_roll_count += 1
        return result

    def move_player(self, player: Player, steps: int) -> Cell:
        """Перемещает фишку игрока"""
        old_position = player.position
        new_position = self.board.next_position(old_position, steps)

        # Проверка прохождения Старт
        if new_position < old_position:
            print(f"{player.name} прошёл через Старт! +$200")
            self.bank.credit(player, 200, "Прохождение Старта")

        player.move_to(new_position)
        cell = self.board.get_cell(new_position)
        print(
            f"{player.name} перемещается с {old_position} на {new_position}: {cell.name}"
        )
        return cell

    def apply_cell_effects(self, player: Player, cell: Cell) -> Dict:
        """Обрабатывает обязательные эффекты клетки"""
        result = cell.on_land(player, self)
        action = result.get("action")

        if action == "purchase_offer":
            property_cell = result["property"]
            print(
                f"\nВозможность купить {property_cell.name} за ${property_cell.price}"
            )
            # Для демо - автоматическая покупка при наличии средств
            if player.balance >= property_cell.price:
                if self.bank.purchase_property(player, property_cell):
                    print(f"✓ {player.name} купил {property_cell.name}")
                else:
                    print(f"✗ Не удалось купить {property_cell.name}")
            else:
                print("✗ Недостаточно средств для покупки")

        elif action == "pay_rent":
            property_cell = result["property"]
            owner = result["owner"]
            rent = property_cell.calculate_rent()
            print(f"\nНеобходимо заплатить аренду ${rent} владельцу {owner.name}")
            if self.bank.pay_rent(player, owner, property_cell):
                print(f"✓ Аренда ${rent} оплачена")
            else:
                print("✗ Недостаточно средств для оплаты аренды!")

        elif action == "own_property":
            print(f"{player.name} на своей собственности")

        elif action == "pay_tax":
            tax = result["amount"]
            print(f"\nНалог: ${tax}")
            if self.bank.debit(player, tax, "Налог"):
                print(f"✓ Налог ${tax} оплачен")
            else:
                print("✗ Недостаточно средств для оплаты налога!")

        elif action == "go_to_jail":
            self.send_to_jail(player)

        return result

    def offer_optional_actions(self, player: Player) -> List[str]:
        """Предлагает необязательные действия"""
        actions = []

        # Проверка возможности строительства
        for prop in player.properties:
            if isinstance(prop, PropertyCell) and prop.can_build(self.board):
                actions.append(f"build_{prop.id}")

        # Проверка возможности залога
        for prop in player.properties:
            if isinstance(prop, PropertyCell) and not prop.is_mortgaged:
                actions.append(f"mortgage_{prop.id}")

        # Торговля всегда доступна
        actions.append("trade")

        return actions

    def end_turn(self):
        """Завершает ход"""
        print(f"{'=' * 50}\n")

        # Проверка правила трёх дублей
        if self.double_roll_count >= 3:
            current_player = self.game_session.get_current_player()
            print(f"{current_player.name} выбросил 3 дубля подряд!")
            self.send_to_jail(current_player)

        self.game_session.end_turn()

    def grant_extra_turn(self, player: Player):
        """Даёт дополнительный ход при дубле"""
        print(f"{player.name} получает дополнительный ход!")

    def send_to_jail(self, player: Player):
        """Помещает игрока в тюрьму"""
        print(f"🚔 {player.name} отправлен в тюрьму!")
        player.in_jail = True
        player.jail_turns_left = 3
        # Перемещаем на клетку тюрьмы (обычно позиция 10)
        player.move_to(10)


class GameSession:
    """
    Управляет партией
    Корневая сущность агрегата "Игровая Логика"
    """

    def __init__(self):
        self.players: List[Player] = []
        self.board: Optional[Board] = None
        self.bank: Optional[Bank] = None
        self.turn_manager: Optional[TurnManager] = None
        self.trade_manager: Optional[TradeManager] = None
        self.event_publisher: Optional[GameEventPublisher] = None
        self.console_logger: Optional[ConsoleLoggerObserver] = None
        self.statistics: Optional[StatisticsObserver] = None
        self.ai_players: Dict[str, AIPlayer] = {}  # Словарь AI-игроков по ID
        self.settings = {}
        self.is_paused = False
        self.current_player_index = 0

    def start(self, game_config: Dict):
        """Запускает новую партию"""
        print("🎲 Инициализация игры Монополия...")

        # Создание игроков
        for player_config in game_config.get("players", []):
            player = Player(
                player_config["id"],
                player_config["name"],
                player_config.get("is_ai", False),
            )
            self.players.append(player)
            print(f"  Игрок добавлен: {player}")

        # Инициализация доски
        self.board = self._create_board()

        # Инициализация системы наблюдателей
        self.event_publisher = GameEventPublisher()
        self.console_logger = ConsoleLoggerObserver()
        self.statistics = StatisticsObserver()

        # Автоматическая подписка встроенных наблюдателей
        self.event_publisher.attach(self.console_logger)
        self.event_publisher.attach(self.statistics)

        # Инициализация финансового агрегата
        self.bank = Bank()
        self.bank.event_publisher = self.event_publisher  # Связываем Bank с издателем
        self.trade_manager = TradeManager(self.bank)

        # Инициализация менеджера ходов
        dice = Dice()
        self.turn_manager = TurnManager(
            self.board, self.bank, dice, self.trade_manager, self
        )

        # Создание AI-игроков со стратегиями
        self._initialize_ai_players()

        self.settings = game_config.get("settings", {})
        print("✓ Игра инициализирована!\n")

    def _initialize_ai_players(self):
        """Создаёт AI-игроков с начальными стратегиями"""
        for player in self.players:
            if player.is_ai:
                # Назначаем стратегии на основе имени или позиции
                if "Консервативный" in player.name or player.id == "p2":
                    strategy = ConservativeAIStrategy()
                elif "Агрессивный" in player.name or player.id == "p3":
                    strategy = AggressiveAIStrategy()
                else:
                    strategy = BalancedAIStrategy()

                ai_player = AIPlayer(player, strategy)
                self.ai_players[player.id] = ai_player
                print(
                    f"  AI создан: {player.name} со стратегией {strategy.get_strategy_name()}"
                )

    def _create_board(self) -> Board:
        """Создаёт упрощённое игровое поле"""
        board = Board()

        from models import GoToJailCell, JailCell, StartCell, TaxCell

        # Клетка 0: Старт
        board.add_cell(StartCell(0))

        # Клетки 1-3: Коричневая группа
        board.add_cell(
            PropertyCell("prop1", "Средиземноморский проспект", 1, 60, "brown", 2, 50)
        )
        board.add_cell(
            PropertyCell("prop2", "Балтийский проспект", 3, 60, "brown", 4, 50)
        )

        # Клетка 4: Налог
        board.add_cell(TaxCell("tax1", "Подоходный налог", 4, 200))

        # Клетки 5-7: Голубая группа
        board.add_cell(
            PropertyCell("prop3", "Восточный проспект", 6, 100, "lightblue", 6, 50)
        )
        board.add_cell(
            PropertyCell("prop4", "Вермонт проспект", 8, 100, "lightblue", 6, 50)
        )
        board.add_cell(
            PropertyCell("prop5", "Коннектикут проспект", 9, 120, "lightblue", 8, 50)
        )

        # Клетка 10: Тюрьма
        board.add_cell(JailCell(10))

        # Клетки 11-13: Розовая группа
        board.add_cell(
            PropertyCell("prop6", "Сент-Чарльз плейс", 11, 140, "pink", 10, 100)
        )
        board.add_cell(PropertyCell("prop7", "Штаты-Авеню", 13, 140, "pink", 10, 100))
        board.add_cell(
            PropertyCell("prop8", "Вирджиния Авеню", 14, 160, "pink", 12, 100)
        )

        # Клетка 15: Налог
        board.add_cell(TaxCell("tax2", "Роскошный налог", 15, 100))

        # Клетки 16-19: Оранжевая группа
        board.add_cell(
            PropertyCell("prop9", "Нью-Йорк Авеню", 19, 200, "orange", 16, 100)
        )

        # Клетка 20: Иди в тюрьму
        board.add_cell(GoToJailCell(30))

        return board

    def pause(self):
        """Ставит игру на паузу"""
        self.is_paused = True
        print("⏸ Игра поставлена на паузу")

    def resume(self):
        """Снимает с паузы"""
        self.is_paused = False
        print("▶ Игра возобновлена")

    def save_state(self) -> str:
        """Сохраняет снимок партии"""
        # Упрощённая реализация
        snapshot_id = f"save_{self.current_player_index}"
        print(f"💾 Состояние игры сохранено: {snapshot_id}")
        return snapshot_id

    def load_state(self, snapshot_id: str) -> bool:
        """Загружает сохранение"""
        print(f"📂 Загрузка состояния: {snapshot_id}")
        return True

    def end_turn(self):
        """Фиксирует завершение хода и передаёт ход следующему"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def get_current_player(self) -> Player:
        """Возвращает текущего игрока"""
        return self.players[self.current_player_index]

    def attach_observer(self, observer):
        """Подписать наблюдателя на игровые события"""
        if self.event_publisher:
            self.event_publisher.attach(observer)

    def detach_observer(self, observer):
        """Отписать наблюдателя от игровых событий"""
        if self.event_publisher:
            self.event_publisher.detach(observer)

    def play_turn(self):
        """Выполняет один полный ход"""
        if self.is_paused:
            print("Игра на паузе")
            return

        current_player = self.get_current_player()

        # Управление стратегиями AI перед ходом
        if current_player.is_ai and current_player.id in self.ai_players:
            self._manage_ai_strategy(current_player)

        self.turn_manager.start_turn(current_player)

        if not current_player.in_jail:
            # Бросок кубиков
            dice_result = self.turn_manager.roll_dice()

            # Перемещение
            cell = self.turn_manager.move_player(current_player, dice_result["sum"])

            # Применение эффектов клетки
            self.turn_manager.apply_cell_effects(current_player, cell)

            # Предложение необязательных действий
            optional_actions = self.turn_manager.offer_optional_actions(current_player)
            if optional_actions:
                print(f"Доступные действия: {len(optional_actions)}")

        # Завершение хода
        self.turn_manager.end_turn()

    def _manage_ai_strategy(self, player: Player):
        """Управляет динамической сменой стратегии AI на основе баланса"""
        ai_player = self.ai_players.get(player.id)
        if not ai_player:
            return

        current_strategy = ai_player.strategy

        # Логика смены стратегии на основе баланса
        if player.balance < 500 and isinstance(current_strategy, AggressiveAIStrategy):
            print(f"\n⚠️ {player.name} в финансовых затруднениях!")
            ai_player.set_strategy(ConservativeAIStrategy())
        elif player.balance > 2000 and isinstance(
            current_strategy, ConservativeAIStrategy
        ):
            print(f"\n💪 {player.name} имеет большой резерв!")
            ai_player.set_strategy(AggressiveAIStrategy())

    def demonstrate_strategy_change(self, player_id: str, new_strategy_name: str):
        """Демонстрирует ручную смену стратегии AI"""
        if player_id in self.ai_players:
            ai_player = self.ai_players[player_id]

            if new_strategy_name == "Balanced":
                new_strategy = BalancedAIStrategy()
            elif new_strategy_name == "Conservative":
                new_strategy = ConservativeAIStrategy()
            elif new_strategy_name == "Aggressive":
                new_strategy = AggressiveAIStrategy()
            else:
                return

            ai_player.set_strategy(new_strategy)
