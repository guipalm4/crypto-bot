# Estratégias como Plugins

Este documento descreve como o bot descobre e carrega estratégias de trading via Entry Points do Python.

## Interface Base

- Arquivo: `src/crypto_bot/plugins/strategies/base.py`
- Classe ABC: `Strategy`
  - `name: ClassVar[str]` — identificador único da estratégia
  - `validate_parameters(params)` — valida parâmetros
  - `generate_signal(market_data, params) -> StrategySignal` — gera sinal padronizado
  - `reset_state()` — reinicializa estado interno
- DTO: `StrategySignal` (action, strength, metadata)

## Descoberta de Plugins

- Arquivo: `src/crypto_bot/plugins/strategies/loader.py`
- Grupo de entry points: `crypto_bot.strategies`
- Função principal: `discover_strategies() -> Mapping[str, Type[Strategy]]`
  - Usa `importlib.metadata.entry_points(group=...)`
  - Valida subclasses de `Strategy`
  - Previne nomes duplicados (primeiro registro vence)
  - Cache com `functools.lru_cache(maxsize=1)`
  - Log estruturado dos eventos de descoberta/erros

## Como Registrar um Plugin Externo

No pacote da sua estratégia (instalado no mesmo ambiente), adicione no `pyproject.toml`:

```toml
[project.entry-points."crypto_bot.strategies"]
minha_estrategia = "meu_pacote.minha_mod:MinhaClasseEstrategia"
```

A classe referenciada deve herdar de `Strategy` e definir `name`.

## Fallback

Se nenhum plugin for encontrado, `discover_strategies()` retorna um mapeamento vazio e o sistema continua operando sem crash, registrando avisos de log.

## Boas Práticas

- Evite `pkg_resources`; prefira `importlib.metadata`
- Valide interface antes de registrar (segurança e tipagem)
- Trate exceções por plugin isoladamente
- Utilize logs estruturados para auditoria e debug

## Testes

- Testes unitários em `tests/unit/plugins/test_strategy_loader.py` cobrem:
  - descoberta de plugins válidos
  - ignorar não-subclasses
  - nomes duplicados
  - falhas de carregamento
  - cenário sem plugins
