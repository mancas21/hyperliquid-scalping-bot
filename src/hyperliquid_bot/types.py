from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class Network(str, Enum):
    MAINNET = "mainnet"
    TESTNET = "testnet"

class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"
    @property
    def opposite(self) -> "Side":
        return Side.SELL if self is Side.BUY else Side.BUY

@dataclass(frozen=True)
class OrderIntent:
    coin: str
    side: Side
    size: float
    price: float | None = None
    reduce_only: bool = False
    post_only: bool = False
    tif: str = "Ioc"
    tag: str = ""

@dataclass(frozen=True)
class PositionSnapshot:
    coin: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: float
    @property
    def notional(self) -> float:
        return abs(self.size * self.mark_price)
    @property
    def side(self) -> Side | None:
        return Side.BUY if self.size > 0 else Side.SELL if self.size < 0 else None

@dataclass
class RiskLimits:
    max_position_usd: float = 10_000.0
    max_daily_loss_usd: float = 500.0
    max_leverage: float = 5.0
    max_trades_per_hour: int = 30
    cooldown_seconds: float = 10.0
    max_consecutive_losses: int = 5
    kill_switch: bool = False

@dataclass
class BotConfig:
    bot_id: str
    coin: str = "ETH"
    network: Network = Network.TESTNET
    size: float = 0.01
    risk: RiskLimits = field(default_factory=RiskLimits)
    params: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class Signal:
    action: str
    confidence: float = 1.0
    reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class BookFeatures:
    bid: float
    ask: float
    mid: float
    microprice: float
    spread_bps: float
    imbalance: float
    bid_depth: float
    ask_depth: float
    timestamp_ms: int

@dataclass(frozen=True)
class FlowFeatures:
    aggressive_buy_volume: float
    aggressive_sell_volume: float
    flow_imbalance: float
    trade_count: int
    window_seconds: float
