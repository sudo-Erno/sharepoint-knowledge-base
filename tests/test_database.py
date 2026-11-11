from src.storage import database


def test_save_and_get_document(
    tmp_path,
    monkeypatch
):

    test_database = (
        tmp_path / "test_knowledge.db"
    )

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        test_database
    )

    database.initialize_database()

    database.save_document(
        document_id="local:test.txt",
        filename="test.txt",
        file_hash="abc123",
        status="pending"
    )

    document = database.get_document(
        "local:test.txt"
    )

    assert document is not None

    assert document["filename"] == "test.txt"

    assert document["file_hash"] == "abc123"

    assert document["status"] == "pending"