from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_302_FOUND
from passlib.context import CryptContext
from app.database.database import get_db
from app.utils.auth_utils import (
    create_access_token, requires_authentication, verify_password)
from app.services.stock_service import (
    get_stocks_history_by_user, get_stocks_total_by_user
)
from app.services.user_service import get_user_by_username, create_user

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the home page.

    Args:
        request (Request): The HTTP request object.

    Returns:
        HTMLResponse: The rendered home page.
    """
    if request.headers.get("content-type") == "application/json":
        return JSONResponse({"message": "Hey!"})
    return templates.TemplateResponse("home.html", {"request": request, "title": "Hey!"})


@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    """
    Render the registration form.

    Args:
        request (Request): The HTTP request object.

    Returns:
        HTMLResponse: The rendered registration form.
    """
    if request.headers.get("content-type") == "application/json":
        return JSONResponse({"message": "Register form displayed"})
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
async def register(
    request: Request,
    username: str = None,
    password: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.

    Args:
        request (Request): The HTTP request object.
        username (str): The username for the new user.
        password (str): The password for the new user.
        db (AsyncSession): The database session.

    Returns:
        HTMLResponse or JSONResponse: Response indicating success or error.
    """
    if request.headers.get("content-type") == "application/json":
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
    elif username is None or password is None:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")

    existing_user = await get_user_by_username(db, username)

    if existing_user:
        error_msg = "Username already registered!"
        if request.headers.get("content-type") == "application/json":
            return JSONResponse({"error": error_msg}, status_code=400)
        return templates.TemplateResponse("register.html", {"request": request, "error": error_msg})

    await create_user(db=db, username=username, password=password)

    if request.headers.get("content-type") == "application/json":
        return JSONResponse({"message": "User registered successfully"}, status_code=201)

    return RedirectResponse("/login", status_code=HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """
    Render the login form.

    Args:
        request (Request): The HTTP request object.

    Returns:
        HTMLResponse: The rendered login form.
    """
    if request.headers.get("content-type") == "application/json":
        return JSONResponse({"message": "Login form displayed"})
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = None,
    password: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate a user and log them in.

    Args:
        request (Request): The HTTP request object.
        username (str): The username provided by the user.
        password (str): The password provided by the user.
        db (AsyncSession): The database session.

    Returns:
        HTMLResponse or JSONResponse: Response indicating success or error.
    """
    if request.headers.get("content-type") == "application/json":
        body = await request.json()
        username = body.get("username")
        password = str(body.get("password"))
    elif username is None or password is None:
        form_data = await request.form()
        username = form_data.get("username")
        password = str(form_data.get("password"))

    if not username or not password:
        error_msg = "Username and password are required."
        if request.headers.get("content-type") == "application/json":
            return JSONResponse({"error": error_msg}, status_code=400)
        return templates.TemplateResponse("login.html", {"request": request, "error": error_msg})

    user = await get_user_by_username(db, username)

    if not user or not verify_password(password, user.hashed_password):
        error_msg = "Invalid username or password."
        if request.headers.get("content-type") == "application/json":
            return JSONResponse({"error": error_msg}, status_code=400)
        return templates.TemplateResponse("login.html", {"request": request, "error": error_msg})

    access_token = create_access_token(data={"sub": user.username})
    response = RedirectResponse(url="/welcome", status_code=HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    if request.headers.get("content-type") == "application/json":
        return JSONResponse({"access_token": access_token}, status_code=200)
    return response


@router.get("/welcome", response_class=HTMLResponse)
async def stock_form(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Render the user's stock purchase history and wallet information.

    Args:
        request (Request): The HTTP request object.
        db (AsyncSession): The database session.

    Returns:
        HTMLResponse or JSONResponse: Rendered page or JSON response.
    """
    user = await requires_authentication(request, db)

    purchase_history = await get_stocks_history_by_user(db, user)
    total_stocks = await get_stocks_total_by_user(db, user)

    if request.headers.get("content-type") == "application/json":
        return JSONResponse({
            "purchased_stocks": purchase_history,
            "wallet": total_stocks
        })

    return templates.TemplateResponse("stock_search.html", {
        "request": request,
        "purchased_stocks": purchase_history,
        "wallet": total_stocks
    })
