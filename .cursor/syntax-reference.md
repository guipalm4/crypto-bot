# Referência Rápida de Sintaxe - Crypto Trading Bot

## Pydantic v2 (pydantic-settings)

### ✅ Sintaxe Correta
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Campos com alias para variáveis de ambiente
    database_url: str = Field(
        default="postgresql://user:pass@localhost/db",
        alias="DATABASE_URL"
    )
    
    debug: bool = Field(default=False, alias="DEBUG")
```

### ❌ Sintaxe Obsoleta (Pydantic v1)
```python
from pydantic import BaseSettings, Field  # ❌ BaseSettings não está mais em pydantic

class Settings(BaseSettings):
    class Config:  # ❌ Use SettingsConfigDict
        env_file = ".env"
    
    database_url: str = Field(env="DATABASE_URL")  # ❌ Use alias
```

## SQLAlchemy v2

### ✅ Sintaxe Correta
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
```

### ❌ Sintaxe Obsoleta (SQLAlchemy v1)
```python
from sqlalchemy.ext.declarative import declarative_base  # ❌ Use DeclarativeBase
from sqlalchemy import Column, Integer, String

Base = declarative_base()  # ❌ Use class Base(DeclarativeBase)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)  # ❌ Use Mapped[int] = mapped_column
    name = Column(String(50))
```

## CCXT v4

### ✅ Sintaxe Correta
```python
import ccxt

# Inicialização assíncrona
exchange = ccxt.binance({
    'apiKey': 'your-api-key',
    'secret': 'your-secret',
    'sandbox': True,
    'enableRateLimit': True,
})

# Uso assíncrono
async def fetch_ticker(symbol):
    ticker = await exchange.fetch_ticker(symbol)
    return ticker
```

## Click v8

### ✅ Sintaxe Correta
```python
import click
from rich.console import Console

console = Console()

@click.group()
def cli():
    """Crypto Trading Bot CLI"""
    pass

@cli.command()
@click.option('--symbol', default='BTC/USDT', help='Trading pair')
def buy(symbol: str) -> None:
    """Buy command"""
    console.print(f"Buying {symbol}")
```

## AsyncIO (Python 3.12+)

### ✅ Padrões Corretos
```python
import asyncio
from typing import AsyncGenerator

async def fetch_data() -> dict:
    """Fetch data asynchronously"""
    await asyncio.sleep(1)
    return {"data": "value"}

async def process_items(items: list) -> AsyncGenerator[dict, None]:
    """Process items asynchronously"""
    for item in items:
        result = await process_item(item)
        yield result

# Uso correto
async def main():
    data = await fetch_data()
    async for result in process_items([1, 2, 3]):
        print(result)
```

## Rich v13

### ✅ Sintaxe Correta
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Tabela
table = Table(show_header=True, header_style="bold magenta")
table.add_column("Name", style="dim", width=20)
table.add_column("Value")

# Painel
panel = Panel(
    "Content here",
    title="Title",
    border_style="green"
)

console.print(panel)
console.print(table)
```

## Pytest v7

### ✅ Sintaxe Correta
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
async def mock_exchange():
    """Mock exchange for testing"""
    exchange = AsyncMock()
    exchange.fetch_ticker.return_value = {"symbol": "BTC/USDT", "price": 50000}
    return exchange

@pytest.mark.asyncio
async def test_fetch_ticker(mock_exchange):
    """Test fetch ticker functionality"""
    result = await mock_exchange.fetch_ticker("BTC/USDT")
    assert result["symbol"] == "BTC/USDT"
```

## Comandos Úteis

### Validar Sintaxe
```bash
python scripts/validate-syntax.py
```

### Verificar Imports
```bash
python -c "import pydantic_settings; print('Pydantic Settings OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import ccxt; print('CCXT OK')"
```

### Testar Configuração
```bash
python -m src.crypto_bot --help
python -m pytest tests/ -v
```
