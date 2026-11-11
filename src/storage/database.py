import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = Path("data/state/knowledge.db")

def initialize_database() -> None:

    with get_connection() as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                document_id TEXT NOT NULL UNIQUE,

                filename TEXT NOT NULL,

                file_hash TEXT NOT NULL,

                status TEXT NOT NULL,

                updated_at TEXT NOT NULL

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

    connection = sqlite3.connect(DATABASE_PATH)

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