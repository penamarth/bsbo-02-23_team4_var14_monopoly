"""
3апуск игры Монополия
"""

from ai_player import AIPlayer
from game import Game
from game_strategy import AggressiveStrategy, ConservativeStrategy
from player import Player


def main():
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "МОНОПОЛИЯ - ДЕМО ВЕРСИЯ" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")

    # Создание игры
    game = Game()

    # Создание игроков
    print("\nСоздание игроков...")

    # Человек (или симуляция человека)
    player1 = Player("Никита")
    game.add_player(player1)
    print(f"   Добавлен игрок: {player1.name} (Человек)")

    # ИИ игрок с агрессивной стратегией
    player2 = AIPlayer("Робот-1", strategy=AggressiveStrategy())
    game.add_player(player2)
    print(f"   Добавлен игрок: {player2.name} (ИИ - Агрессивная стратегия)")

    # ИИ игрок с консервативной стратегией
    player3 = AIPlayer("Робот-2", strategy=ConservativeStrategy())
    game.add_player(player3)
    print(f"   Добавлен игрок: {player3.name} (ИИ - Консервативная стратегия)")

    # Запуск игры
    game.start_game()

    print("\n" + "─" * 60)

    # Игровой цикл - ограниченное количество ходов для демонстрации
    max_turns = 15
    turn_count = 0

    input("\nНажмите Enter для начала игры...")

    while game.game_state.value == "IN_PROGRESS" and turn_count < max_turns:
        turn_count += 1
        print(f"\n{'─' * 60}")
        print(f"Ход #{turn_count}")
        print(f"{'─' * 60}")

        game.play_turn()

        # Пауза между ходами для читаемости
        if turn_count < max_turns:
            input("\n⏸️  Нажмите Enter для следующего хода...")

    # Финальная статистика
    print("\n" + "=" * 60)
    print("ФИНАЛЬНАЯ СТАТИСТИКА")
    print("=" * 60)

    for i, player in enumerate(game.players, 1):
        status = "БАНКРОТ" if player.is_bankrupt else "Активен"
        print(f"\n{i}. {player.name} - {status}")
        print(f"   Баланс: {player.balance}₽")
        print(f"   Позиция: {player.position}")
        print(f"   Недвижимость: {len(player.properties)} объектов")

        if player.properties:
            print("      Список недвижимости:")
            for prop in player.properties:
                print(
                    f"      - {prop.name} (цена: {prop.price}₽, аренда: {prop.rent}₽)"
                )

    print("\n" + "=" * 60)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")


if __name__ == "__main__":
    main()
