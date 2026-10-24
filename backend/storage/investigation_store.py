"""Canonical Persistent Investigation Store for JANUS (Phase 9).

Provides robust SQLite-backed persistence, ACID transaction isolation, optimistic concurrency locking,
append-only event journaling, and idempotent observation execution across requests and application restarts.
"""

import os
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

from agents.types import (
    AgentInvestigationReport,
    InvestigationEvent,
    ObservationRecord,
    ObservationProvenance,
)


class ConcurrencyConflictError(Exception):
    """Raised when an update encounters an optimistic locking version conflict."""
    pass


class InvestigationNotFoundError(Exception):
    """Raised when an investigation ID does not exist in persistent storage."""
    pass


class DuplicateObservationError(Exception):
    """Raised when an identical observation idempotency key was already applied."""
    def __init__(self, message: str, existing_report: Optional[AgentInvestigationReport] = None):
        super().__init__(message)
        self.existing_report = existing_report


class InvestigationStore:
    """Authoritative, thread-safe persistent store for scientific investigations."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Respect environment variable, or default to data/janus_investigations.db
            env_path = os.getenv("JANUS_DB_PATH")
            if env_path:
                self.db_path = env_path
            else:
                # Find project root data/ directory
                root_dir = Path(__file__).resolve().parent.parent.parent
                data_dir = root_dir / "data"
                data_dir.mkdir(parents=True, exist_ok=True)
                self.db_path = str(data_dir / "janus_investigations.db")
        else:
            self.db_path = db_path

        self._lock = threading.RLock()
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem_conn.row_factory = sqlite3.Row
            self._mem_conn.execute("PRAGMA foreign_keys=ON;")
            self._mem_conn.execute("PRAGMA busy_timeout=5000;")
        else:
            self._mem_conn = None
        self._init_db()

    def _close_conn(self, conn: sqlite3.Connection) -> None:
        """Closes connection if not persistent in-memory connection."""
        if self._mem_conn is None:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a connection configured with WAL journal mode and busy timeout."""
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # WAL mode provides concurrent reads while write transactions are active
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self) -> None:
        """Initializes canonical tables and indexes with safe additive DDL."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS investigations (
                        investigation_id TEXT PRIMARY KEY,
                        version INTEGER NOT NULL DEFAULT 1,
                        question TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        status TEXT NOT NULL,
                        case_study_id TEXT,
                        remaining_budget REAL NOT NULL DEFAULT 10.0,
                        conclusion_gate TEXT,
                        auditor_status TEXT,
                        state_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS investigation_events (
                        event_id TEXT PRIMARY KEY,
                        investigation_id TEXT NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
                        event_type TEXT NOT NULL,
                        version_after INTEGER NOT NULL,
                        idempotency_key TEXT,
                        payload_json TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS investigation_observations (
                        observation_id TEXT PRIMARY KEY,
                        investigation_id TEXT NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
                        experiment_id TEXT NOT NULL,
                        observed_outcome TEXT NOT NULL,
                        provenance TEXT NOT NULL,
                        cost REAL NOT NULL,
                        idempotency_key TEXT UNIQUE,
                        prior_snapshot_json TEXT NOT NULL,
                        posterior_snapshot_json TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        status TEXT NOT NULL
                    );
                """)

                conn.execute("CREATE INDEX IF NOT EXISTS idx_investigations_case ON investigations(case_study_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_investigation ON investigation_events(investigation_id);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_investigation ON investigation_observations(investigation_id);")
                conn.commit()

    def save(
        self,
        report: AgentInvestigationReport,
        event_type: str = "STATE_UPDATE",
        idempotency_key: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> AgentInvestigationReport:
        """Persists or updates an investigation state in an atomic transaction.

        Args:
            report: Canonical AgentInvestigationReport to persist.
            event_type: Event type to append to event journal.
            idempotency_key: Optional idempotency key for this mutation.
            expected_version: Optional expected state version for optimistic locking.

        Raises:
            ConcurrencyConflictError: If expected_version does not match current version.
        """
        now_str = datetime.now(timezone.utc).isoformat()
        if not report.created_at:
            report.created_at = now_str
        report.updated_at = now_str

        conclusion_gate_val = (
            report.review_report.conclusion_gate.value
            if report.review_report and hasattr(report.review_report, "conclusion_gate")
            else None
        )
        auditor_status_val = None
        if report.analysis_result and report.analysis_result.independent_verification:
            aud = report.analysis_result.independent_verification.get("auditor_uagent", {})
            if isinstance(aud, dict):
                auditor_status_val = aud.get("status")

        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    cur = conn.cursor()

                    # Check if investigation already exists
                    cur.execute(
                        "SELECT version FROM investigations WHERE investigation_id = ?",
                        (report.investigation_id,),
                    )
                    existing_row = cur.fetchone()

                    # Append to event audit trail first so state_json captures it
                    event_id = f"EVT-{uuid4().hex[:12].upper()}"
                    event_obj = InvestigationEvent(
                        event_id=event_id,
                        investigation_id=report.investigation_id,
                        event_type=event_type,
                        version_after=report.version,
                        idempotency_key=idempotency_key,
                        payload={"status": report.status, "remaining_budget": report.remaining_budget},
                        timestamp=now_str,
                    )
                    report.events.append(event_obj)
                    if idempotency_key and idempotency_key not in report.idempotency_keys:
                        report.idempotency_keys.append(idempotency_key)

                    report_state_json = report.model_dump_json()

                    if existing_row:
                        current_db_version = existing_row["version"]
                        if expected_version is not None and current_db_version != expected_version:
                            raise ConcurrencyConflictError(
                                f"State version conflict for '{report.investigation_id}': "
                                f"expected version {expected_version}, but database version is {current_db_version}."
                            )

                        # Update existing record
                        cur.execute(
                            """
                            UPDATE investigations
                            SET version = ?,
                                question = ?,
                                mode = ?,
                                status = ?,
                                case_study_id = ?,
                                remaining_budget = ?,
                                conclusion_gate = ?,
                                auditor_status = ?,
                                state_json = ?,
                                updated_at = ?
                            WHERE investigation_id = ?
                            """,
                            (
                                report.version,
                                report.question,
                                report.mode,
                                report.status,
                                report.case_study_id,
                                report.remaining_budget,
                                conclusion_gate_val,
                                auditor_status_val,
                                report_state_json,
                                report.updated_at,
                                report.investigation_id,
                            ),
                        )
                    else:
                        # Insert new record
                        cur.execute(
                            """
                            INSERT INTO investigations (
                                investigation_id, version, question, mode, status,
                                case_study_id, remaining_budget, conclusion_gate,
                                auditor_status, state_json, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                report.investigation_id,
                                report.version,
                                report.question,
                                report.mode,
                                report.status,
                                report.case_study_id,
                                report.remaining_budget,
                                conclusion_gate_val,
                                auditor_status_val,
                                report_state_json,
                                report.created_at,
                                report.updated_at,
                            ),
                        )

                    cur.execute(
                        """
                        INSERT INTO investigation_events (
                            event_id, investigation_id, event_type, version_after,
                            idempotency_key, payload_json, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event_id,
                            report.investigation_id,
                            event_type,
                            report.version,
                            idempotency_key,
                            json.dumps(event_obj.payload),
                            now_str,
                        ),
                    )

                return report
            finally:
                self._close_conn(conn)

    def get(self, investigation_id: str) -> Optional[AgentInvestigationReport]:
        """Retrieves an investigation from persistent storage by ID."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT state_json FROM investigations WHERE investigation_id = ?",
                    (investigation_id,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return AgentInvestigationReport.model_validate_json(row["state_json"])
            finally:
                self._close_conn(conn)

    def list_all(self, limit: int = 100) -> List[AgentInvestigationReport]:
        """Lists all persistent investigations ordered by recent update."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    "SELECT state_json FROM investigations ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                )
                rows = cur.fetchall()
                reports: List[AgentInvestigationReport] = []
                for row in rows:
                    try:
                        reports.append(AgentInvestigationReport.model_validate_json(row["state_json"]))
                    except Exception:
                        pass
                return reports
            finally:
                self._close_conn(conn)

    def find_observation_by_idempotency_key(
        self,
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """Checks if an observation with the given idempotency key was already recorded."""
        if not idempotency_key:
            return None
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT observation_id, investigation_id, experiment_id,
                           observed_outcome, provenance, timestamp, status
                    FROM investigation_observations
                    WHERE idempotency_key = ?
                    """,
                    (idempotency_key,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                return dict(row)
            finally:
                self._close_conn(conn)

    def record_observation_record(
        self,
        record: ObservationRecord,
        investigation_id: str,
    ) -> None:
        """Inserts an observation entry into the durable observations ledger."""
        with self._lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute(
                        """
                        INSERT INTO investigation_observations (
                            observation_id, investigation_id, experiment_id,
                            observed_outcome, provenance, cost, idempotency_key,
                            prior_snapshot_json, posterior_snapshot_json,
                            timestamp, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record.observation_id,
                            investigation_id,
                            record.experiment_id,
                            record.observed_outcome,
                            record.provenance,
                            record.cost,
                            record.idempotency_key,
                            json.dumps(record.prior_snapshot),
                            json.dumps(record.posterior_snapshot),
                            record.timestamp,
                            record.status,
                        ),
                    )
            finally:
                self._close_conn(conn)

    def get_events(self, investigation_id: str) -> List[InvestigationEvent]:
        """Retrieves the full append-only audit trail for an investigation."""
        with self._lock:
            conn = self._get_connection()
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT event_id, investigation_id, event_type, version_after,
                           idempotency_key, payload_json, timestamp
                    FROM investigation_events
                    WHERE investigation_id = ?
                    ORDER BY version_after ASC, timestamp ASC
                    """,
                    (investigation_id,),
                )
                events: List[InvestigationEvent] = []
                for row in cur.fetchall():
                    events.append(
                        InvestigationEvent(
                            event_id=row["event_id"],
                            investigation_id=row["investigation_id"],
                            event_type=row["event_type"],
                            version_after=row["version_after"],
                            idempotency_key=row["idempotency_key"],
                            payload=json.loads(row["payload_json"]),
                            timestamp=row["timestamp"],
                        )
                    )
                return events
            finally:
                self._close_conn(conn)

    def clear_all_data(self) -> None:
        """Clears all records (used exclusively in isolated test fixtures)."""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM investigation_observations;")
                conn.execute("DELETE FROM investigation_events;")
                conn.execute("DELETE FROM investigations;")
                conn.commit()


# Process-wide singleton instance
_GLOBAL_STORE: Optional[InvestigationStore] = None
_STORE_LOCK = threading.Lock()


def get_investigation_store() -> InvestigationStore:
    """Returns the process-wide canonical InvestigationStore instance."""
    global _GLOBAL_STORE
    expected_path = os.getenv("JANUS_DB_PATH", "data/janus_investigations.db")
    if _GLOBAL_STORE is None or _GLOBAL_STORE.db_path != expected_path:
        with _STORE_LOCK:
            if _GLOBAL_STORE is None or _GLOBAL_STORE.db_path != expected_path:
                _GLOBAL_STORE = InvestigationStore(db_path=expected_path)
    return _GLOBAL_STORE


def set_investigation_store(store: Optional[InvestigationStore]) -> None:
    """Sets or resets the process-wide InvestigationStore instance (for testing)."""
    global _GLOBAL_STORE
    with _STORE_LOCK:
        _GLOBAL_STORE = store
        if store is not None:
            os.environ["JANUS_DB_PATH"] = store.db_path
