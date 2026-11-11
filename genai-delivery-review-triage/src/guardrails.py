import hashlib
import re
from typing import Tuple


class SecurityGuardrails:
    """Camada de proteção para conformidade LGPD (PII Masking),
    detecção de Prompt Injection e geração de chave de idempotência."""

    CPF_REGEX = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")
    PHONE_REGEX = re.compile(r"(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b")
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"ignore\s+as\s+instru[cç][oõ]es\s+anteriores",
        r"system\s+prompt",
        r"voc[eê]\s+agora\s+[eé]\s+um",
        r"aprove\s+o\s+reembolso\s+obrigatoriamente",
        r"retorne\s+json\s+com\s+refund_recommended\s*=\s*true",
    ]

    @classmethod
    def sanitize_pii(cls, text: str) -> str:
        """Mascaramento determinístico de dados pessoais sensíveis (LGPD)."""
        sanitized = cls.CPF_REGEX.sub("[CPF_OCULTO_LGPD]", text)
        sanitized = cls.EMAIL_REGEX.sub("[EMAIL_OCULTO_LGPD]", sanitized)
        sanitized = cls.PHONE_REGEX.sub("[TELEFONE_OCULTO_LGPD]", sanitized)
        return sanitized

    @classmethod
    def detect_prompt_injection(cls, text: str) -> Tuple[bool, str]:
        """Verifica tentativas de sequestro de instrução (Prompt Injection)."""
        lowered = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                return True, f"Padrão suspeito detectado: {pattern}"
        return False, "OK"

    @staticmethod
    def generate_idempotency_key(order_id: str, customer_id: str, review_text: str) -> str:
        """Gera hash SHA-256 único para garantir idempotência transacional no banco."""
        raw_payload = f"{order_id.strip()}::{customer_id.strip()}::{review_text.strip()}"
        return hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
