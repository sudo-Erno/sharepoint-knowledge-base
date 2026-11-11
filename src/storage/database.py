import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DATABASE_PATH = Path("data/state/knowledge.db")

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def observe_document(
    document_id: str,
    filename: str,
    observed_hash: str
) -> None:

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO documents (
                document_id,
                filename,
                observed_hash,
                status,
                updated_at
            )
            VALUES (?, ?, ?, 'pending', ?)

            ON CONFLICT(document_id)
            DO UPDATE SET
                filename = excluded.filename,
                observed_hash = excluded.observed_hash,

                status = CASE

                    WHEN documents.status = 'deleted'
                        THEN 'pending'

                    WHEN documents.observed_hash != excluded.observed_hash
                         AND documents.status != 'processing'
                        THEN 'pending'

                    ELSE documents.status

                END,

                updated_at = excluded.updated_at
            """,
            (
                document_id,
                filename,
                observed_hash,
                utc_now()
            )
        )

def initialize_database() -> None:

    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id TEXT NOT NULL UNIQUE,

                filename TEXT NOT NULL,

                observed_hash TEXT NOT NULL,

                processed_hash TEXT,

                processing_hash TEXT,

                status TEXT NOT NULL DEFAULT 'pending',

                last_error TEXT,

                retry_count INTEGER NOT NULL DEFAULT 0,

                updated_at TEXT NOT NULL,

                processed_at TEXT,

                CHECK (
                    status IN (
                        'pending',
                        'processing',
                        'completed',
                        'failed',
                        'deleted'
                    )
                )
            )
            """
        )

        connection.commit()

def get_document(document_id: str):

    with get_connection() as connection:

        cursor = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE document_id = ?
            """,
            (document_id,)
        )

        return cursor.fetchone()

def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )
    connection.row_factory = sqlite3.Row
    return connection

def save_document(
    document_id: str,
    filename: str,
    file_hash: str,
    status: str
) -> None:

    updated_at = datetime.now(
        timezone.utc
    ).isoformat()

    with get_connection() as connection:

        connection.execute(
            """
            INSERT INTO documents (
                document_id,
                filename,
                file_hash,
                status,
                updated_at
            )

            VALUES (?, ?, ?, ?, ?)

            ON CONFLICT(document_id)
            DO UPDATE SET
                filename = excluded.filename,
                file_hash = excluded.file_hash,
                status = excluded.status,
                updated_at = excluded.updated_at
            """,
            (
                document_id,
                filename,
                file_hash,
                status,
                updated_at
            )
        )

        connection.commit()

def should_process(document_id: str) -> bool:

    document = get_document(document_id)

    if document is None:
        return False

    status = document["status"]

    if status in ("processing", "deleted"):
        return False

    if status in ("pending", "failed"):
        return True

    return (
        document["observed_hash"]
        != document["processed_hash"]
    )

def start_processing(document_id: str) -> str | None:

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE documents
            SET
                status = 'processing',
                processing_hash = observed_hash,
                last_error = NULL,
                updated_at = ?

            WHERE document_id = ?
              AND status IN ('pending', 'failed')
              AND (
                    processed_hash IS NULL
                    OR observed_hash != processed_hash
                    OR status = 'failed'
              )
            """,
            (
                utc_now(),
                document_id
            )
        )

        if cursor.rowcount != 1:
            return None

        row = connection.execute(
            """
            SELECT processing_hash
            FROM documents
            WHERE document_id = ?
            """,
            (document_id,)
        ).fetchone()

        return row["processing_hash"]

def complete_processing(
    document_id: str,
    processing_hash: str
) -> bool:

    now = utc_now()

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE documents
            SET
                processed_hash = ?,
                processing_hash = NULL,

                status = CASE
                    WHEN observed_hash = ?
                        THEN 'completed'
                    ELSE 'pending'
                END,

                last_error = NULL,
                retry_count = 0,
                processed_at = ?,
                updated_at = ?

            WHERE document_id = ?
              AND status = 'processing'
              AND processing_hash = ?
            """,
            (
                processing_hash,
                processing_hash,
                now,
                now,
                document_id,
                processing_hash
            )
        )

        return cursor.rowcount == 1

def fail_processing(
    document_id: str,
    processing_hash: str,
    error_message: str
) -> bool:

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE documents
            SET
                status = 'failed',
                processing_hash = NULL,
                last_error = ?,
                retry_count = retry_count + 1,
                updated_at = ?

            WHERE document_id = ?
              AND status = 'processing'
              AND processing_hash = ?
            """,
            (
                error_message,
                utc_now(),
                document_id,
                processing_hash
            )
        )

        return cursor.rowcount == 1

def mark_missing_documents(
    observed_ids: set[str]
) -> int:

    with get_connection() as connection:

        rows = connection.execute(
            """
            SELECT document_id
            FROM documents
            WHERE document_id LIKE 'local:%'
              AND status != 'deleted'
            """
        ).fetchall()

        missing_ids = [
            row["document_id"]
            for row in rows
            if row["document_id"] not in observed_ids
        ]

        for document_id in missing_ids:

            connection.execute(
                """
                UPDATE documents
                SET
                    status = 'deleted',
                    processing_hash = NULL,
                    updated_at = ?
                WHERE document_id = ?
                """,
                (
                    utc_now(),
                    document_id
                )
            )

        return len(missing_ids)

def recover_interrupted_processing() -> int:

    with get_connection() as connection:

        cursor = connection.execute(
            """
            UPDATE documents
            SET
                status = 'pending',
                processing_hash = NULL,
                updated_at = ?
            WHERE status = 'processing'
            """,
            (utc_now(),)
        )

        return cursor.rowcount