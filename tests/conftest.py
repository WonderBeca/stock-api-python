import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database.database import Base

@pytest.fixture(scope="session")
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Criação das tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Retorno da sessão
    async with async_session() as session:
        yield session  # Retorna a sessão para os testes

        # Limpeza do banco de dados após os testes
        await session.close()
        await engine.dispose()
