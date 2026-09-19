from __future__ import annotations
import time
from collections import deque
from typing import Any
from hyperliquid_bot.types import BookFeatures, FlowFeatures

def _levels(book: dict[str, Any], key: str) -> list[tuple[float,float]]:
    out=[]
    for row in book.get(key, [])[:10]:
        px=float(row.get("px",row.get("price",0))); sz=float(row.get("sz",row.get("size",0)))
        if px>0 and sz>0: out.append((px,sz))
    return out

def compute_book_features(book: dict[str, Any], timestamp_ms: int|None=None) -> BookFeatures|None:
    bids,asks=_levels(book,"bids"),_levels(book,"asks")
    if not bids or not asks: return None
    bid,bid_sz=bids[0]; ask,ask_sz=asks[0]
    if ask<=bid: return None
    mid=(bid+ask)/2; total=bid_sz+ask_sz
    return BookFeatures(bid,ask,mid,(ask*bid_sz+bid*ask_sz)/total,
        (ask-bid)/mid*10000,(bid_sz-ask_sz)/total,sum(s for _,s in bids),
        sum(s for _,s in asks),timestamp_ms or int(time.time()*1000))

class TradeFlow:
    def __init__(self,window_seconds:float=10.0): self.window_seconds=window_seconds; self._trades=deque()
    def update(self,trades:list[dict[str,Any]])->FlowFeatures:
        now=time.time()
        for t in trades:
            ts=float(t.get("time",t.get("timestamp",now*1000)))/1000
            sz=float(t.get("sz",t.get("size",0))); side=str(t.get("side","")).lower()
            if sz>0: self._trades.append((ts,sz,side in {"b","buy","buy_aggressor"}))
        cutoff=now-self.window_seconds
        while self._trades and self._trades[0][0]<cutoff: self._trades.popleft()
        buy=sum(s for _,s,b in self._trades if b); sell=sum(s for _,s,b in self._trades if not b); total=buy+sell
        return FlowFeatures(buy,sell,(buy-sell)/total if total else 0.0,len(self._trades),self.window_seconds)
