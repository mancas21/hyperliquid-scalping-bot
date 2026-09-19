from __future__ import annotations
import asyncio,logging,os
from typing import Any
from hyperliquid_bot.client import HyperliquidClient
from hyperliquid_bot.orderflow import TradeFlow
from hyperliquid_bot.risk import RiskManager
from hyperliquid_bot.strategy_base import Strategy
from hyperliquid_bot.types import BotConfig,Network,PositionSnapshot,RiskLimits

logger=logging.getLogger(__name__)

class BotRunner:
    def __init__(self,strategy:Strategy,config:BotConfig|None=None,poll_interval:float=1.0)->None:
        self.strategy=strategy; self.config=config or strategy.config; self.poll_interval=poll_interval
        self.client=HyperliquidClient(self.config); self.risk=RiskManager(self.config.risk)
        self.flow=TradeFlow(float(self.config.params.get("flow_window_seconds",10))); self._running=False

    def _position(self)->PositionSnapshot:
        state=self.client.get_user_state(); mark=self.client.get_mid_price()
        for item in state.get("assetPositions",[]):
            p=item.get("position",item)
            if p.get("coin")==self.config.coin:
                lev=p.get("leverage") or {}
                return PositionSnapshot(self.config.coin,float(p.get("szi",0)),float(p.get("entryPx",0) or 0),mark,
                    float(p.get("unrealizedPnl",0)),float(lev.get("value",0) or 0))
        return PositionSnapshot(self.config.coin,0,0,mark,0,0)

    def _market_snapshot(self)->dict[str,Any]:
        coin=self.config.coin; book=self.client.get_l2_book(coin); trades=self.client.get_recent_trades(coin)
        return {"coin":coin,"book":book,"flow":self.flow.update(trades),"mid":self.client.get_mid_price(coin)}

    async def tick_once(self)->dict[str,Any]:
        position=self._position(); self.risk.sync_realized_pnl(self.client.get_today_realized_pnl())
        market=self._market_snapshot(); signal=self.strategy.on_tick(market)
        ok,reason=self.risk.can_trade(position)
        result={"signal":signal.action,"confidence":signal.confidence,"reason":signal.reason,"risk":reason,"position":position.size,"orders":[]}
        if not ok or signal.action not in {"long","short"}: return result
        for order in self.strategy.build_orders(signal,market):
            if position.size and ((position.size>0)!=(order.side.value=="buy")) and not order.reduce_only: continue
            book=market["book"]; bid=float(book["bids"][0]["px"]); ask=float(book["asks"][0]["px"])
            slip=float(self.config.params.get("max_entry_slippage_bps",5))/10000
            px=order.price or (ask*(1+slip) if order.side.value=="buy" else bid*(1-slip))
            payload={"coin":order.coin,"is_buy":order.side.value=="buy","sz":order.size,"limit_px":px,
                     "reduce_only":order.reduce_only,"order_type":{"limit":{"tif":order.tif}}}
            result["orders"].append(self.client.place_order(payload))
            self.risk.record_trade(0.0)
        return result

    async def run(self)->None:
        self._running=True
        while self._running:
            try: logger.debug("Tick: %s",await self.tick_once())
            except Exception: logger.exception("Tick failed")
            await asyncio.sleep(self.poll_interval)
    def stop(self)->None:self._running=False

def default_config(bot_id:str,coin:str="ETH",**params:Any)->BotConfig:
    return BotConfig(bot_id=bot_id,coin=coin,network=Network(os.getenv("HL_NETWORK","testnet")),
        risk=RiskLimits(max_position_usd=float(os.getenv("HL_MAX_POSITION_USD","10000")),
        max_daily_loss_usd=float(os.getenv("HL_MAX_DAILY_LOSS_USD","500")),max_leverage=float(os.getenv("HL_MAX_LEVERAGE","5")),
        max_trades_per_hour=int(os.getenv("HL_MAX_TRADES_PER_HOUR","30")),cooldown_seconds=float(os.getenv("HL_COOLDOWN_SECONDS","10")),
        max_consecutive_losses=int(os.getenv("HL_MAX_CONSECUTIVE_LOSSES","5")),kill_switch=os.getenv("HL_KILL_SWITCH","false").lower()=="true"),params=params)
