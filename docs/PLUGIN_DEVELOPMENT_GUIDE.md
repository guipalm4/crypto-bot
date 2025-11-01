# 🔌 Guia de Desenvolvimento de Plugins

Este guia completo explica como desenvolver, integrar e manter plugins para o Crypto Trading Bot. O sistema suporta três tipos de plugins: **Exchange Plugins**, **Indicator Plugins**, e **Strategy Plugins**.

## 📋 Índice

1. [Visão Geral da Arquitetura](#visão-geral-da-arquitetura)
2. [Exchange Plugins](#exchange-plugins)
3. [Indicator Plugins](#indicator-plugins)
4. [Strategy Plugins](#strategy-plugins)
5. [Processo de Registro](#processo-de-registro)
6. [Boas Práticas](#boas-práticas)
7. [Testes](#testes)
8. [Troubleshooting](#troubleshooting)

## 🏗️ Visão Geral da Arquitetura

O sistema de plugins utiliza três mecanismos principais:

### 1. Exchange Plugins
- **Registro**: Descoberta automática via sistema de arquivos
- **Base Class**: `ExchangeBase` (`src/crypto_bot/infrastructure/exchanges/base.py`)
- **Localização**: `src/crypto_bot/plugins/exchanges/`

### 2. Indicator Plugins
- **Registro**: Descoberta automática via sistema de arquivos
- **Base Class**: `BaseIndicator` (`src/crypto_bot/plugins/indicators/base.py`)
- **Protocol**: `Indicator` (Protocol checking)
- **Localização**: `src/crypto_bot/plugins/indicators/`

### 3. Strategy Plugins
- **Registro**: Via Python Entry Points (`pyproject.toml`)
- **Base Class**: `Strategy` (`src/crypto_bot/plugins/strategies/base.py`)
- **Entry Point Group**: `crypto_bot.strategies`
- **Localização**: Pode estar em pacotes externos

## 🏦 Exchange Plugins

### Interface Base

Todos os exchange plugins devem herdar de `ExchangeBase` e implementar os métodos abstratos:

```python
from crypto_bot.infrastructure.exchanges.base import ExchangeBase

class MyExchangePlugin(ExchangeBase):
    """Plugin para uma nova exchange."""
    
    # Atributos obrigatórios (class attributes)
    name = "my_exchange"
    id = "myexchange"
    countries = ["US", "EU"]
    urls = {
        "api": {
            "public": "https://api.myexchange.com",
            "private": "https://api.myexchange.com",
        }
    }
    version = "1.0.0"
    
    @property
    async def fetch_markets(self) -> Dict[str, Any]:
        """Buscar mercados disponíveis."""
        pass
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Buscar ticker de um símbolo."""
        pass
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> List[List[float]]:
        """Buscar dados OHLCV."""
        pass
    
    async def fetch_balance(self) -> Dict[str, BalanceDTO]:
        """Buscar saldo da conta."""
        pass
    
    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """Criar uma ordem."""
        pass
    
    async def cancel_order(self, order_id: str, symbol: str) -> OrderDTO:
        """Cancelar uma ordem."""
        pass
    
    # Métodos obrigatórios do lifecycle
    async def initialize(self) -> None:
        """Inicializar conexão com a exchange."""
        pass
    
    async def load_markets(self) -> Dict[str, Any]:
        """Carregar lista de mercados."""
        pass
    
    async def close(self) -> None:
        """Fechar conexões e limpar recursos."""
        pass
```

### Implementação Completa - Exemplo

```python
"""
Plugin para nova exchange usando CCXT como base.

Para exchanges suportadas pelo CCXT, use CCXTExchangePlugin.
"""
from decimal import Decimal
from typing import Any, Dict, List

from crypto_bot.application.dtos.order import (
    BalanceDTO,
    CreateOrderRequest,
    OrderDTO,
    OrderSide,
    OrderStatus,
    OrderType,
)
from crypto_bot.infrastructure.exchanges.base import ExchangeBase
from crypto_bot.plugins.exchanges.config_models import ExchangeConfig

class MyExchangePlugin(ExchangeBase):
    """Plugin para MyExchange usando CCXT."""
    
    name = "my_exchange"
    id = "myexchange"
    countries = ["US"]
    urls = {
        "api": {
            "public": "https://api.myexchange.com",
            "private": "https://api.myexchange.com",
        }
    }
    version = "1.0.0"
    
    def __init__(self, config: ExchangeConfig) -> None:
        """Inicializar plugin com configuração."""
        super().__init__(
            api_key=config.api_key,
            secret=config.api_secret,
            sandbox=config.sandbox,
        )
        self.config = config
        self._markets: Dict[str, Any] = {}
    
    async def initialize(self) -> None:
        """Inicializar conexão."""
        # Configurar cliente HTTP, autenticação, etc.
        self._initialized = True
    
    async def load_markets(self) -> Dict[str, Any]:
        """Carregar mercados."""
        # Implementar carregamento de mercados
        return self._markets
    
    async def fetch_markets(self) -> Dict[str, Any]:
        """Buscar mercados."""
        if not self._markets:
            await self.load_markets()
        return self._markets
    
    async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """Buscar ticker."""
        # Implementar busca de ticker
        return {
            "symbol": symbol,
            "last": 50000.0,
            "bid": 49990.0,
            "ask": 50010.0,
            "volume": 1000.0,
        }
    
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100,
    ) -> List[List[float]]:
        """Buscar OHLCV."""
        # Retornar lista de candles: [timestamp, open, high, low, close, volume]
        return [
            [1640000000000, 50000.0, 51000.0, 49000.0, 50500.0, 1000.0],
            # ... mais candles
        ]
    
    async def fetch_balance(self) -> Dict[str, BalanceDTO]:
        """Buscar saldo."""
        return {
            "USDT": BalanceDTO(
                currency="USDT",
                free=Decimal("1000.0"),
                used=Decimal("0.0"),
                total=Decimal("1000.0"),
                exchange="my_exchange",
                timestamp=datetime.now(UTC),
            )
        }
    
    async def create_order(self, request: CreateOrderRequest) -> OrderDTO:
        """Criar ordem."""
        # Implementar criação de ordem
        return OrderDTO(
            id="order_123",
            exchange_order_id="ex_order_123",
            exchange="my_exchange",
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            status=OrderStatus.OPEN,
            quantity=request.quantity,
            filled_quantity=Decimal("0"),
            remaining_quantity=request.quantity,
            price=request.price,
            average_price=None,
            cost=Decimal("0"),
            fee=Decimal("0"),
            fee_currency="USDT",
            timestamp=datetime.now(UTC),
            last_trade_timestamp=None,
        )
    
    async def cancel_order(self, order_id: str, symbol: str) -> OrderDTO:
        """Cancelar ordem."""
        # Implementar cancelamento
        pass
    
    async def close(self) -> None:
        """Fechar conexões."""
        self._initialized = False
```

### Usando CCXT como Base

Para exchanges suportadas pelo CCXT, é recomendado usar `CCXTExchangePlugin`:

```python
from crypto_bot.plugins.exchanges.base_ccxt_plugin import CCXTExchangePlugin
from crypto_bot.plugins.exchanges.config_models import ExchangeConfig

class MyExchangeCCXTPlugin(CCXTExchangePlugin):
    """Plugin usando CCXT para MyExchange."""
    
    name = "my_exchange"
    id = "myexchange"
    
    def __init__(self, config: ExchangeConfig) -> None:
        """Inicializar."""
        super().__init__(config)
```

### Validação de Exchange Plugins

O sistema valida automaticamente:

- ✅ Herda de `ExchangeBase`
- ✅ Possui atributos obrigatórios: `name`, `id`, `countries`, `urls`, `version`
- ✅ Implementa métodos obrigatórios: `initialize`, `load_markets`, `fetch_markets`, `fetch_ticker`, `create_order`, `cancel_order`, `fetch_balance`

### Registro Automático

Coloque o arquivo do plugin em:
```
src/crypto_bot/plugins/exchanges/my_exchange_plugin.py
```

O sistema descobre automaticamente durante a inicialização.

## 📊 Indicator Plugins

### Interface Base

Indicadores podem implementar `BaseIndicator` (recomendado) ou seguir o `Indicator` Protocol:

```python
from crypto_bot.plugins.indicators.base import (
    BaseIndicator,
    IndicatorMetadata,
    InvalidIndicatorParameters,
)
import pandas as pd
from typing import Any, Mapping

class MyIndicator(BaseIndicator):
    """Indicador técnico customizado."""
    
    metadata = IndicatorMetadata(
        name="my_indicator",
        version="1.0",
        description="Descrição do indicador",
    )
    
    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validar parâmetros."""
        period = params.get("period", 14)
        if not isinstance(period, int) or period < 1:
            raise InvalidIndicatorParameters(
                f"period must be a positive integer, got {period}"
            )
    
    def _calculate_impl(
        self,
        data: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        """Calcular indicador."""
        period = params.get("period", 14)
        
        # Calcular indicador
        result = data["close"].rolling(window=period).mean()
        
        return result
```

### Implementação Completa - Exemplo (RSI)

```python
"""Relative Strength Index (RSI) indicator."""
from typing import Any, Mapping

import pandas as pd

from crypto_bot.plugins.indicators.base import (
    BaseIndicator,
    IndicatorMetadata,
    InvalidIndicatorParameters,
)

class RSIIndicator(BaseIndicator):
    """Relative Strength Index (RSI) indicator."""
    
    metadata = IndicatorMetadata(
        name="rsi",
        version="1.0",
        description="Relative Strength Index - momentum oscillator",
    )
    
    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validar parâmetros RSI."""
        length = params.get("length", 14)
        if not isinstance(length, int) or length < 1:
            raise InvalidIndicatorParameters(
                f"RSI 'length' must be a positive integer, got {length}"
            )
    
    def _calculate_impl(
        self,
        data: pd.DataFrame,
        params: Mapping[str, Any],
    ) -> pd.Series:
        """Calcular RSI."""
        length = params.get("length", 14)
        
        # Calcular mudanças de preço
        delta = data["close"].diff()
        
        # Separar ganhos e perdas
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        # Médias móveis de ganhos e perdas
        avg_gain = gain.rolling(window=length).mean()
        avg_loss = loss.rolling(window=length).mean()
        
        # Calcular RS e RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
```

### Validação de Indicator Plugins

O sistema valida:

- ✅ Herda de `BaseIndicator` ou implementa `Indicator` Protocol
- ✅ Possui `metadata` com `name`, `version`, `description`
- ✅ Implementa `validate_parameters`
- ✅ Implementa `_calculate_impl` (ou `calculate` se usar Protocol)
- ✅ Retorna `pd.Series` ou `pd.DataFrame`
- ✅ Não modifica o DataFrame de entrada

### Registro Automático

Coloque o arquivo do plugin em:
```
src/crypto_bot/plugins/indicators/my_indicator.py
```

O sistema descobre automaticamente.

## 🎯 Strategy Plugins

### Interface Base

Estratégias devem herdar de `Strategy` e implementar os métodos abstratos:

```python
from crypto_bot.plugins.strategies.base import Strategy, StrategySignal
from typing import Any, Mapping

class MyStrategy(Strategy):
    """Estratégia de trading customizada."""
    
    name = "my_strategy"
    
    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validar parâmetros."""
        threshold = params.get("threshold", 0.5)
        if not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
    
    def generate_signal(
        self,
        market_data: Any,
        params: Mapping[str, Any],
    ) -> StrategySignal:
        """Gerar sinal de trading."""
        # market_data contém: OHLCV, indicadores, etc.
        ohlcv = market_data.get("ohlcv")
        indicators = market_data.get("indicators", {})
        
        # Lógica da estratégia
        current_price = ohlcv["close"].iloc[-1]
        rsi = indicators.get("rsi")
        
        if rsi is not None:
            current_rsi = rsi.iloc[-1]
            
            if current_rsi < 30:
                # Sinal de compra
                return StrategySignal(
                    action="buy",
                    strength=Decimal("0.8"),
                    metadata={"reason": "RSI oversold"},
                )
            elif current_rsi > 70:
                # Sinal de venda
                return StrategySignal(
                    action="sell",
                    strength=Decimal("0.8"),
                    metadata={"reason": "RSI overbought"},
                )
        
        # Sem sinal (hold)
        return StrategySignal(
            action="hold",
            strength=Decimal("0.0"),
            metadata={},
        )
    
    def reset_state(self) -> None:
        """Reinicializar estado interno."""
        # Se a estratégia mantém estado, reinicializar aqui
        pass
```

### Implementação Completa - Exemplo (RSI Mean Reversion)

```python
"""RSI Mean Reversion Strategy."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar, Mapping

from crypto_bot.plugins.strategies.base import Strategy, StrategySignal

@dataclass
class _ValidatedParams:
    """Parâmetros validados."""
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

class RSIMeanReversion(Strategy):
    """Estratégia de mean reversion baseada em RSI."""
    
    name: ClassVar[str] = "rsi_mean_reversion"
    
    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """Validar parâmetros."""
        # Validações aqui
        pass
    
    def generate_signal(
        self,
        market_data: Any,
        params: Mapping[str, Any],
    ) -> StrategySignal:
        """Gerar sinal baseado em RSI."""
        # Implementação completa
        pass
    
    def reset_state(self) -> None:
        """Resetar estado."""
        pass
```

### Registro via Entry Points

**Para plugins internos**, o registro é automático se o arquivo estiver em `src/crypto_bot/plugins/strategies/`.

**Para plugins externos**, registre no `pyproject.toml`:

```toml
[project.entry-points."crypto_bot.strategies"]
my_strategy = "my_package.strategies:MyStrategy"
minha_estrategia = "meu_pacote.minha_mod:MinhaClasseEstrategia"
```

**Estrutura do pacote externo:**

```
my-strategy-plugin/
├── pyproject.toml
├── src/
│   └── my_package/
│       ├── __init__.py
│       └── strategies.py  # Contém MyStrategy
└── README.md
```

**Exemplo de `pyproject.toml`:**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-strategy-plugin"
version = "0.1.0"
description = "My custom trading strategy"

[project.entry-points."crypto_bot.strategies"]
my_strategy = "my_package.strategies:MyStrategy"
```

**Instalação:**

```bash
pip install -e /path/to/my-strategy-plugin
```

## 🔄 Processo de Registro

### Exchange e Indicator Plugins

**Descoberta Automática:**

1. Sistema escaneia `src/crypto_bot/plugins/exchanges/` e `src/crypto_bot/plugins/indicators/`
2. Importa módulos Python encontrados
3. Descobre classes que herdam de `ExchangeBase` ou `BaseIndicator`
4. Valida plugins encontrados
5. Registra em cache interno

**Não requer configuração adicional!**

### Strategy Plugins

**Descoberta via Entry Points:**

1. Sistema consulta Python Entry Points do grupo `crypto_bot.strategies`
2. Importa classes referenciadas
3. Valida que herdam de `Strategy`
4. Cacheia resultado com `@lru_cache`

**Requer registro no `pyproject.toml` (plugins externos) ou arquivo em `plugins/strategies/` (plugins internos).**

## ✅ Boas Práticas

### 1. Validação Robusta

```python
def validate_parameters(self, params: Mapping[str, Any]) -> None:
    """Sempre valide parâmetros com mensagens claras."""
    required = ["threshold"]
    for key in required:
        if key not in params:
            raise ValueError(f"Missing required parameter: {key}")
    
    threshold = params.get("threshold")
    if not isinstance(threshold, (int, float)):
        raise TypeError(f"threshold must be numeric, got {type(threshold)}")
    
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
```

### 2. Tratamento de Erros

```python
async def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
    """Sempre trate erros apropriadamente."""
    try:
        # Implementação
        pass
    except NetworkError as e:
        logger.error(f"Network error fetching ticker for {symbol}: {e}")
        raise
    except ExchangeError as e:
        logger.error(f"Exchange error: {e}")
        raise
```

### 3. Type Hints Completos

```python
from typing import Dict, List, Any
from decimal import Decimal

def calculate(
    self,
    data: pd.DataFrame,
    params: Mapping[str, Any],
) -> pd.Series:  # Sempre especifique tipo de retorno
    """..."""
    pass
```

### 4. Docstrings Completos

```python
async def create_order(
    self,
    request: CreateOrderRequest,
) -> OrderDTO:
    """
    Criar uma ordem na exchange.
    
    Args:
        request: Request de criação de ordem com símbolo, lado, tipo, quantidade, etc.
    
    Returns:
        OrderDTO com detalhes da ordem criada.
    
    Raises:
        ExchangeError: Se a exchange retornar erro
        NetworkError: Se houver erro de rede
        InsufficientBalance: Se não houver saldo suficiente
        InvalidOrder: Se os parâmetros da ordem forem inválidos
    
    Example:
        >>> request = CreateOrderRequest(
        ...     exchange="my_exchange",
        ...     symbol="BTC/USDT",
        ...     side=OrderSide.BUY,
        ...     type=OrderType.MARKET,
        ...     quantity=Decimal("0.001"),
        ... )
        >>> order = await plugin.create_order(request)
        >>> print(order.status)
        OrderStatus.OPEN
    """
    pass
```

### 5. Estado Stateless (quando possível)

Estratégias devem ser stateless ou gerenciar estado explicitamente:

```python
class MyStrategy(Strategy):
    """Estratégia stateless (recomendado)."""
    
    def generate_signal(self, market_data, params):
        # Não mantém estado, sempre determina sinal baseado em dados atuais
        pass
```

```python
class StatefulStrategy(Strategy):
    """Estratégia com estado gerenciado."""
    
    def __init__(self):
        self._state = {}
    
    def generate_signal(self, market_data, params):
        # Usa self._state para manter histórico
        pass
    
    def reset_state(self):
        """Sempre implemente reset_state para limpar estado."""
        self._state = {}
```

### 6. Não Modifique DataFrames de Entrada

```python
def _calculate_impl(
    self,
    data: pd.DataFrame,
    params: Mapping[str, Any],
) -> pd.Series:
    """Sempre trabalhe em cópia ou retorne novo objeto."""
    # ✅ CORRETO: Trabalha em cópia
    result = data["close"].rolling(window=14).mean()
    
    # ❌ ERRADO: Modifica DataFrame original
    # data["close"] = data["close"].rolling(window=14).mean()
    
    return result
```

### 7. Use Async/Await Corretamente

```python
# ✅ CORRETO
async def fetch_balance(self) -> Dict[str, BalanceDTO]:
    response = await self._http_client.get("/balance")
    return self._parse_balance(response)

# ❌ ERRADO (bloqueante)
async def fetch_balance(self) -> Dict[str, BalanceDTO]:
    response = requests.get("/balance")  # Bloqueia!
    return self._parse_balance(response)
```

## 🧪 Testes

### Exemplo: Teste de Exchange Plugin

```python
import pytest
from crypto_bot.plugins.exchanges.my_exchange_plugin import MyExchangePlugin

@pytest.mark.asyncio
async def test_my_exchange_plugin():
    """Testar plugin de exchange."""
    config = ExchangeConfig(
        enabled=True,
        sandbox=True,
        api_key="test_key",
        api_secret="test_secret",
    )
    
    plugin = MyExchangePlugin(config)
    await plugin.initialize()
    
    # Testar métodos
    markets = await plugin.load_markets()
    assert len(markets) > 0
    
    ticker = await plugin.fetch_ticker("BTC/USDT")
    assert "symbol" in ticker
    
    await plugin.close()
```

### Exemplo: Teste de Indicator Plugin

```python
import pandas as pd
import pytest
from crypto_bot.plugins.indicators.my_indicator import MyIndicator

def test_my_indicator():
    """Testar indicador."""
    indicator = MyIndicator()
    
    # Dados de teste
    data = pd.DataFrame({
        "close": [100, 101, 102, 101, 100],
    })
    
    # Calcular
    result = indicator.calculate(data, {"period": 2})
    
    assert isinstance(result, pd.Series)
    assert len(result) == len(data)
    assert not result.isna().all()
```

### Exemplo: Teste de Strategy Plugin

```python
import pytest
from crypto_bot.plugins.strategies.my_strategy import MyStrategy

def test_my_strategy():
    """Testar estratégia."""
    strategy = MyStrategy()
    
    # Validar parâmetros
    strategy.validate_parameters({"threshold": 0.5})
    
    with pytest.raises(ValueError):
        strategy.validate_parameters({"threshold": 1.5})  # Inválido
    
    # Gerar sinal
    market_data = {
        "ohlcv": pd.DataFrame({
            "close": [100, 101, 102],
        }),
        "indicators": {
            "rsi": pd.Series([30, 31, 32]),
        },
    }
    
    signal = strategy.generate_signal(market_data, {"threshold": 0.5})
    assert signal.action in ["buy", "sell", "hold"]
```

## 🔍 Troubleshooting

### Plugin não é descoberto

**Exchange/Indicator Plugins:**
- ✅ Verifique se o arquivo está em `src/crypto_bot/plugins/exchanges/` ou `src/crypto_bot/plugins/indicators/`
- ✅ Verifique se a classe herda corretamente de `ExchangeBase` ou `BaseIndicator`
- ✅ Verifique logs para erros de importação
- ✅ Execute `python -m crypto_bot.plugins.registry` para debug

**Strategy Plugins:**
- ✅ Verifique se está registrado no `pyproject.toml` (plugins externos)
- ✅ Verifique se o pacote está instalado: `pip list | grep my-strategy`
- ✅ Verifique Entry Points: `python -c "from importlib.metadata import entry_points; print(list(entry_points(group='crypto_bot.strategies')))"`

### Plugin falha na validação

- ✅ Verifique se todos os métodos obrigatórios estão implementados
- ✅ Verifique se atributos obrigatórios estão definidos
- ✅ Verifique mensagens de erro nos logs
- ✅ Consulte a documentação da interface base

### Erros de Importação

- ✅ Verifique dependências do plugin
- ✅ Verifique caminhos de importação
- ✅ Execute `python -m crypto_bot.plugins.registry` para ver erros detalhados

### Performance

- ✅ Use cache para dados que não mudam frequentemente
- ✅ Evite operações bloqueantes em métodos async
- ✅ Use conexões persistentes quando possível
- ✅ Implemente rate limiting apropriado

## 📚 Referências

- [Exchange Plugin Base](../src/crypto_bot/infrastructure/exchanges/base.py)
- [Indicator Plugin Base](../src/crypto_bot/plugins/indicators/base.py)
- [Strategy Plugin Base](../src/crypto_bot/plugins/strategies/base.py)
- [Plugin Registry](../src/crypto_bot/plugins/registry.py)
- [Exemplo: Binance Plugin](../src/crypto_bot/plugins/exchanges/binance_plugin.py)
- [Exemplo: RSI Indicator](../src/crypto_bot/plugins/indicators/pandas_ta_indicators.py)
- [Exemplo: RSI Strategy](../src/crypto_bot/plugins/strategies/rsi_mean_reversion.py)

## ✅ Checklist de Desenvolvimento

Antes de submeter um plugin:

- [ ] Plugin implementa interface completa
- [ ] Todos os métodos obrigatórios implementados
- [ ] Validação de parâmetros robusta
- [ ] Type hints completos
- [ ] Docstrings completos
- [ ] Testes unitários criados
- [ ] Testes de integração (para exchanges)
- [ ] Tratamento de erros adequado
- [ ] Não modifica dados de entrada (indicators)
- [ ] Estado gerenciado corretamente (strategies)
- [ ] Logging estruturado
- [ ] Código formatado com Black
- [ ] Sem erros de linting (Ruff)
- [ ] Sem erros de type checking (MyPy)
- [ ] Documentação atualizada

---

**💡 Dica**: Comece sempre com um plugin simples e teste antes de adicionar complexidade. Use os plugins existentes (Binance, RSI, etc.) como referência!
