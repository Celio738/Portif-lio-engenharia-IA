import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class ReviewDatabase:
    """Camada de persistência SQLite com garantia de idempotência para evitar
    reprocessamento de chamadas de LLM e duplicidade de eventos."""

    def __init__(self, db_path: str = "triage_events.db") -> None:
        self.db_path = db_path
        self._init_table()

    def _init_table(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_triage_logs (
                    idempotency_key TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    customer_id TEXT NOT NULL,
                    restaurant_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    sanitized_text TEXT NOT NULL,
                    injection_flagged INTEGER NOT NULL,
                    triage_json TEXT NOT NULL,
                    processed_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_by_idempotency_key(self, key: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT triage_json, processed_at FROM review_triage_logs WHERE idempotency_key = ?",
                (key,),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "cached": True,
                    "processed_at": row[1],
                    "result": json.loads(row[0]),
                }
        return None

    def save_triage(
        self,
        idempotency_key: str,
        order_id: str,
        customer_id: str,
        restaurant_id: str,
        rating: int,
        sanitized_text: str,
        injection_flagged: bool,
        triage_result_dict: Dict[str, Any],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO review_triage_logs (
                    idempotency_key, order_id, customer_id, restaurant_id,
                    rating, sanitized_text, injection_flagged, triage_json, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    idempotency_key,
                    order_id,
                    customer_id,
                    restaurant_id,
                    rating,
                    sanitized_text,
                    1 if injection_flagged else 0,
                    json.dumps(triage_result_dict, ensure_ascii=False),
                    now,
                ),
            )
            conn.commit()
