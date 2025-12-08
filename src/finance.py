"""
Финансовый агрегат: Bank, TradeManager, TradeOffer, Auction
Корневая сущность агрегата: Bank
"""

from typing import Dict, List, Optional

from models import Player, PropertyCell


class Bank:
    """
    Единый центр финансов и обменов
    Корневая сущность агрегата "Торговля и Финансы"
    """

    def __init__(self):
        self.reserves = 1000000  # Виртуальный баланс банка
        self.transaction_log: List[Dict] = []

    def _log_transaction(self, transaction_type: str, **kwargs):
        """Логирование транзакции"""
        log_entry = {"type": transaction_type, **kwargs}
        self.transaction_log.append(log_entry)

    def debit(self, player: Player, amount: int, reason: str) -> bool:
        """Списывает деньги с игрока"""
        if player.balance < amount:
            return False
        player.adjust_balance(-amount)
        self._log_transaction("debit", player=player.name, amount=amount, reason=reason)
        return True

    def credit(self, player: Player, amount: int, reason: str):
        """Начисляет деньги игроку"""
        player.adjust_balance(amount)
        self._log_transaction(
            "credit", player=player.name, amount=amount, reason=reason
        )

    def transfer(
        self, from_player: Player, to_player: Player, amount: int, reason: str
    ) -> bool:
        """Перевод между игроками"""
        if from_player.balance < amount:
            return False
        from_player.adjust_balance(-amount)
        to_player.adjust_balance(amount)
        self._log_transaction(
            "transfer",
            from_player=from_player.name,
            to_player=to_player.name,
            amount=amount,
            reason=reason,
        )
        return True

    def purchase_property(self, player: Player, property_cell: PropertyCell) -> bool:
        """Оформляет покупку собственности"""
        if property_cell.owner is not None:
            return False
        if not self.debit(
            player, property_cell.price, f"Purchase {property_cell.name}"
        ):
            return False
        property_cell.owner = player
        player.add_property(property_cell)
        return True

    def pay_rent(
        self, payer: Player, owner: Player, property_cell: PropertyCell
    ) -> bool:
        """Взыскивает аренду"""
        rent = property_cell.calculate_rent()
        if rent == 0:
            return True
        return self.transfer(payer, owner, rent, f"Rent for {property_cell.name}")

    def mortgage_property(self, player: Player, property_cell: PropertyCell) -> bool:
        """Кладёт собственность в залог"""
        if property_cell.owner != player or property_cell.is_mortgaged:
            return False
        if property_cell.build_level > 0:
            return False
        mortgage_value = property_cell.price // 2
        self.credit(player, mortgage_value, f"Mortgage {property_cell.name}")
        property_cell.mark_mortgaged()
        return True

    def redeem_mortgage(self, player: Player, property_cell: PropertyCell) -> bool:
        """Выкупает залог"""
        if property_cell.owner != player or not property_cell.is_mortgaged:
            return False
        redeem_cost = int(property_cell.price * 0.55)  # 50% + 10% надбавка
        if not self.debit(player, redeem_cost, f"Redeem {property_cell.name}"):
            return False
        property_cell.redeem_mortgage()
        return True

    def pay_build_cost(
        self, player: Player, property_cell: PropertyCell, board
    ) -> bool:
        """Оплачивает строительство"""
        if not property_cell.can_build(board):
            return False
        cost = (
            property_cell.house_cost
            if property_cell.build_level < 4
            else property_cell.hotel_cost
        )
        if not self.debit(player, cost, f"Build on {property_cell.name}"):
            return False
        property_cell.upgrade_building()
        return True

    def refund_building(self, player: Player, property_cell: PropertyCell, board):
        """Выплачивает возврат при сносе"""
        if not property_cell.can_sell_building(board):
            return
        refund = property_cell.house_cost // 2
        self.credit(player, refund, f"Sell building on {property_cell.name}")
        property_cell.downgrade_building()

    def handle_card_payment(self, player: Player, amount: int) -> bool:
        """Обрабатывает денежные эффекты карт"""
        if amount > 0:
            self.credit(player, amount, "Card effect")
            return True
        else:
            return self.debit(player, abs(amount), "Card effect")

    def settle_trade(self, trade_offer: "TradeOffer") -> bool:
        """Применяет одобренную сделку"""
        # Проверка средств
        if trade_offer.money_from > 0:
            if trade_offer.from_player.balance < trade_offer.money_from:
                return False
        if trade_offer.money_to > 0:
            if trade_offer.to_player.balance < trade_offer.money_to:
                return False

        # Обмен деньгами
        if trade_offer.money_from > 0:
            self.transfer(
                trade_offer.from_player,
                trade_offer.to_player,
                trade_offer.money_from,
                "Trade",
            )
        if trade_offer.money_to > 0:
            self.transfer(
                trade_offer.to_player,
                trade_offer.from_player,
                trade_offer.money_to,
                "Trade",
            )

        # Обмен собственностью
        for prop in trade_offer.properties_from:
            prop.owner = trade_offer.to_player
            trade_offer.from_player.remove_property(prop)
            trade_offer.to_player.add_property(prop)

        for prop in trade_offer.properties_to:
            prop.owner = trade_offer.from_player
            trade_offer.to_player.remove_property(prop)
            trade_offer.from_player.add_property(prop)

        return True

    def resolve_auction(self, auction_result: Dict):
        """Финализирует аукцион"""
        if "winner" not in auction_result or "amount" not in auction_result:
            return
        winner = auction_result["winner"]
        amount = auction_result["amount"]
        property_cell = auction_result["property"]

        if self.debit(winner, amount, f"Auction {property_cell.name}"):
            property_cell.owner = winner
            winner.add_property(property_cell)


