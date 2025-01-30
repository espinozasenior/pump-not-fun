from sqlalchemy import select
from database.database import AsyncSession, User
from logger.logger import logger

from pyrogram.types import Message, CallbackQuery
from typing import Callable, Union
from functools import wraps

def get_user():
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(client, update: Union[Message, CallbackQuery], *args, **kwargs):
            async with AsyncSession() as session:
                try:
                    user_id = update.from_user.id
                    result = await session.execute(
                        select(User).where(User.user_id == user_id)
                    )
                    user = result.scalars().first()
                    
                    if not user:
                        user = User(
                            user_id=user_id,
                            username=update.from_user.username,
                            first_name=update.from_user.first_name,
                            last_name=update.from_user.last_name
                        )
                        session.add(user)
                        await session.commit()
                        await session.refresh(user)
                    
                    return await func(client, update, user, session, *args, **kwargs)
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error in decorator: {e}")
                    raise
        return wrapper
    return decorator
