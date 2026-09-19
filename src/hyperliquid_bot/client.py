from __future__ import annotations
import os
from typing import Any
from hyperliquid_bot.types import BotConfig, Network

class HyperliquidClient:
    MAINNET_URL = "https://api.hyperliquid.xyz"
    TESTNET_URL = "https://api.hyperliquid-testnet.xyz"

    def __init__(self, config: BotConfig, private_key: str | None = None) -> None:
        self.config = config
        self.private_key = private_key or os.getenv("HL_PRIVATE_KEY")
        self._info = None
        self._exchange = None

    def _ensure_clients(self) -> None:
        if self._info is not None:
            return
        from hyperliquid.info import Info
        from hyperliquid.utils import constants
        url = constants.TESTNET_API_URL if self.config.network == Network.TESTNET else constants.MAINNET_API_URL
        self._info = Info(url, skip_ws=True)
        if self.private_key:
            from eth_account import Account
            from hyperliquid.exchange import Exchange
            self._exchange = Exchange(Account.from_key(self.private_key), url)

    def get_l2_book(self, coin: str | None = None) -> dict[str, Any]:
        self._ensure_clients()
        return self._info.l2_snapshot(coin or self.config.coin)

    def get_recent_trades(self, coin: str | None = None) -> list[dict[str, Any]]:
        self._ensure_clients()
        return self._info.post("/info", {"type": "recentTrades", "coin": coin or self.config.coin})

    def get_user_state(self, address: str | None = None) -> dict[str, Any]:
        self._ensure_clients()
        user = address or (self._exchange.account_address if self._exchange else os.getenv("HL_ACCOUNT_ADDRESS"))
        return self._info.user_state(user) if user else {}

    def get_open_orders(self, address: str | None = None) -> list[dict[str, Any]]:
        self._ensure_clients()
        user = address or (self._exchange.account_address if self._exchange else os.getenv("HL_ACCOUNT_ADDRESS"))
        return self._info.open_orders(user) if user else []

    def place_order(self, order: dict[str, Any]) -> dict[str, Any]:
        self._ensure_clients()
        if not self._exchange:
            raise RuntimeError("HL_PRIVATE_KEY is required for order placement")
        return self._exchange.order(**order)

    def cancel_all(self, coin: str | None = None) -> Any:
        self._ensure_clients()
        if not self._exchange:
            return None
        return self._exchange.cancel_all(coin or self.config.coin)
