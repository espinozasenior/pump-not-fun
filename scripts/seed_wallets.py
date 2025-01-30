#!/usr/bin/env python3
import asyncio
from database.database import SmartWallet, AsyncSession, engine
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, UTC

WALLETS = [
    {
        "address": "0x",
        "name": "Wallet 1"
    },
]

async def seed_smart_wallets():
    async with AsyncSession() as session:
        for wallet_data in WALLETS:
            try:
                stmt = insert(SmartWallet).values(
                    address=wallet_data['address'],
                    name=wallet_data['name'],
                    first_seen=datetime.utcnow(),
                    last_active=datetime.utcnow(),
                    profit_rate=0.0,
                    total_trades=0

                ).on_conflict_do_update(
                    index_elements=['address'],
                    set_=dict(
                        name=wallet_data['name'],
                        first_seen=datetime.utcnow(),
                        last_active=datetime.utcnow(),
                        profit_rate=0.0,
                        total_trades=0
                    )
                )
                
                await session.execute(stmt)
                await session.commit()
                print(f"Successfully seeded {wallet_data['name']}")
            except Exception as e:
                print(f"Error seeding {wallet_data['name']}: {str(e)}")
                await session.rollback()

if __name__ == "__main__":
    asyncio.run(seed_smart_wallets())
