import hashlib

from enum import Enum
from pathlib import Path

from src.storage.database import (
    get_document,
    observe_document
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
) -> tuple[str, ChangeStatus]:

    file_path = Path(file_path).resolve()
    input_directory = Path(input_directory).resolve()

    relative_path = file_path.relative_to(
        input_directory
    )

    document_id = (
        f"local:{relative_path.as_posix()}"
    )

    current_hash = calculate_file_hash(
        file_path
    )

    previous = get_document(document_id)

    if previous is None:
        change_status = ChangeStatus.NEW

    elif previous["status"] == "deleted":
        change_status = ChangeStatus.MODIFIED

    elif previous["observed_hash"] != current_hash:
        change_status = ChangeStatus.MODIFIED

    else:
        change_status = ChangeStatus.UNCHANGED

    observe_document(
        document_id=document_id,
        filename=file_path.name,
        observed_hash=current_hash
    )

    return document_id, change_status