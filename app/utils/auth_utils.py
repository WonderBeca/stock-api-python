import os
from datetime import datetime, timedelta
from typing import Optional

import logging
from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.services.user_service import get_user_by_username

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create an access token with an expiration time.

    Args:
        data (dict): A dictionary containing the data to encode in the token.
        expires_delta (Optional[timedelta], optional): A timedelta indicating the token's expiration time.
            If not provided, a default expiration time will be used.

    Returns:
        str: The encoded JWT as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_access_token(token: str, db: AsyncSession):
    """
    Verifies the provided JWT access token and retrieves the associated user from the database.

    Args:
        token (str): The JWT access token to verify.
        db (AsyncSession): The database session to use for querying the user.

    Returns:
        User or None: The User object associated with the token if verification is successful,
                       or None if the token is invalid or the user is not found.

    Raises:
        HTTPException: If the token is expired, an HTTPException is raised with a 302 status code,
                       redirecting the user to the login page.

    Logs:
        - Decodes the JWT token and logs any errors encountered during verification.
        - Logs the result of the token verification, including the user found or errors.
    """
    user = None
    try:
        logging.debug("Decoding the token: %s", token)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        if username is None:
            logging.error("Username not found in the token payload.")
        else:
            user = await get_user_by_username(db, username)
            if user is None:
                logging.error("User not found in the database.")

    except ExpiredSignatureError:
        logging.error("JWT token has expired.")
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            detail="Token expired, redirecting to login page",
            headers={"Location": "/login"}
        )
    except JWTError as jwt_error:
        logging.error("Error decoding the JWT token: %s", jwt_error)
    except Exception as err:
        logging.error("Unexpected error: %s", err)
    finally:
        logging.debug("Result of token verification: %s", user)
        return user


async def requires_authentication(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Checks if the user is authenticated.

    Args:
        request (Request): The HTTP request object.
        db (AsyncSession): The database session.

    Returns:
        int: ID of the authenticated user.

    Raises:
        HTTPException: If the user is not authenticated, returns a 401 error or redirects to the login page.
    """
    token = request.headers.get("Authorization")
    if token is None:
        token = request.cookies.get("access_token")

    if token is None:
        # Redirect to the login page for frontend requests
        if "application/json" not in request.headers.get("content-type", ""):
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail="Redirecting to login page",  # Optional detail message
                headers={"Location": "/"}
            )
        # Return a 401 error for API requests
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Remove the "Bearer " prefix from the token if present
    if token.startswith("Bearer "):
        token = token[7:]

    user = await verify_access_token(token, db)

    if user is None:
        # Redirect to the login page for frontend requests
        if "application/json" not in request.headers.get("content-type", ""):
            raise HTTPException(
                status_code=status.HTTP_302_FOUND,
                detail="Redirecting to login page",  # Optional detail message
                headers={"Location": "/login"}
            )
        # Return a 401 error for API requests
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    return user.id  # Return the authenticated user's ID


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if a plain password matches a hashed password.

    Args:
        plain_password (str): The plain password to be checked.
        hashed_password (str): The hashed password to compare with.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash the provided password.

    Args:
        password (str): The password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)
