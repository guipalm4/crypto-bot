from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Mapping, MutableMapping


@dataclass(slots=True)
class StrategySignal:
    """
    Representa um sinal gerado por uma estratégia.

    Attributes:
        action: Ação recomendada (por exemplo: "buy", "sell", "hold").
        strength: Força/confiança do sinal, tipicamente em [0.0, 1.0].
        metadata: Informações adicionais relevantes para auditoria/explicabilidade.
    """

    action: str
    strength: float = 0.0
    metadata: MutableMapping[str, Any] = field(default_factory=dict)


class Strategy(ABC):
    """
    Interface base para estratégias de trading plugáveis.

    Requisitos para implementações concretas:
    - Definir `name` como identificador único e estável da estratégia.
    - Validar parâmetros de configuração recebidos.
    - Gerar sinais a partir de dados de mercado e parâmetros.
    - Gerenciar e reinicializar estado interno quando necessário.
    """

    name: ClassVar[str]

    @abstractmethod
    def validate_parameters(self, params: Mapping[str, Any]) -> None:
        """
        Valida os parâmetros fornecidos para a estratégia.

        Args:
            params: Mapeamento de parâmetros de configuração.

        Raises:
            ValueError: Quando parâmetros obrigatórios estão ausentes ou inválidos.
            TypeError: Quando tipos de parâmetros não correspondem ao esperado.
        """

    @abstractmethod
    def generate_signal(
        self, market_data: Any, params: Mapping[str, Any]
    ) -> StrategySignal:
        """
        Gera um `StrategySignal` a partir dos dados de mercado e parâmetros.

        Args:
            market_data: Estrutura com dados de mercado (ex.: candles, indicadores, etc.).
            params: Mapeamento de parâmetros validados.

        Returns:
            StrategySignal: Sinal de trading padronizado.
        """

    @abstractmethod
    def reset_state(self) -> None:
        """
        Reinicializa qualquer estado interno mantido pela estratégia.
        """
