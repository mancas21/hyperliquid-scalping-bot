from __future__ import annotations
from typing import Any
from hyperliquid_bot.client import HyperliquidClient
from hyperliquid_bot.types import PositionSnapshot,Side

class ExecutionEngine:
    """Exchange-side protection and reconciliation helpers."""
    def __init__(self,client:HyperliquidClient,coin:str,tp_bps:float=12,sl_bps:float=8)->None:
        self.client=client; self.coin=coin; self.tp_bps=tp_bps; self.sl_bps=sl_bps

    def protection_orders(self,position:PositionSnapshot)->list[dict[str,Any]]:
        if not position.size or not position.entry_price:return []
        long=position.size>0; s=abs(position.size); entry=position.entry_price
        tp=entry*(1+self.tp_bps/10000) if long else entry*(1-self.tp_bps/10000)
        sl=entry*(1-self.sl_bps/10000) if long else entry*(1+self.sl_bps/10000)
        return [
            {"coin":self.coin,"is_buy":not long,"sz":s,"limit_px":tp,"reduce_only":True,
             "order_type":{"trigger":{"triggerPx":tp,"isMarket":True,"tpsl":"tp"}}},
            {"coin":self.coin,"is_buy":not long,"sz":s,"limit_px":sl,"reduce_only":True,
             "order_type":{"trigger":{"triggerPx":sl,"isMarket":True,"tpsl":"sl"}}},
        ]
