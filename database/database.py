from config.settings import DATABASE_URL, HELIUS_API_KEY

from sqlalchemy import create_engine, Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from datetime import datetime, UTC
from typing import AsyncGenerator
import base58

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    username = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    language = Column(String, default='en')
    joined_date = Column(DateTime, default=datetime.now(UTC))
    is_active = Column(Boolean, default=True)

class SmartWalletHolding(Base):
    __tablename__ = "smart_wallet_holding"

    # Remove trailing commas that caused tuple warnings
    token_id = Column(Integer, ForeignKey('tokens.id'), primary_key=True)
    wallet_id = Column(Integer, ForeignKey('smart_wallets.id'), primary_key=True)
    amount = Column(Float)
    buy_price = Column(Float)
    buy_timestamp = Column(DateTime, default=datetime.now(UTC))
    sell_price = Column(Float, nullable=True)
    sell_timestamp = Column(DateTime, nullable=True)

    # Add relationships
    token = relationship("Token", back_populates="holdings")
    wallet = relationship("SmartWallet", back_populates="holdings")

    # Add index for faster queries
    __table_args__ = (
        Index('idx_wallet_token', wallet_id, token_id),
    )


class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ca = Column(String, unique=True)
    symbol = Column(String, nullable=True)  # Ensure nullable=True exists
    holders = Column(Integer)
    bc_owners_percent = Column(Float)
    insiders_percent = Column(Float)
    avg_profit_percent = Column(Float)
    fresh_wallets = Column(Integer)
    sold_wallets = Column(Integer)
    suspicious_wallets = Column(Integer)
    insiders_wallets = Column(Integer)
    phishing_wallets = Column(Integer)
    profitable_wallets = Column(Integer)
    same_address_funded = Column(Integer)
    twitter = Column(String, nullable=True)
    github = Column(String, nullable=True)
    telegram = Column(String, nullable=True)
    website = Column(String, nullable=True)
    created_date = Column(DateTime(timezone=False), default=datetime.utcnow)  # Change to naive datetime
    is_active = Column(Boolean, default=True)
    # Update relationships
    holdings = relationship("SmartWalletHolding", back_populates="token")
    wallets = relationship(
        "SmartWallet", 
        secondary="smart_wallet_holding", 
        back_populates="tokens",
        viewonly=True,
        overlaps="holdings,token"
    )

class WalletHoldingHistory(Base):
    __tablename__ = "wallet_holding_history"
    
    id = Column(Integer, primary_key=True)
    wallet_address = Column(
        String, 
        ForeignKey('smart_wallets.address'),  # Add this foreign key
        index=True
    )
    token_mint = Column(String, index=True)  # Store token CA directly
    first_seen = Column(DateTime(timezone=True), default=datetime.now(UTC))
    last_seen = Column(DateTime(timezone=True), default=datetime.now(UTC))

    wallet = relationship(
        "SmartWallet", 
        back_populates="holding_history",
        foreign_keys=[wallet_address]  # Add this relationship
    )

class SmartWallet(Base):
    __tablename__ = "smart_wallets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String, unique=True)
    name = Column(String, nullable=True, unique=True)
    first_seen = Column(DateTime, default=datetime.now(UTC))
    last_active = Column(DateTime, default=datetime.now(UTC))
    profit_rate = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    
    # Fix relationships
    holdings = relationship("SmartWalletHolding", back_populates="wallet")
    tokens = relationship(
        "Token", 
        secondary="smart_wallet_holding", 
        back_populates="wallets",
        viewonly=True,
        overlaps="holdings,wallet"
    )
    holding_history = relationship(
        "WalletHoldingHistory",
        back_populates="wallet",  # Change backref to back_populates
        foreign_keys="WalletHoldingHistory.wallet_address",  # Add explicit foreign key
        cascade="all, delete-orphan"
    )

    @classmethod
    async def is_valid_address(cls, address: str) -> bool:
        """Validate Solana wallet using format checks + Helius API"""
        # First perform basic format validation
        if len(address) != 44:
            return False
            
        valid_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        if not all(c in valid_chars for c in address):
            return False
            
        try:
            decoded = base58.b58decode(address)
            if len(decoded) != 32:
                return False
        except Exception:
            return False

        return True


engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    .replace("?sslmode=", "?ssl=")  # Convert sslmode param to asyncpg's format
    .replace("&sslmode=", "&ssl="),  # Handle cases where it's not first param
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800
)

async def init_db():
    async with engine.begin() as conn:
        # Drop all tables first (only for development!)
        await conn.run_sync(Base.metadata.drop_all)
        # Create fresh tables with latest schema
        await conn.run_sync(Base.metadata.create_all)

from sqlalchemy.ext.asyncio import async_sessionmaker

AsyncSessionFactory = async_sessionmaker(
    engine, 
    class_=AsyncSession,
    expire_on_commit=False
)
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionFactory() as session:
        yield session
