"""
Este módulo será responsable de:
1. Verificar si un documento necesita procesamiento.
2. Reservar su versión.
3. Ejecutar el procesador.
4. Registrar éxito o error.
"""
from pathlib import Path

from src.ingestion.change_detector import (
    calculate_file_hash
)

from src.storage.database import (
    should_process,
    start_processing,
    complete_processing,
    fail_processing
)


def simulate_processing(file_path: Path) -> None:

    content = file_path.read_bytes()

    print(
        f"    Simulating processing: "
        f"{len(content)} bytes"
    )

def process_document(
    document_id: str,
    file_path: Path
) -> bool:

    if not should_process(document_id):

        print(f"[SKIP] {document_id}")

        return False

    processing_hash = start_processing(
        document_id
    )

    if processing_hash is None:
        return False

    try:

        current_hash = calculate_file_hash(
            file_path
        )

        if current_hash != processing_hash:
            raise RuntimeError(
                "File changed before processing started"
            )

        simulate_processing(file_path)

        final_hash = calculate_file_hash(
            file_path
        )

        if final_hash != processing_hash:
            raise RuntimeError(
                "File changed during processing"
            )

        completed = complete_processing(
            document_id,
            processing_hash
        )

        if not completed:
            raise RuntimeError(
                "Could not confirm processing completion"
            )

        print(f"[COMPLETED] {document_id}")

        return True

    except Exception as error:

        fail_processing(
            document_id,
            processing_hash,
            str(error)
        )

        print(
            f"[FAILED] {document_id}: {error}"
        )

        return False