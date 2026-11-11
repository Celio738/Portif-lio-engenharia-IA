from enum import Enum
from typing import List
from pydantic import BaseModel, Field


class SentimentEnum(str, Enum):
    POSITIVO = "POSITIVO"
    NEUTRO = "NEUTRO"
    NEGATIVO = "NEGATIVO"


class IssueCategoryEnum(str, Enum):
    LOGISTICA_ATRASO = "LOGISTICA_ATRASO"
    QUALIDADE_PREPARO = "QUALIDADE_PREPARO"
    EMBALAGEM_VIOLADA = "EMBALAGEM_VIOLADA"
    ITEM_FALTANTE_ERRADO = "ITEM_FALTANTE_ERRADO"
    SUSPEITA_FRAUDE = "SUSPEITA_FRAUDE"
    ELOGIO_GERAL = "ELOGIO_GERAL"


class UrgencyLevelEnum(str, Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class ReviewInput(BaseModel):
    order_id: str = Field(..., min_length=3, description="ID único do pedido")
    customer_id: str = Field(..., description="ID do cliente")
    restaurant_id: str = Field(..., description="ID do restaurante parceiro")
    rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5 estrelas")
    review_text: str = Field(..., min_length=5, description="Texto bruto da avaliação")


class TriageResult(BaseModel):
    sentiment: SentimentEnum = Field(..., description="Sentimento global da avaliação")
    primary_category: IssueCategoryEnum = Field(..., description="Categoria raiz do ocorrido")
    urgency: UrgencyLevelEnum = Field(..., description="Nível de urgência operacional")
    refund_recommended: bool = Field(..., description="Indica se requer análise de reembolso/cupom")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Grau de confiança da extração")
    key_entities: List[str] = Field(default_factory=list, description="Itens do cardápio ou problemas citados")
    suggested_response: str = Field(..., description="Resposta empática sugerida ao cliente")
    internal_routing_team: str = Field(..., description="Squad responsável: Logística, Restaurante, Risco/Fraude ou CRM")