class TradeOffer:
    """
    Модель торгового предложения
    """

    def __init__(self, from_player: Player, to_player: Player):
        self.from_player = from_player
        self.to_player = to_player
        self.money_from = 0
        self.money_to = 0
        self.properties_from: List[PropertyCell] = []
        self.properties_to: List[PropertyCell] = []
        self.cards_from: List = []
        self.cards_to: List = []
        self.comment = ""

    def is_valid(self) -> bool:
        """Базовая проверка наполненности"""
        has_offer = (
            self.money_from > 0
            or len(self.properties_from) > 0
            or len(self.cards_from) > 0
        )
        has_request = (
            self.money_to > 0 or len(self.properties_to) > 0 or len(self.cards_to) > 0
        )
        return has_offer or has_request


class TradeManager:
    """
    Управляет циклом торговли
    """

    def __init__(self, bank: Bank):
        self.pending_offers: List[TradeOffer] = []
        self.bank = bank
        self.rules = {}  # Ограничения на сделки

    def create_offer(
        self, from_player: Player, to_player: Player, payload: Dict
    ) -> TradeOffer:
        """Формирует предложение"""
        offer = TradeOffer(from_player, to_player)
        offer.money_from = payload.get("money_from", 0)
        offer.money_to = payload.get("money_to", 0)
        offer.properties_from = payload.get("properties_from", [])
        offer.properties_to = payload.get("properties_to", [])
        return offer

    def validate(self, offer: TradeOffer) -> tuple[bool, str]:
        """Проверяет допустимость сделки"""
        if not offer.is_valid():
            return False, "Empty offer"

        # Проверка средств
        if offer.money_from > offer.from_player.balance:
            return False, "Insufficient funds from sender"
        if offer.money_to > offer.to_player.balance:
            return False, "Insufficient funds from receiver"

        # Проверка собственности
        for prop in offer.properties_from:
            if prop.owner != offer.from_player:
                return False, f"{prop.name} not owned by sender"
            if prop.build_level > 0:
                return False, f"{prop.name} has buildings"

        for prop in offer.properties_to:
            if prop.owner != offer.to_player:
                return False, f"{prop.name} not owned by receiver"
            if prop.build_level > 0:
                return False, f"{prop.name} has buildings"

        return True, "Valid"

    def submit(self, offer: TradeOffer) -> bool:
        """Отправляет партнёру"""
        valid, reason = self.validate(offer)
        if not valid:
            return False
        self.pending_offers.append(offer)
        return True

    def accept(self, offer: TradeOffer) -> bool:
        """Принимает сделку"""
        if offer not in self.pending_offers:
            return False
        success = self.bank.settle_trade(offer)
        if success:
            self.pending_offers.remove(offer)
        return success

    def decline(self, offer: TradeOffer, reason: str):
        """Отклоняет сделку"""
        if offer in self.pending_offers:
            self.pending_offers.remove(offer)

    def counter(self, offer: TradeOffer, adjustments: Dict) -> TradeOffer:
        """Формирует встречное предложение"""
        # Меняем местами стороны
        counter_offer = TradeOffer(offer.to_player, offer.from_player)
        counter_offer.money_from = adjustments.get("money_from", offer.money_to)
        counter_offer.money_to = adjustments.get("money_to", offer.money_from)
        counter_offer.properties_from = adjustments.get(
            "properties_from", offer.properties_to
        )
        counter_offer.properties_to = adjustments.get(
            "properties_to", offer.properties_from
        )
        return counter_offer


class Auction:
    """
    Проводит торги при отказе от покупки
    """

    def __init__(self):
        self.property: Optional[PropertyCell] = None
        self.participants: List[Player] = []
        self.bids: List[tuple[Player, int]] = []
        self.is_active = False

    def start(self, property_cell: PropertyCell, participants: List[Player]):
        """Открывает аукцион"""
        self.property = property_cell
        self.participants = participants
        self.bids = []
        self.is_active = True

    def place_bid(self, player: Player, amount: int) -> bool:
        """Делает ставку"""
        if not self.is_active or player not in self.participants:
            return False
        if player.balance < amount:
            return False
        if self.bids and amount <= self.bids[-1][1]:
            return False
        self.bids.append((player, amount))
        return True

    def close(self) -> Optional[Dict]:
        """Завершает торги"""
        self.is_active = False
        if not self.bids:
            return None
        winner, amount = self.bids[-1]
        return {"winner": winner, "amount": amount, "property": self.property}
