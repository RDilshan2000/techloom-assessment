import asyncio
import logging
from app.database import AsyncSessionLocal
from app.services.order_service import cleanup_expired_orders
from app.config import settings

logger = logging.getLogger("background_cleanup")

class ExpirationCleanupWorker:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False

    async def _run_loop(self):
        logger.info(f"Starting Background Expiration Worker (interval: {settings.CLEANUP_INTERVAL_SECONDS}s)")
        while self._running:
            try:
                async with AsyncSessionLocal() as db:
                    count = await cleanup_expired_orders(db)
                    if count > 0:
                        logger.info(f"[Background Cleanup] Released inventory for {count} expired order(s).")
            except Exception as e:
                logger.error(f"[Background Cleanup] Error during cleanup execution: {e}")
            
            await asyncio.sleep(settings.CLEANUP_INTERVAL_SECONDS)

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self):
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("Background Expiration Worker stopped.")

cleanup_worker = ExpirationCleanupWorker()
