from __future__ import annotations
import time
from collections import deque
from datetime import date
from typing import Any
from hyperliquid_bot.types import PositionSnapshot,RiskLimits

class RiskManager:
    def __init__(self,limits:RiskLimits)->None:
        self.limits=limits; self._day=date.today(); self._daily_pnl=0.0; self._losses=0; self._trades=deque(); self._last_trade=0.0

    def _reset(self)->None:
        if date.today()!=self._day:
            self._day=date.today(); self._daily_pnl=0.0; self._losses=0; self._trades.clear()
    def sync_realized_pnl(self,pnl:float)->None:
        self._reset(); self._daily_pnl=float(pnl)
    def record_trade(self,pnl:float)->None:
        self._reset(); self._trades.append(time.time()); self._last_trade=time.time()
        self._losses=self._losses+1 if pnl<0 else 0 if pnl>0 else self._losses
    def can_trade(self,position:PositionSnapshot)->tuple[bool,str]:
        self._reset(); now=time.time()
        while self._trades and self._trades[0]<now-3600: self._trades.popleft()
        if self.limits.kill_switch:return False,"kill_switch"
        if self._daily_pnl<=-abs(self.limits.max_daily_loss_usd):return False,"daily_loss_limit"
        if self._losses>=self.limits.max_consecutive_losses:return False,"consecutive_loss_limit"
        if now-self._last_trade<self.limits.cooldown_seconds:return False,"cooldown"
        if len(self._trades)>=self.limits.max_trades_per_hour:return False,"trade_rate_limit"
        if position.notional>self.limits.max_position_usd:return False,"max_position"
        if abs(position.leverage)>self.limits.max_leverage:return False,"max_leverage"
        return True,"ok"
    def status(self)->dict[str,Any]:
        return {"daily_realized_pnl":self._daily_pnl,"consecutive_losses":self._losses,"trades_last_hour":len(self._trades),"limits":self.limits.__dict__}
