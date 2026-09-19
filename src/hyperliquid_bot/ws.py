from __future__ import annotations
import asyncio,json,logging
from collections.abc import AsyncIterator
from typing import Any
import websockets
from hyperliquid_bot.types import Network

logger=logging.getLogger(__name__)

class HyperliquidWS:
    """Public Hyperliquid websocket feed. No simulated market data."""
    def __init__(self,network:Network)->None:
        self.url="wss://api.hyperliquid-testnet.xyz/ws" if network==Network.TESTNET else "wss://api.hyperliquid.xyz/ws"
    async def stream(self,coin:str)->AsyncIterator[dict[str,Any]]:
        while True:
            try:
                async with websockets.connect(self.url,ping_interval=20,ping_timeout=20,max_queue=2048) as ws:
                    for channel in ("l2Book","trades","bbo"):
                        await ws.send(json.dumps({"method":"subscribe","subscription":{"type":channel,"coin":coin}}))
                    async for raw in ws:
                        msg=json.loads(raw)
                        if msg.get("channel") in {"l2Book","trades","bbo"}:
                            yield msg
            except (OSError,asyncio.TimeoutError,websockets.WebSocketException) as exc:
                logger.warning("Hyperliquid WS disconnected: %s",exc)
                await asyncio.sleep(2)
