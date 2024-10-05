# stock-api-python

A REST API built with Python that retrieves stock data from Polygon.io and scrapes performance data from MarketWatch. Features include fetching stock details, updating purchased amounts, caching, and storing data in PostgreSQL. Includes Docker support, logging, and unit tests for reliability.

create venv python3.10

install requirements

create .env file

DATABASE_URL
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

run docker file

docker-compose up -d

docker-compose exec web bash

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
