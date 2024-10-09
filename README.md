# Stock API Python

**Stock API Python** is a Python library designed to simplify interactions with stock market APIs. With this library, you can effortlessly collect and analyze financial data such as stock prices, market capitalization, and competitor information, providing an efficient way to monitor market performance.

## Features

- **Data Collection**: Access real-time stock data, including prices, market capitalization, and more.
- **Competitor Analysis**: Compare the performance of different companies with detailed reports.
- **Historical Data**: Retrieve information on stock performance over time.
- **Flexible Configuration**: Utilize proxies and login options for a personalized experience.

## Docker Setup

### Prerequisites

Make sure you have Docker and Docker Compose installed on your machine. You can download and install them from [Docker&#39;s official website](https://www.docker.com/get-started).

### Running with Docker Compose

1. **Clone the Repository**:
   First, clone the repository to your local machine:

   ```bash
   git clone https://github.com/WonderBeca/stock-api-python.git
   cd stock-api-python
   ```
2. **Create a .env File**

   The application requires specific environment variables for configuration and proper functionality. Create a `.env` file in the root directory of your project and populate it with the following variables:

   ### Required Environment Variables


   ```python
   Required Environment Variables
   Database Configuration:
   DATABASE_URL: The connection string for the PostgreSQL database.
   POSTGRES_DB: The name of the PostgreSQL database.
   POSTGRES_USER: The PostgreSQL database username.
   POSTGRES_PASSWORD: The password for the PostgreSQL database user.
   MarketWatch API Credentials:
   MARKETWATCH_USER: Your email address associated with the MarketWatch account.
   MARKETWATCH_PWD: Your password for the MarketWatch account.
   MARKETWATCH_ID: The client ID for MarketWatch API access (default value provided if not set).
   Application Configuration:
   LAST_UPDATE: The last update interval (in minutes).
   ACCESS_TOKEN_EXPIRE_MINUTES: Duration (in minutes) for which the access token remains valid.
   CACHE_EXPIRATION_TIME: Cache expiration duration (in minutes).
   ALGORITHM: The algorithm used for encoding the JWT (default: HS256).

   ```
3. **Inside the repository folder, run docker-compose with:**

   ```
   docker-compose up --build
   ```

   After that you application will run on http://localhost:8000/

# Stock API

### Overview

The Stock API provides endpoints for user registration, authentication, and stock management. It allows users to register, log in, view their stock purchases, and manage their stocks. I made a whole front end but since the test specifies some endpoints requirements i addapted so the endpoints work either on front  and backend directly.

### Endpoints

#### Home

- **GET /**
  Render the home page.

  **Responses:**

  - `200`: Successful response.
  - `204`: No content.

---

#### User Registration

- **GET /register**Render the registration form.

  **Responses:**

  - `200`: Successful response with registration form.
- **POST /register**
  Register a new user.

  **Request Body:**

  - **Form Data:**
    - `username`: string
    - `password`: string
  - **JSON:**
    ```json
    {
      "username": "string",
      "password": "string"
    }
    ```

  **Responses:**

  - `201`: User registered successfully.
  - `400`: Username already registered.

---

#### User Login

- **GET /login**Render the login form.

  **Responses:**

  - `200`: Successful response with login form.
- **POST /login**
  Authenticate a user and log them in.

  **Request Body:**

  - **Form Data:**
    - `username`: string
    - `password`: string
  - **JSON:**
    ```json
    {
      "username": "string",
      "password": "string"
    }
    ```

  **Responses:**

  - `200`: Successful login.
  - `400`: Invalid username or password.

---

#### User Dashboard

- **GET /welcome**
  Render the user's stock purchase history and wallet information.

  **Responses:**

  - `200`: Successful response with user's stock information.

---

#### Stock Management

- **GET /stocks**Get all stocks.

  **Responses:**

  - `200`: Successful retrieval of all stocks.
  - `204`: No stocks found.
- **GET /stocks/{user_id}**Get stocks by user ID.

  **Parameters:**

  - `user_id`: integer (required) - The ID of the user to retrieve stocks for.

  **Responses:**

  - `200`: Successful retrieval of stocks for user.
  - `404`: User not found.
- **GET /stock/{stock_symbol}**Retrieve stock information by symbol.

  **Parameters:**

  - `stock_symbol`: string (required) - The stock symbol to query.
  - `date`: string (optional) - The date for stock data.

  **Responses:**

  - `200`: Successful retrieval of stock information.
  - `400`: Stock not found.
  - `302`: Redirect to welcome page with error message.
- **POST /stock/{stock_symbol}**Buy stock.

  **Parameters:**

  - `stock_symbol`: string (required) - The stock symbol to purchase.

  **Request Body:**

  - **Form Data:**
    - `amount`: integer
    - `stock_symbol`: string
  - **JSON:**
    ```json
    {
      "amount": integer
    }
    ```

  **Responses:**

  - `200`: Stock purchase successful.
  - `400`: Amount not provided or stock not found.
  - `302`: Redirect to welcome page with error message.
- **POST /stock/{stock_symbol}/update**
  Update stock amount.

  **Parameters:**

  - `stock_symbol`: string (required) - The stock symbol to update.

  **Request Body:**

  - **Form Data:**
    - `amount`: integer
    - `current_amount`: integer

  **Responses:**

  - `200`: Stock updated successfully.
  - `302`: Redirect to welcome page with error message.

---

### Contributing

Feel free to contribute to the project by submitting a pull request or opening an issue for any enhancements or bugs.

### License

This project is licensed under the MIT License.
