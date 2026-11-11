from pathlib import Path

from src.storage.database import (
    initialize_database,
    recover_interrupted_processing,
    mark_missing_documents,
    get_document
)

from src.ingestion.change_detector import (
    check_document,
    ChangeStatus
)

from src.ingestion.processing_engine import (
    process_document
)


def main():

    print("\nSharePoint Knowledge Engine")
    print("=" * 40)

    initialize_database()

    recovered = recover_interrupted_processing()

    if recovered:
        print(f"[RECOVERY] {recovered} interrupted jobs")

    input_directory = Path("data/input")

    input_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    files = sorted(
        path
        for path in input_directory.rglob("*")
        if path.is_file()
    )

    observed_ids = set()

    counters = {
        ChangeStatus.NEW: 0,
        ChangeStatus.MODIFIED: 0,
        ChangeStatus.UNCHANGED: 0
    }

    print("\nScanning documents...\n")

    for file_path in files:

        document_id, status = check_document(
            file_path,
            input_directory
        )

        observed_ids.add(document_id)

        counters[status] += 1

        print(
            f"[{status.value.upper()}] "
            f"{file_path.relative_to(input_directory)}"
        )

    deleted_count = mark_missing_documents(
        observed_ids
    )

    print("\nProcessing documents...\n")

    processed_count = 0

    for file_path in files:

        relative_path = file_path.relative_to(
            input_directory
        )

        document_id = (
            f"local:{relative_path.as_posix()}"
        )

        if process_document(
            document_id,
            file_path
        ):
            processed_count += 1

    print("\nExecution summary")
    print("-" * 40)

    print(f"New: {counters[ChangeStatus.NEW]}")

    print(
        f"Modified: "
        f"{counters[ChangeStatus.MODIFIED]}"
    )

    print(
        f"Unchanged: "
        f"{counters[ChangeStatus.UNCHANGED]}"
    )

    print(f"Deleted: {deleted_count}")

    print(f"Successfully processed: {processed_count}")


if __name__ == "__main__":
    main()