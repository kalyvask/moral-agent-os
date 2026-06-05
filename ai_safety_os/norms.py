"""Local norm memory scaffold."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from ai_safety_os.schema import Disposition, Scenario


@runtime_checkable
class CorrectionStore(Protocol):
    """A store the runtime can consult for a remembered disposition.

    Both the lightweight ``LocalNormMemory`` and the richer ``WorkspaceMemory`` satisfy
    this, so either can back ``MoralAgentOS``.
    """

    def lookup(self, scenario: Scenario) -> Disposition | None: ...


@dataclass(frozen=True)
class NormCorrection:
    scenario_id: str
    situation_signature: str
    chosen_disposition: Disposition
    note: str


class LocalNormMemory:
    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self._memory_conn = sqlite3.connect(self.db_path) if self.db_path == ":memory:" else None
        self._init()

    def _connect(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        return sqlite3.connect(self.db_path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id TEXT NOT NULL,
                    situation_signature TEXT NOT NULL,
                    chosen_disposition TEXT NOT NULL,
                    note TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def signature_for(self, scenario: Scenario) -> str:
        text = f"{scenario.action_family}|{scenario.agent_role}|{scenario.context}".lower()
        tokens = [token.strip(".,:;()[]") for token in text.split()]
        important = sorted(
            {
                token
                for token in tokens
                if len(token) > 4
                and token
                not in {"action", "agent", "context", "should", "would"}
            }
        )
        return " ".join(important[:16])

    def add_correction(self, correction: NormCorrection) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO corrections (
                    scenario_id,
                    situation_signature,
                    chosen_disposition,
                    note
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    correction.scenario_id,
                    correction.situation_signature,
                    correction.chosen_disposition.value,
                    correction.note,
                ),
            )

    def lookup(self, scenario: Scenario) -> Disposition | None:
        signature = self.signature_for(scenario)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT chosen_disposition
                FROM corrections
                WHERE situation_signature = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (signature,),
            ).fetchone()
        if not row:
            return None
        return Disposition(row[0])
