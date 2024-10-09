from fastapi import APIRouter, Depends, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from starlette.status import (
    HTTP_302_FOUND, HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_203_NON_AUTHORITATIVE_INFORMATION
)

from app.database.database import get_db
from app.services.stock_service import (
    get_stock_by_symbol, create_stock, purchase_stock, update_stock_amount,
    get_stocks_history_by_user, get_stocks_total_by_user, stock_dict, get_marketwatch_data
)
from app.utils.auth_utils import requires_authentication
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_valid_amount(amount) -> bool:
    """Check if the amount is valid and can be converted to an integer."""
    if isinstance(amount, int):
        return amount > 0
    if isinstance(amount, str):
        return amount.isdigit() and int(amount) > 0
    return False


async def redirect_with_message(url: str, message: str, status_code=HTTP_302_FOUND) -> RedirectResponse:
    """
    Redirects to a specified URL with a message set in a cookie.

    This function creates a redirect response to a given URL and sets a cookie containing
    a warning message to inform the user about the reason for the redirection.

    Args:
        url (str): The URL to redirect to.
        message (str): The message to be stored in a cookie for user notification.
        status_code (int, optional): The HTTP status code for the redirect. Defaults to 302 (Found).

    Returns:
        RedirectResponse: The redirect response object that includes the URL and the cookie.
    """
    redirect = RedirectResponse(url=url, status_code=status_code)
    redirect.set_cookie(key="warning_message", value=message)
    return redirect


async def check_stock_exists(stock_symbol: str, db: AsyncSession):
    """
    Checks if a stock exists in the database by its symbol.

    This function queries the database for a stock using the provided symbol.
    If the stock does not exist, it returns a message prompting the user
    to check the current stock price before proceeding with any buy/sell actions.

    Args:
        stock_symbol (str): The stock symbol to check.
        db (AsyncSession): The database session for asynchronous operations.

    Returns:
        tuple: A tuple containing:
            - stock: The stock object if it exists, or None if it does not.
            - error_message: An error message string if the stock does not exist, or None if it does.
    """
    stock = await get_stock_by_symbol(db, stock_symbol)
    if not stock:
        msg = (
            'You are about to make a buy/sell action and have not checked the '
            'current stock price; please check before proceeding.'
        )
        return None, msg
    return stock, None


@router.get("/stock/{stock_symbol}", response_class=HTMLResponse)
@router.get("/stock", response_class=HTMLResponse)
async def query_stock(
        request: Request,
        stock_symbol: str = None,
        date: str = Query(None),
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(requires_authentication),
) -> HTMLResponse:
    """
    Retrieves stock information by its symbol. If the stock is not found in the database,
    it attempts to fetch data from MarketWatch and create a new stock entry.

    Args:
        request (Request): The FastAPI request object.
        stock_symbol (str, optional): The stock symbol to query.
            If not provided, it is extracted from query parameters.
        date (str, optional): The date for stock data. Defaults to None.
        db (AsyncSession): The database session for async operations.
        user_id (int): The ID of the authenticated user.

    Returns:
        HTMLResponse: The rendered HTML template with stock data if found,
        or a redirect to the welcome page with an error message if the stock is not found.

    Raises:
        HTTPException: If the stock data cannot be retrieved or created,
        an appropriate HTTP response is returned based on the content type of the request.
    """
    if stock_symbol is None:
        stock_symbol = request.query_params.get("stock_symbol")

    stock = await get_stock_by_symbol(db, stock_symbol)

    if not stock:
        marketwatch_data = await get_marketwatch_data(stock_symbol, date)
        if not marketwatch_data:
            msg = "Stock not found"
            if request.headers.get("content-type") == "application/json":
                return JSONResponse({"message": msg}, status_code=HTTP_400_BAD_REQUEST)
            return await redirect_with_message("/welcome", msg, status_code=HTTP_302_FOUND)
        stock = await create_stock(db, marketwatch_data.get('data'))

    if request.headers.get("content-type") == "application/json":
        return JSONResponse(stock_dict(stock), status_code=HTTP_200_OK)

    wallet = await get_stocks_total_by_user(db, user_id)
    purchased_stocks = await get_stocks_history_by_user(db, user_id)

    return templates.TemplateResponse("stock_search.html", {
        "request": request,
        "stock": stock_dict(stock),
        "wallet": wallet,
        "purchased_stocks": purchased_stocks
    })


