from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.user_model import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user_by_username(db: AsyncSession, username: str):
    """
    Retrieve a user from the database by their username.

    Args:
        db (AsyncSession): The database session for making queries.
        username (str): The username of the user to retrieve.

    Returns:
        User or None: The user object if found, otherwise None.
    """
    result = await db.execute(select(User).filter(User.username == username))
    return result.scalars().first()


async def create_user(db: AsyncSession, username: str, password: str):
    """
    Create a new user in the database with the specified username and password.

    Args:
        db (AsyncSession): The database session for making changes.
        username (str): The username for the new user.
        password (str): The password for the new user.

    Returns:
        User: The created user object with a hashed password.
    """
    hashed_password = pwd_context.hash(password)
    db_user = User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
