from __future__ import annotations

from functools import lru_cache
from importlib.metadata import EntryPoint, entry_points
from typing import Dict, Iterable, Mapping, Type

from crypto_bot.utils.structured_logger import get_logger

from .base import Strategy

# Grupo de entry points para estratégias externas
ENTRY_POINT_GROUP: str = "crypto_bot.strategies"


@lru_cache(maxsize=1)
def discover_strategies() -> Mapping[str, Type[Strategy]]:
    """
    Descobre e valida estratégias registradas via Entry Points.

    Returns:
        Mapping de `name` -> classe `Strategy`.

    Observações:
    - Apenas classes que são subclasses de `Strategy` serão registradas.
    - Estratégias com nomes duplicados serão ignoradas após o primeiro registro.
    - Falhas ao carregar um entry point são ignoradas para não interromper a descoberta.
    """

    logger = get_logger(__name__)
    logger.info("discover_strategies:start", entry_point_group=ENTRY_POINT_GROUP)

    discovered: Dict[str, Type[Strategy]] = {}

    try:
        eps_iter: Iterable[EntryPoint] = entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        # Compatibilidade defensiva para ambientes antigos (API de entrada sem argumentos)
        all_eps = entry_points()
        selector = getattr(all_eps, "select", None)
        eps_iter = selector(group=ENTRY_POINT_GROUP) if callable(selector) else []

    eps_list = list(eps_iter)
    logger.debug(
        "discover_strategies:entry_points_fetched",
        count=len(eps_list),
    )

    for ep in eps_list:
        try:
            loaded = ep.load()
        except Exception as exc:
            logger.warning(
                "discover_strategies:load_failed",
                entry_point=str(getattr(ep, "value", ep)),
                exc_type=type(exc).__name__,
            )
            continue

        # Suportar tanto classe Strategy quanto fábrica que retorna classe Strategy
        candidate = loaded
        try:
            # Se for uma fábrica zero-arg que retorna a classe
            if not isinstance(candidate, type) and callable(candidate):
                candidate = candidate()
        except Exception as exc:
            logger.warning(
                "discover_strategies:factory_failed",
                entry_point=str(getattr(ep, "value", ep)),
                exc_type=type(exc).__name__,
            )
            continue

        if not isinstance(candidate, type):
            logger.warning(
                "discover_strategies:invalid_type",
                entry_point=str(getattr(ep, "value", ep)),
            )
            continue
        if not issubclass(candidate, Strategy):
            logger.warning(
                "discover_strategies:not_subclass",
                candidate=getattr(candidate, "__name__", str(candidate)),
            )
            continue

        # Verifica atributo `name` definido na classe
        strategy_name = getattr(candidate, "name", None)
        if not isinstance(strategy_name, str) or not strategy_name:
            logger.warning(
                "discover_strategies:missing_name",
                candidate=getattr(candidate, "__name__", str(candidate)),
            )
            continue

        if strategy_name in discovered:
            # Duplicata: manter o primeiro registro
            logger.warning("discover_strategies:duplicate_name", name=strategy_name)
            continue

        discovered[strategy_name] = candidate
        logger.info(
            "discover_strategies:registered", name=strategy_name, cls=candidate.__name__
        )

    logger.info("discover_strategies:done", registered=list(discovered.keys()))
    return discovered
