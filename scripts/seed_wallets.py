#!/usr/bin/env python3
import asyncio                                                                         
from database.database import SmartWallet, AsyncSessionFactory, init_db, engine        
from sqlalchemy.dialects.postgresql import insert                                      
from datetime import datetime
from config.settings import WALLETS

async def seed_smart_wallets():
    await init_db()
    
    async with AsyncSessionFactory() as session:
        try:
            valid_count = 0
            invalid_count = 0
            
            for wallet_data in WALLETS:
                address = wallet_data['address']
                
                # Add await since validation is now async
                if not await SmartWallet.is_valid_address(address):
                    print(f"❌ Invalid address: {address}")
                    invalid_count += 1
                    continue
                    
                stmt = insert(SmartWallet).values(
                    address=address,
                    name=wallet_data['name'],
                    first_seen=datetime.utcnow(),
                    last_active=datetime.utcnow(),
                    profit_rate=0.0,
                    total_trades=0
                ).on_conflict_do_update(
                    index_elements=['address'],
                    set_=dict(
                        name=wallet_data['name'],
                        last_active=datetime.utcnow()
                    )
                )
                await session.execute(stmt)
                valid_count += 1
                                
            await session.commit()
            print(f"✅ Seeding complete: {valid_count} valid wallets added/updated")
            if invalid_count > 0:
                print(f"⚠️  Skipped {invalid_count} invalid addresses")
            
        except Exception as e:
            print(f"🚨 Error seeding wallets: {str(e)}")
            await session.rollback()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_smart_wallets())
