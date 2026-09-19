"""L2/order-flow microstructure scalper using observed Hyperliquid data only."""
from __future__ import annotations
from typing import Any
from hyperliquid_bot.orderflow import compute_book_features
from hyperliquid_bot.strategy_base import Strategy
from hyperliquid_bot.types import OrderIntent, Side, Signal

class StrategyImpl(Strategy):
    name="scalp-v2"
    description="L2 imbalance + microprice + aggressive trade-flow scalper"

    def on_tick(self, market: dict[str,Any]) -> Signal:
        book=compute_book_features(market.get("book",{})); flow=market.get("flow")
        if book is None or flow is None: return Signal("hold",0.0,"insufficient live L2/trade data")
        if book.spread_bps>float(self.config.params.get("max_spread_bps",8)): return Signal("hold",0.0,"spread_filter")
        mi=float(self.config.params.get("min_imbalance",0.18)); mf=float(self.config.params.get("min_flow_imbalance",0.15))
        edge=(book.microprice-book.mid)/book.mid*10000
        ls=int(book.imbalance>mi)+int(flow.flow_imbalance>mf)+int(edge>0.5)
        ss=int(book.imbalance<-mi)+int(flow.flow_imbalance<-mf)+int(edge<-0.5)
        threshold=int(self.config.params.get("min_score",2))
        if ls>=threshold and ss==0: return Signal("long",ls/3,"L2+flow bullish",{"imbalance":book.imbalance,"flow_imbalance":flow.flow_imbalance})
        if ss>=threshold and ls==0: return Signal("short",ss/3,"L2+flow bearish",{"imbalance":book.imbalance,"flow_imbalance":flow.flow_imbalance})
        return Signal("hold",0.0,"no order-flow edge")

    def build_orders(self,signal:Signal,market:dict[str,Any])->list[OrderIntent]:
        if signal.action not in {"long","short"}: return []
        side=Side.BUY if signal.action=="long" else Side.SELL
        return [OrderIntent(self.config.coin,side,float(self.config.size),tif="Ioc",tag=f"entry_{signal.action}")]
