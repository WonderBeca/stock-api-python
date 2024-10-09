import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.user_routes import router
from app.models.user_model import User
from app.utils.auth_utils import create_access_token
from fastapi import HTTPException
from sqlalchemy.future import select


@pytest.fixture
def client():
    with TestClient(router) as c:
        yield c


@pytest.fixture
async def test_user(db: AsyncSession, username="testuser", password="hashed_password"):
    existing_user = await db.execute(select(User).filter_by(username=username))
    user = existing_user.scalar_one_or_none()

    if user is None:
        new_user = User(username=username, hashed_password=password)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        yield new_user
        await db.delete(new_user)
        await db.commit()
    else:
        yield user


@pytest.mark.asyncio
async def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Hey!" in response.text


@pytest.mark.asyncio
async def test_register_form(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert "Register" in response.text


@pytest.mark.asyncio
async def test_login_form(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "Login" in response.text


@pytest.mark.asyncio
async def test_welcome(client, test_user):
    access_token = create_access_token(data={"sub": test_user.username})
    with pytest.raises(HTTPException) as exc_info:
        client.get("/welcome", cookies={"access_token": access_token})
    assert exc_info.value.detail == "Redirecting to login page"


@pytest.mark.asyncio
async def test_welcome_without_auth(client):
    headers = {"content-type": "application/json"}

    with pytest.raises(HTTPException) as exc_info:
        await client.get("/welcome", headers=headers)

    # Verifique o código de status e a mensagem de erro
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


@pytest.mark.asyncio
@patch('app.api.user_routes.get_user_by_username')
@patch('app.api.user_routes.verify_password')
@patch('app.api.user_routes.create_access_token')
async def test_login_success(mock_create_token, mock_verify_pass, mock_get_user, client, test_user):
    mock_get_user.return_value = test_user
    mock_verify_pass.return_value = True
    mock_create_token.return_value = "mocked_access_token"
    login_data = {
        "username": "testuser",
        "password": "hashed_password"
    }

    response = client.post("/login", json=login_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["access_token"] == "mocked_access_token"


@pytest.mark.asyncio
@patch('app.api.user_routes.get_user_by_username')
@patch('app.api.user_routes.verify_password')
@patch('app.api.user_routes.create_access_token')
async def test_login_fail(mock_create_token, mock_verify_pass, mock_get_user, client, test_user):
    mock_get_user.return_value = test_user
    mock_verify_pass.return_value = False
    login_data = {
        "username": "wrong_user",
        "password": "wrong_pass"
    }

    response = client.post("/login", json=login_data)

    assert response.status_code == 400
    assert "access_token" not in response.json()
