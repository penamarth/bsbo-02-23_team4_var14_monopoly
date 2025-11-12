"""
Основной класс Game - управление игровой сессией
"""

from enum import Enum
from typing import Optional

from bank import Bank
from board import Board
from dice import Dice
from game_observer import ConsoleGameObserver, GameSubject
from game_rules import GameRules
from player import Player


class GameState(Enum):
    """Состояние игры"""

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class Game(GameSubject):
    _instance: Optional["Game"] = None

    def __init__(self):
        super().__init__()
        self.players: list[Player] = []
        self.current_player: Optional[Player] = None
        self.current_player_index: int = 0
        self.board: Board = Board()
        self.bank: Bank = Bank()
        self.dice: Dice = Dice()
        self.game_rules: GameRules = GameRules()
        self.game_state: GameState = GameState.NOT_STARTED

        # Singleton для доступа из других классов
        Game._instance = self

        # Подключить консольный наблюдатель по умолчанию
        self.attach(ConsoleGameObserver())

    @classmethod
    def get_instance(cls) -> Optional["Game"]:
        return cls._instance

    def add_player(self, player: Player):
        self.players.append(player)
        # Установить начальные деньги
        player._set_balance(self.game_rules.start_money)

    def start_game(self):
        if len(self.players) < 2:
            print("Для начала игры нужно минимум 2 игрока!")
            return

        print("\n" + "=" * 60)
        print("ИГРА 'МОНОПОЛИЯ' НАЧИНАЕТСЯ!")
        print("=" * 60)
        print(f"\nИгроки ({len(self.players)}):")
        for i, player in enumerate(self.players, 1):
            player_type = "ИИ" if hasattr(player, "strategy") else "Человек"
            print(f"  {i}. {player.name} ({player_type}) - {player.balance}₽")

        self.game_state = GameState.IN_PROGRESS
        self.current_player_index = 0
        self.current_player = self.players[0]

        print(f"\nПервым ходит: {self.current_player.name}")

    def play_turn(self):
        if self.game_state != GameState.IN_PROGRESS:
            print("Игра не запущена!")
            return

        player = self.current_player

        if player.is_bankrupt:
            print(f"\n{player.name} обанкротился, пропускаем ход")
            self.next_turn()
            return

        self.notify_turn_changed(player)
        print(f"Позиция: {player.position}, Баланс: {player.balance}₽")
        print(f"Недвижимость: {len(player.properties)} объектов")

        # Обработка тюрьмы
        if player.in_jail:
            self._handle_jail_turn(player)
            return

        # Бросок костей
        dice_values = self.dice.roll()
        dice_sum = self.dice.get_sum()

        self.notify_dice_rolled(player, dice_values, dice_sum, self.dice.is_double)

        # Проверка третьего дубля подряд - отправка в тюрьму
        if self.dice.double_count >= 3:
            print(f"🚨 {player.name} выбросил 3 дубля подряд и отправляется в ТЮРЬМУ!")
            player.in_jail = True
            old_pos = player.position
            player.position = 10  # Позиция тюрьмы
            self.notify_player_moved(player, old_pos, player.position)
            self.dice.reset_double_count()
            self.next_turn()
            return

        # Перемещение
        old_position = player.position
        cell = player.move(dice_sum, self.board)
        self.notify_player_moved(player, old_position, player.position)

        print(f"📍 {player.name} попал на клетку: '{cell.name}'")

        # Обработка действия клетки
        self.board.process_cell_action(player, cell)

        # Если дубль - дополнительный ход
        if self.dice.is_double and not player.is_bankrupt:
            print(f"\n{player.name} выбросил дубль и получает дополнительный ход!")
            input("\n   Нажмите Enter для следующего броска...")
            self.play_turn()  # Рекурсивный вызов для дополнительного хода
        else:
            self.dice.reset_double_count()
            self.next_turn()

    def _handle_jail_turn(self, player: Player):
        print(f"\n{player.name} находится в тюрьме (попытка {player.jail_turns + 1}/3)")

        # Для упрощения - автоматическая попытка выбросить дубль
        dice_values = self.dice.roll()
        dice_sum = self.dice.get_sum()

        self.notify_dice_rolled(player, dice_values, dice_sum, self.dice.is_double)

        if self.dice.is_double:
            print(f"{player.name} выбросил дубль и освобождается из тюрьмы!")
            player.in_jail = False
            player.jail_turns = 0

            # Перемещение после освобождения
            old_position = player.position
            cell = player.move(dice_sum, self.board)
            self.notify_player_moved(player, old_position, player.position)
            print(f"{player.name} попал на клетку: '{cell.name}'")
            self.board.process_cell_action(player, cell)
        else:
            player.jail_turns += 1

            if player.jail_turns >= self.game_rules.max_jail_turns:
                # Принудительная оплата штрафа
                print(f"{player.name} провел 3 хода в тюрьме и должен заплатить штраф!")
                success = self.bank.transfer(player, None, self.game_rules.jail_fine)

                if success:
                    print(
                        f"{player.name} заплатил {self.game_rules.jail_fine}₽ и освобожден"
                    )
                    player.in_jail = False
                    player.jail_turns = 0
                else:
                    print(f"У {player.name} нет денег на штраф!")
                    self.bank.handle_bankruptcy(player)

        self.next_turn()

    def next_turn(self):
        # Проверка условия окончания игры
        active_players = [p for p in self.players if not p.is_bankrupt]

        if len(active_players) <= 1:
            self.game_state = GameState.FINISHED
            if active_players:
                winner = active_players[0]
                print(f"\n{'=' * 60}")
                print(f"ИГРА ОКОНЧЕНА! ПОБЕДИТЕЛЬ: {winner.name}")
                print(f"{'=' * 60}")
                print(f"Финальный баланс: {winner.balance}₽")
                print(f"Недвижимость: {len(winner.properties)} объектов")
            return

        # Переход к следующему игроку
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.current_player = self.players[self.current_player_index]

        # Пропустить обанкротившихся игроков
        while self.current_player.is_bankrupt:
            self.current_player_index = (self.current_player_index + 1) % len(
                self.players
            )
            self.current_player = self.players[self.current_player_index]

    def save_game_state(self):
        print(f"\nСостояние игры сохранено (Ход: {self.current_player.name})")
