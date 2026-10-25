from storage import load_records, save_records


def test_save_and_load(tmp_path):
    filename = tmp_path / "expenses.json"
    save_records(filename, [{"id": 1, "title": "Ужин"}])
    assert load_records(filename) == [{"id": 1, "title": "Ужин"}]


def test_load_missing_file(tmp_path):
    assert load_records(tmp_path / "nope.json") == []


def test_load_broken_file(tmp_path):
    filename = tmp_path / "broken.json"
    filename.write_text("{не json", encoding="utf-8")
    assert load_records(filename) == []
