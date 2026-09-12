import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Order, Product
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("background_worker")

async def expire_unpaid_orders():
    """
    Background worker running periodically (every 30s by default) to automatically
    release reserved stock and mark orders as 'EXPIRED' if unpaid after reservation window (5 minutes).
    """
    logger.info(f"Starting background order cleanup worker (interval: {settings.BACKGROUND_CLEANUP_INTERVAL_SECONDS}s)...")
    while True:
        try:
            await asyncio.sleep(settings.BACKGROUND_CLEANUP_INTERVAL_SECONDS)
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    now = datetime.now(timezone.utc)
                    stmt = (
                        select(Order)
                        .where(
                            Order.status == "RESERVED",
                            Order.reservation_expires_at <= now
                        )
                        .with_for_update()
                    )
                    result = await session.execute(stmt)
                    expired_orders = result.scalars().all()

                    if expired_orders:
                        logger.info(f"Found {len(expired_orders)} expired unpaid order(s) to process.")

                    for order in expired_orders:
                        logger.info(f"Expiring Order #{order.id} (expired at {order.reservation_expires_at}). Restoring stock...")
                        order.status = "EXPIRED"

                        for item in order.items:
                            prod_stmt = select(Product).where(Product.id == item.product_id).with_for_update()
                            prod_res = await session.execute(prod_stmt)
                            product = prod_res.scalar_one_or_none()
                            if product:
                                product.stock_quantity += item.quantity
                                product.reserved_quantity = max(0, product.reserved_quantity - item.quantity)
                                logger.info(
                                    f"Restored {item.quantity} units of '{product.name}' (Product #{product.id}). "
                                    f"New stock: {product.stock_quantity}, reserved: {product.reserved_quantity}"
                                )
        except asyncio.CancelledError:
            logger.info("Background cleanup worker stopped.")
            break
        except Exception as e:
            logger.error(f"Error during background order cleanup cycle: {e}")
