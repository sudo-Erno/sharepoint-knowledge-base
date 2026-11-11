from pathlib import Path

from src.storage.database import (
    initialize_database
)

from src.ingestion.change_detector import (
    check_document,
    ChangeStatus
)


def main():

    print("SharePoint Knowledge Engine")
    print("---------------------------")

    initialize_database()

    input_directory = Path("data/input")

    files = [
        path
        for path in input_directory.rglob("*")
        if path.is_file()
    ]

    counters = {
        ChangeStatus.NEW: 0,
        ChangeStatus.MODIFIED: 0,
        ChangeStatus.UNCHANGED: 0
    }

    for file_path in files:

        status = check_document(
            file_path,
            input_directory
        )

        counters[status] += 1

        print(
            f"[{status.value.upper()}] "
            f"{file_path.relative_to(input_directory)}"
        )

    print("\nSummary")
    print("-------")

    print(
        f"New documents: "
        f"{counters[ChangeStatus.NEW]}"
    )

    print(
        f"Modified documents: "
        f"{counters[ChangeStatus.MODIFIED]}"
    )

    print(
        f"Unchanged documents: "
        f"{counters[ChangeStatus.UNCHANGED]}"
    )


if __name__ == "__main__":
    main()