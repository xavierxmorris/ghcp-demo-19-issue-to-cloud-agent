"""A single-machine admission ledger for synthetic enterprise rehearsals."""

from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .contracts import ContractError, Json

APPLICATION_ID = 0x47443139
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Reservation:
    status: str
    reason: str
    canonical_request_id: str | None = None


class AdmissionQueue:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def decide(
        self, *, request_id: str, input_hash: str, intent_hash: str, work_key: str, pipeline_key: str,
        route: str, policy_status: str, policy_reason: str,
        max_queued: int, remaining_admissions: int, stop_new_work: bool,
    ) -> Reservation:
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            prior = self.connection.execute(
                "SELECT input_hash FROM requests WHERE request_id = ?", (request_id,),
            ).fetchone()
            if prior is not None and prior[0] != input_hash:
                return Reservation("blocked", "REQUEST_ID_CHANGED")
            if prior is None:
                self.connection.execute(
                    "INSERT INTO requests(request_id, input_hash) VALUES (?, ?)",
                    (request_id, input_hash),
                )
            if policy_status != "candidate":
                return Reservation(policy_status, policy_reason)
            existing = self.connection.execute(
                "SELECT request_id, intent_hash FROM work_items WHERE work_key = ?", (work_key,),
            ).fetchone()
            if existing is not None:
                if existing[1] != intent_hash:
                    return Reservation("blocked", "WORK_INTENT_CHANGED", existing[0])
                return Reservation("duplicate", "WORK_ALREADY_RESERVED", existing[0])
            occupied = self.connection.execute(
                "SELECT request_id FROM work_items WHERE pipeline_key = ?", (pipeline_key,),
            ).fetchone()
            if occupied is not None:
                return Reservation("deferred", "PIPELINE_ALREADY_QUEUED", occupied[0])
            if stop_new_work:
                return Reservation("deferred", "STOP_SWITCH")
            if remaining_admissions <= 0:
                return Reservation("deferred", "RUN_SUBMISSION_LIMIT")
            queued = self.connection.execute("SELECT COUNT(*) FROM work_items").fetchone()[0]
            if queued >= max_queued:
                return Reservation("deferred", "QUEUE_CAPACITY")
            self.connection.execute(
                "INSERT INTO work_items(work_key, pipeline_key, request_id, intent_hash, route) VALUES (?, ?, ?, ?, ?)",
                (work_key, pipeline_key, request_id, intent_hash, route),
            )
            return Reservation("admitted", "LOCAL_RESERVATION_CREATED", request_id)

    def snapshot(self) -> list[dict[str, Json]]:
        rows = self.connection.execute(
            "SELECT work_key, request_id, route FROM work_items ORDER BY request_id",
        ).fetchall()
        return [
            {"work_key": row[0], "request_id": row[1], "route": row[2], "state": "queued-locally"}
            for row in rows
        ]


@contextmanager
def open_queue(path: Path, policy_fingerprint: str) -> Iterator[AdmissionQueue]:
    if path.suffix != ".sqlite3" or path.is_symlink():
        raise ContractError("Use a regular .sqlite3 file for the local enterprise ledger")
    path.parent.mkdir(parents=True, exist_ok=True)
    existed = path.exists()
    if not existed:
        path.touch(exist_ok=False)
    elif not path.is_file():
        raise ContractError("Enterprise ledger must be a regular file")
    with closing(sqlite3.connect(path, timeout=5, isolation_level=None)) as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            if existed:
                if connection.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
                    raise ContractError("Existing database is not an initialized enterprise-demo ledger")
                if connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                    raise ContractError("Unsupported enterprise ledger version")
                stored = connection.execute("SELECT fingerprint FROM policy WHERE id = 1").fetchone()
                if stored is None or stored[0] != policy_fingerprint:
                    raise ContractError("Ledger policy/engine differs; use a new ledger instead of rewriting history")
            else:
                connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
                connection.execute("CREATE TABLE policy(id INTEGER PRIMARY KEY CHECK(id = 1), fingerprint TEXT NOT NULL)")
                connection.execute("INSERT INTO policy VALUES (1, ?)", (policy_fingerprint,))
                connection.execute(
                    "CREATE TABLE requests(request_id TEXT PRIMARY KEY, input_hash TEXT NOT NULL)",
                )
                connection.execute(
                    "CREATE TABLE work_items("
                    "work_key TEXT PRIMARY KEY, pipeline_key TEXT NOT NULL UNIQUE, "
                    "request_id TEXT NOT NULL UNIQUE, intent_hash TEXT NOT NULL, route TEXT NOT NULL,"
                    "FOREIGN KEY(request_id) REFERENCES requests(request_id))",
                )
        connection.execute("PRAGMA foreign_keys = ON")
        yield AdmissionQueue(connection)
