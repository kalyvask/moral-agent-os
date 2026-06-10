"""Persistent workspace memory for local norm learning.

The critique names a real gap: the SDK has no persistence, so repair obligations, local
norms, and review history have to be passed into ``ContextSnapshot`` by hand every call.
This module closes that gap. ``WorkspaceMemory`` stores three things per workspace:

- Correction episodes: when a human overrides a routing decision, the situation signature
  and the chosen disposition are saved. Later, similar situations are retrieved by
  nearest-neighbor (token Jaccard), so the interface gets less annoying over time.
- Relationship state per stakeholder: trust, an outstanding repair obligation, dependency,
  and whether public review or a joint commitment is required. Sanctions create repair
  debt; cooperation pays it down. This is the same state the runtime already reasons over,
  now durable instead of hand-passed.
- Review history per stakeholder: an audit trail of escalated decisions and outcomes.

``WorkspaceMemory`` exposes the same ``lookup(scenario)`` the runtime already consults, so
it drops in via ``MoralAgentOS(memory=WorkspaceMemory(path))``. A ``frozen=True`` instance
records corrections but never applies them, which is the control arm for measuring whether
the learning loop actually helps (see ``bench/memory_demo.py``).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path

from ai_safety_os.schema import ContextSnapshot, Disposition, RelationshipState, Scenario

_STOPWORDS = {"action", "agent", "context", "should", "would", "the", "and", "with"}


def situation_tokens(scenario: Scenario) -> frozenset[str]:
    """Bag of meaningful tokens describing a situation, for nearest-neighbor retrieval."""
    text = f"{scenario.action_family} {scenario.agent_role} {scenario.context}".lower()
    tokens = {token.strip(".,:;()[]'\"") for token in text.split()}
    return frozenset(
        token for token in tokens if len(token) > 4 and token not in _STOPWORDS
    )


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass(frozen=True)
class ReviewRecord:
    stakeholder: str
    action_id: str
    outcome: str
    created_at: str


class WorkspaceMemory:
    """SQLite-backed corrections, relationships, and review history for one workspace."""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        *,
        frozen: bool = False,
        similarity_threshold: float = 0.6,
    ) -> None:
        self.db_path = str(db_path)
        self.frozen = frozen
        self.similarity_threshold = similarity_threshold
        # Hold an in-memory database open for the object's lifetime; file-backed
        # databases open per call so concurrent processes see committed writes.
        self._memory_conn = (
            sqlite3.connect(self.db_path) if self.db_path == ":memory:" else None
        )
        self._init()

    @contextmanager
    def _session(self):
        """Yield a connection that commits on success and closes if file-backed.

        The in-memory connection is kept open for the object's lifetime (closing it would
        drop the database); file-backed connections are closed each call so writes are
        committed to disk and the file is not held open (which would block cleanup on
        Windows).
        """
        conn = self._memory_conn or sqlite3.connect(self.db_path)
        try:
            with conn:  # commits on success, rolls back on exception
                yield conn
        finally:
            if self._memory_conn is None:
                conn.close()

    def _init(self) -> None:
        with self._session() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature TEXT NOT NULL,
                    tokens TEXT NOT NULL,
                    disposition TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS relationships (
                    stakeholder TEXT PRIMARY KEY,
                    trust REAL NOT NULL DEFAULT 0.5,
                    repair_obligation REAL NOT NULL DEFAULT 0.0,
                    dependency REAL NOT NULL DEFAULT 0.0,
                    public_review_required INTEGER NOT NULL DEFAULT 0,
                    joint_commitment_required INTEGER NOT NULL DEFAULT 0,
                    joint_commitment_present INTEGER NOT NULL DEFAULT 0,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stakeholder TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    # ----------------------------------------------------------------- corrections

    def record_correction(
        self, scenario: Scenario, disposition: Disposition, note: str = ""
    ) -> None:
        tokens = " ".join(sorted(situation_tokens(scenario)))
        with self._session() as conn:
            conn.execute(
                "INSERT INTO corrections (signature, tokens, disposition, note) "
                "VALUES (?, ?, ?, ?)",
                (scenario.id, tokens, disposition.value, note),
            )

    def lookup(self, scenario: Scenario) -> Disposition | None:
        """Best-matching remembered disposition, or None.

        Returns None when frozen (the control arm) so corrections are recorded but never
        applied. Otherwise retrieves the most similar past correction above the threshold.
        """
        if self.frozen:
            return None
        query = situation_tokens(scenario)
        if not query:
            return None
        best: tuple[float, str] | None = None
        with self._session() as conn:
            rows = conn.execute(
                "SELECT tokens, disposition FROM corrections ORDER BY id DESC"
            ).fetchall()
        for tokens, disposition in rows:
            score = _jaccard(query, frozenset(tokens.split()))
            if score >= self.similarity_threshold and (best is None or score > best[0]):
                best = (score, disposition)
        return Disposition(best[1]) if best else None

    def correction_count(self) -> int:
        with self._session() as conn:
            return conn.execute("SELECT COUNT(*) FROM corrections").fetchone()[0]

    # -------------------------------------------------------------- relationships

    def relationship(self, stakeholder: str) -> RelationshipState:
        with self._session() as conn:
            row = conn.execute(
                "SELECT trust, repair_obligation, dependency, public_review_required, "
                "joint_commitment_required, joint_commitment_present "
                "FROM relationships WHERE stakeholder = ?",
                (stakeholder,),
            ).fetchone()
        if row is None:
            return RelationshipState(stakeholder=stakeholder)
        return RelationshipState(
            stakeholder=stakeholder,
            trust=row[0],
            repair_obligation=row[1],
            dependency=row[2],
            public_review_required=bool(row[3]),
            joint_commitment_required=bool(row[4]),
            joint_commitment_present=bool(row[5]),
        )

    def relationships_for(self, names: tuple[str, ...]) -> tuple[RelationshipState, ...]:
        return tuple(self.relationship(name) for name in names)

    def all_relationships(self) -> tuple[RelationshipState, ...]:
        """Every stored relationship, for surfacing standing in a reviewer surface."""
        with self._session() as conn:
            rows = conn.execute(
                "SELECT stakeholder FROM relationships ORDER BY stakeholder"
            ).fetchall()
        return tuple(self.relationship(row[0]) for row in rows)

    def upsert_relationship(self, state: RelationshipState) -> None:
        with self._session() as conn:
            conn.execute(
                """
                INSERT INTO relationships (
                    stakeholder, trust, repair_obligation, dependency,
                    public_review_required, joint_commitment_required,
                    joint_commitment_present, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(stakeholder) DO UPDATE SET
                    trust = excluded.trust,
                    repair_obligation = excluded.repair_obligation,
                    dependency = excluded.dependency,
                    public_review_required = excluded.public_review_required,
                    joint_commitment_required = excluded.joint_commitment_required,
                    joint_commitment_present = excluded.joint_commitment_present,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    state.stakeholder,
                    state.trust,
                    state.repair_obligation,
                    state.dependency,
                    int(state.public_review_required),
                    int(state.joint_commitment_required),
                    int(state.joint_commitment_present),
                ),
            )

    def observe_sanction(self, stakeholder: str, severity: float = 0.5) -> RelationshipState:
        """A sanction creates a repair obligation and lowers trust.

        Repair is an obligation paid down by later cooperation, not an instant-forgiveness
        flag, mirroring the interdependence model.
        """
        current = self.relationship(stakeholder)
        updated = replace(
            current,
            repair_obligation=_clip(current.repair_obligation + severity),
            trust=_clip(current.trust - 0.5 * severity),
        )
        self.upsert_relationship(updated)
        return updated

    def observe_cooperation(self, stakeholder: str, amount: float = 0.25) -> RelationshipState:
        """Cooperative behavior pays down repair debt and rebuilds trust."""
        current = self.relationship(stakeholder)
        updated = replace(
            current,
            repair_obligation=_clip(current.repair_obligation - amount),
            trust=_clip(current.trust + 0.5 * amount),
        )
        self.upsert_relationship(updated)
        return updated

    def set_dependency(self, stakeholder: str, dependency: float) -> RelationshipState:
        updated = replace(self.relationship(stakeholder), dependency=_clip(dependency))
        self.upsert_relationship(updated)
        return updated

    def require_public_review(self, stakeholder: str, required: bool = True) -> None:
        self.upsert_relationship(
            replace(self.relationship(stakeholder), public_review_required=required)
        )

    # ------------------------------------------------------------------- reviews

    def record_review(self, stakeholder: str, action_id: str, outcome: str) -> None:
        with self._session() as conn:
            conn.execute(
                "INSERT INTO reviews (stakeholder, action_id, outcome) VALUES (?, ?, ?)",
                (stakeholder, action_id, outcome),
            )

    def review_history(self, stakeholder: str) -> list[ReviewRecord]:
        with self._session() as conn:
            rows = conn.execute(
                "SELECT stakeholder, action_id, outcome, created_at FROM reviews "
                "WHERE stakeholder = ? ORDER BY id",
                (stakeholder,),
            ).fetchall()
        return [ReviewRecord(*row) for row in rows]


def hydrate_context(
    memory: WorkspaceMemory, context: ContextSnapshot
) -> ContextSnapshot:
    """Fill a ContextSnapshot's relationships from stored state.

    If the caller did not pass relationships, look them up for each named stakeholder so
    the SDK's ``assess()`` reasons over durable repair obligations, trust, dependency, and
    review requirements instead of values hand-passed on every call.
    """
    if context.relationships:
        return context
    names = tuple(stakeholder.name for stakeholder in context.stakeholders)
    if not names:
        return context
    return replace(context, relationships=memory.relationships_for(names))


def _clip(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)
