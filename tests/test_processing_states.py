import pytest

from src.storage import database


@pytest.fixture
def test_db(tmp_path, monkeypatch):

    db_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        db_path
    )

    database.initialize_database()

    return db_path


def test_new_document_requires_processing(test_db):

    database.observe_document(
        document_id="local:test.txt",
        filename="test.txt",
        observed_hash="hash_v1"
    )

    assert database.should_process(
        "local:test.txt"
    ) is True


def test_completed_document_is_skipped(test_db):

    document_id = "local:test.txt"

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v1"
    )

    processing_hash = database.start_processing(
        document_id
    )

    assert processing_hash == "hash_v1"

    assert database.complete_processing(
        document_id,
        processing_hash
    ) is True

    assert database.should_process(
        document_id
    ) is False


def test_modified_document_requires_processing(test_db):

    document_id = "local:test.txt"

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v1"
    )

    processing_hash = database.start_processing(
        document_id
    )

    database.complete_processing(
        document_id,
        processing_hash
    )

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v2"
    )

    assert database.should_process(
        document_id
    ) is True


def test_failed_document_can_retry(test_db):

    document_id = "local:test.txt"

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v1"
    )

    processing_hash = database.start_processing(
        document_id
    )

    database.fail_processing(
        document_id,
        processing_hash,
        "Simulated LLM error"
    )

    document = database.get_document(
        document_id
    )

    assert document["status"] == "failed"

    assert document["retry_count"] == 1

    assert database.should_process(
        document_id
    ) is True


def test_document_changes_during_processing(test_db):

    document_id = "local:test.txt"

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v1"
    )

    processing_hash = database.start_processing(
        document_id
    )

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v2"
    )

    database.complete_processing(
        document_id,
        processing_hash
    )

    document = database.get_document(
        document_id
    )

    assert document["processed_hash"] == "hash_v1"

    assert document["observed_hash"] == "hash_v2"

    assert document["status"] == "pending"

    assert database.should_process(
        document_id
    ) is True

def test_recover_interrupted_processing(test_db):

    document_id = "local:test.txt"

    database.observe_document(
        document_id,
        "test.txt",
        "hash_v1"
    )

    database.start_processing(
        document_id
    )

    recovered = database.recover_interrupted_processing()

    document = database.get_document(
        document_id
    )

    assert recovered == 1

    assert document["status"] == "pending"

    assert document["processing_hash"] is None

    assert database.should_process(
        document_id
    ) is True