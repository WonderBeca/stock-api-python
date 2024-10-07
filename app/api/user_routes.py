# app/api/user_routes.py

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.models.user_model import User
from app.utils.auth_utils import create_access_token
from passlib.context import CryptContext
from sqlalchemy.future import select
from starlette.status import HTTP_302_FOUND

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# Criptografia de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "title": "Home Page"})


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Verifica se o nome de usuário já está cadastrado
    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalars().first()
    if existing_user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Username already registered!"})

    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return RedirectResponse("/login", status_code=HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password."})

    # Gera o token de acesso
    access_token = create_access_token(data={"sub": user.username})

    return templates.TemplateResponse("welcome.html", {"request": request, "token": access_token})

@router.get("/stock", response_class=HTMLResponse)
async def stock_form(request: Request):
    return templates.TemplateResponse("stock_search.html", {"request": request})
