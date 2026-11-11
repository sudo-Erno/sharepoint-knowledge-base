import hashlib
from pathlib import Path
from enum import Enum

from src.storage.database import (
    get_document,
    save_document
)

class ChangeStatus(str, Enum):
    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"

def calculate_file_hash(file_path: str | Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the document.

    Returns:
        SHA-256 hexadecimal digest.
    """

    file_path = Path(file_path)

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(8192):
            sha256.update(chunk)

    return sha256.hexdigest()


def check_document(
    file_path: str | Path,
    input_directory: str | Path = "data/input"
) -> ChangeStatus:

    file_path = Path(file_path).resolve()

    input_directory = Path(
        input_directory
    ).resolve()

    relative_path = file_path.relative_to(
        input_directory
    )

    document_id = (
        f"local:{relative_path.as_posix()}"
    )

    current_hash = calculate_file_hash(
        file_path
    )

    stored_document = get_document(
        document_id
    )

    if stored_document is None:

        save_document(
            document_id=document_id,
            filename=file_path.name,
            file_hash=current_hash,
            status="pending"
        )

        return ChangeStatus.NEW

    stored_hash = stored_document["file_hash"]

    if current_hash != stored_hash:

        save_document(
            document_id=document_id,
            filename=file_path.name,
            file_hash=current_hash,
            status="pending"
        )

        return ChangeStatus.MODIFIED

    return ChangeStatus.UNCHANGED