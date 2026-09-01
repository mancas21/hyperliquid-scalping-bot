"""Micro-trend scalping on Hyperliquid."""
from __future__ import annotations
from typing import Any
from hyperliquid_bot.strategy_base import Strategy
from hyperliquid_bot.types import OrderIntent, Side, Signal

class StrategyImpl(Strategy):
    name = "scalp"
    description = "1m micro-trend scalps with tight TP/SL"

    def on_tick(self, market: dict[str, Any]) -> Signal:
        candles = market.get("candles", [])
        if len(candles) < 3:
            return Signal("hold", 0.2, "warming up")
        c1, c2 = float(candles[-2].get("c", 0)), float(candles[-1].get("c", 0))
        tp_bps = self.config.params.get("tp_bps", 5)
        if c2 > c1 * (1 + tp_bps / 20_000):
            return Signal("long", 0.7, "micro uptick")
        if c2 < c1 * (1 - tp_bps / 20_000):
            return Signal("short", 0.7, "micro downtick")
        return Signal("hold", 0.4, "no edge")

    def build_orders(self, signal: Signal, market: dict[str, Any]) -> list[OrderIntent]:
        sz = self.config.size * 0.5
        if signal.action == "long":
            return [OrderIntent(self.config.coin, Side.BUY, sz, None, tag="scalp_long")]
        if signal.action == "short":
            return [OrderIntent(self.config.coin, Side.SELL, sz, None, tag="scalp_short")]
        return []