@router.post("/stock/{stock_symbol}/update", response_class=HTMLResponse)
async def update_stock(
    request: Request,
    stock_symbol: str = None,
    amount: int = Form(None),
    current_amount: int = Form(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(requires_authentication),
) -> RedirectResponse:
    """
    Updates the amount of a specified stock for the authenticated user.

    This endpoint allows the user to update the quantity of a stock they own. It verifies
    whether the stock exists for the given symbol and checks for any errors during the
    update process.

    Args:
        request (Request): The FastAPI request object.
        stock_symbol (str): The stock symbol to update.
        amount (int): The new amount of the stock to be set.
        current_amount (int): The current amount of the stock before the update.
        db (AsyncSession): The database session for async operations.
        user_id (int): The ID of the authenticated user.

    Returns:
        RedirectResponse: A redirect response indicating the outcome of the update operation.
                          If the stock does not exist or if an error occurs, a message is
                          provided to the user.

    Raises:
        Exception: Any exception raised during the update process will result in a redirect
                   with the error message.
    """
    try:
        stock, msg = await check_stock_exists(stock_symbol, db)
        if not stock:
            return await redirect_with_message("/welcome", msg, status_code=HTTP_302_FOUND)

        await update_stock_amount(db, user_id, stock_symbol, amount, current_amount)
        return await redirect_with_message("/welcome", "Stock updated successfully!", status_code=HTTP_302_FOUND)

    except Exception as err:
        return await redirect_with_message("/welcome", str(err), status_code=HTTP_302_FOUND)


@router.post("/stock/{stock_symbol}", response_class=HTMLResponse)
@router.post("/stock", response_class=HTMLResponse)
async def buy_stock(
    request: Request,
    stock_symbol: str = None,
    amount: int = Form(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(requires_authentication),
) -> RedirectResponse:
    """
    Buys a specified amount of stock for the authenticated user, handling both form-data and JSON.

    This endpoint allows the user to purchase stocks either by submitting a form or
    sending a JSON request. The function checks if the specified stock exists and
    processes the purchase accordingly.

    Args:
        request (Request): The FastAPI request object.
        stock_symbol (str): The stock symbol to purchase. Can be provided in the URL path or form-data.
        amount (int): The stock amount from form-data (optional). If not provided, it must be present
        in the request body.
        db (AsyncSession): The database session for async operations.
        user_id (int): The ID of the authenticated user.

    Returns:
        RedirectResponse: A redirect response indicating success or failure of the purchase operation.
                          If the stock does not exist or the amount is not provided, an appropriate
                          error message is returned.

    Raises:
        HTTPException: Returns a 400 status code if the stock does not exist or if the amount is not provided.
    """
    if stock_symbol is None:
        form_data = await request.form()
        stock_symbol = form_data.get("stock_symbol")
        amount = form_data.get("amount")

    if request.headers.get("content-type") == "application/json":
        body = await request.json()
        amount = body.get('amount')

    stock, msg = await check_stock_exists(stock_symbol, db)

    if not stock:
        if request.headers.get("content-type") == "application/json":
            return JSONResponse({"message": msg}, status_code=HTTP_400_BAD_REQUEST)
        return await redirect_with_message("/welcome", msg, status_code=HTTP_302_FOUND)

    if not is_valid_amount(amount):
        msg = "Amount not provided or not greater than 0"
        if request.headers.get("content-type") == "application/json":
            return JSONResponse({"message": msg}, status_code=HTTP_400_BAD_REQUEST)
        return await redirect_with_message("/welcome", msg, status_code=HTTP_302_FOUND)

    await purchase_stock(db, user_id, stock_symbol, int(amount))

    if request.headers.get("content-type") == "application/json":
        return JSONResponse(
            f'{amount} units of stock {stock_symbol} were added to your stock record',
            status_code=HTTP_203_NON_AUTHORITATIVE_INFORMATION
        )
    return await redirect_with_message("/welcome", "Purchase successful!", status_code=HTTP_302_FOUND)
