from src.ingestion.change_detector import calculate_file_hash


def test_same_content_produces_same_hash(tmp_path):

    file_a = tmp_path / "document_a.txt"
    file_b = tmp_path / "document_b.txt"

    file_a.write_text("Hello SharePoint")
    file_b.write_text("Hello SharePoint")

    hash_a = calculate_file_hash(file_a)
    hash_b = calculate_file_hash(file_b)

    assert hash_a == hash_b


def test_different_content_produces_different_hash(tmp_path):

    file_a = tmp_path / "document_a.txt"
    file_b = tmp_path / "document_b.txt"

    file_a.write_text("Version 1")
    file_b.write_text("Version 2")

    hash_a = calculate_file_hash(file_a)
    hash_b = calculate_file_hash(file_b)

    assert hash_a != hash_b