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
    """Live runner. Account state is reconciled from Hyperliquid before every decision."""
    def __init__(self,strategy:Strategy,config:BotConfig|None=None,poll_interval:float=1.0)->None:
        self.strategy=strategy; self.config=config or strategy.config; self.poll_interval=poll_interval
        self.client=HyperliquidClient(self.config); self.risk=RiskManager(self.config.risk)
        self.flow=TradeFlow(float(self.config.params.get("flow_window_seconds",10))); self._running=False

    def _position(self)->PositionSnapshot:
        state=self.client.get_user_state(); coin=self.config.coin; mark=self.client.get_mid_price(coin)
        for item in state.get("assetPositions",[]):
            p=item.get("position",item)
            if p.get("coin")==coin:
                return PositionSnapshot(coin,float(p.get("szi",0)),float(p.get("entryPx",0) or 0),mark,
                    float(p.get("unrealizedPnl",0)),float((p.get("leverage") or {}).get("value",1)))
        return PositionSnapshot(coin,0,0,mark,0,0)

    def _market_snapshot(self)->dict[str,Any]:
        coin=self.config.coin; book=self.client.get_l2_book(coin); trades=self.client.get_recent_trades(coin)
        return {"coin":coin,"book":book,"flow":self.flow.update(trades),"mid":self.client.get_mid_price(coin)}

    async def tick_once(self)->dict[str,Any]:
        position=self._position()
        self.risk.sync_realized_pnl(self.client.get_today_realized_pnl())
        market=self._market_snapshot(); signal=self.strategy.on_tick(market)
        ok,reason=self.risk.can_trade(position)
        result={"signal":signal.action,"confidence":signal.confidence,"reason":signal.reason,"risk":reason,"position":position.size,"orders":[]}
        if not ok or signal.action not in {"long","short"}: return result
        orders=self.strategy.build_orders(signal,market)
        for order in orders:
            if position.size and ((position.size>0)!=(order.side.value=="buy")) and not order.reduce_only: continue
            payload={"coin":order.coin,"is_buy":order.side.value=="buy","sz":order.size,"limit_px":order.price,
                     "reduce_only":order.reduce_only,"order_type":{"limit":{"tif":order.tif}}}
            result["orders"].append(self.client.place_order(payload))
        return result

    async def run(self)->None:
        self._running=True
        logger.info("Starting %s on %s/%s",self.strategy.name,self.config.coin,self.config.network.value)
        while self._running:
            try: logger.debug("Tick: %s",await self.tick_once())
            except Exception: logger.exception("Tick failed")
            await asyncio.sleep(self.poll_interval)
    def stop(self)->None:self._running=False

def default_config(bot_id:str,coin:str="ETH",**params:Any)->BotConfig:
    return BotConfig(bot_id=bot_id,coin=coin,network=Network(os.getenv("HL_NETWORK","testnet")),
        risk=RiskLimits(max_position_usd=float(os.getenv("HL_MAX_POSITION_USD","10000")),
        max_daily_loss_usd=float(os.getenv("HL_MAX_DAILY_LOSS_USD","500")),
        max_leverage=float(os.getenv("HL_MAX_LEVERAGE","5")),
        max_trades_per_hour=int(os.getenv("HL_MAX_TRADES_PER_HOUR","30")),
        cooldown_seconds=float(os.getenv("HL_COOLDOWN_SECONDS","10")),
        max_consecutive_losses=int(os.getenv("HL_MAX_CONSECUTIVE_LOSSES","5")),
        kill_switch=os.getenv("HL_KILL_SWITCH","false").lower()=="true"),params=params)
