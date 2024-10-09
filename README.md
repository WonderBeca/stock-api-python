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
