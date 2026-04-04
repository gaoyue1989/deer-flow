"""Tests for file helper utilities."""

import json
import tempfile
from pathlib import Path

import pytest

from deerflow.utils.file_helpers import atomic_write_json, atomic_write_text


class TestAtomicWriteJson:
    def test_write_and_read_json(self, tmp_path):
        """Test writing and reading JSON data."""
        test_path = tmp_path / "test.json"
        data = {"key": "value", "nested": {"a": 1}}
        atomic_write_json(test_path, data)
        with open(test_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_write_json_creates_file(self, tmp_path):
        """Test that atomic_write_json creates the file."""
        test_path = tmp_path / "new.json"
        assert not test_path.exists()
        atomic_write_json(test_path, {"test": True})
        assert test_path.exists()

    def test_write_json_overwrites(self, tmp_path):
        """Test that atomic_write_json overwrites existing file."""
        test_path = tmp_path / "overwrite.json"
        atomic_write_json(test_path, {"old": "data"})
        atomic_write_json(test_path, {"new": "data"})
        with open(test_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == {"new": "data"}

    def test_write_json_unicode(self, tmp_path):
        """Test writing JSON with unicode characters."""
        test_path = tmp_path / "unicode.json"
        data = {"message": "你好世界", "emoji": "🎉"}
        atomic_write_json(test_path, data)
        with open(test_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["message"] == "你好世界"

    def test_write_json_list(self, tmp_path):
        """Test writing JSON list data."""
        test_path = tmp_path / "list.json"
        data = [1, 2, 3, {"a": "b"}]
        atomic_write_json(test_path, data)
        with open(test_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_write_json_non_serializable_raises(self, tmp_path):
        """Test that non-serializable data raises an exception."""
        test_path = tmp_path / "bad.json"
        with pytest.raises(TypeError):
            atomic_write_json(test_path, {"key": set()})
        assert not test_path.exists()


class TestAtomicWriteText:
    def test_write_and_read_text(self, tmp_path):
        """Test writing and reading text content."""
        test_path = tmp_path / "test.txt"
        content = "Hello, World!"
        atomic_write_text(test_path, content)
        assert test_path.read_text(encoding="utf-8") == content

    def test_write_text_creates_file(self, tmp_path):
        """Test that atomic_write_text creates the file."""
        test_path = tmp_path / "new.txt"
        assert not test_path.exists()
        atomic_write_text(test_path, "content")
        assert test_path.exists()

    def test_write_text_overwrites(self, tmp_path):
        """Test that atomic_write_text overwrites existing file."""
        test_path = tmp_path / "overwrite.txt"
        atomic_write_text(test_path, "old content")
        atomic_write_text(test_path, "new content")
        assert test_path.read_text(encoding="utf-8") == "new content"

    def test_write_text_unicode(self, tmp_path):
        """Test writing text with unicode characters."""
        test_path = tmp_path / "unicode.txt"
        content = "你好世界 🎉"
        atomic_write_text(test_path, content)
        assert test_path.read_text(encoding="utf-8") == content

    def test_write_text_multiline(self, tmp_path):
        """Test writing multiline text."""
        test_path = tmp_path / "multiline.txt"
        content = "line1\nline2\nline3"
        atomic_write_text(test_path, content)
        assert test_path.read_text(encoding="utf-8") == content

    def test_write_text_empty(self, tmp_path):
        """Test writing empty string."""
        test_path = tmp_path / "empty.txt"
        atomic_write_text(test_path, "")
        assert test_path.read_text(encoding="utf-8") == ""

    def test_no_temp_file_left_after_write(self, tmp_path):
        """Test that no .tmp files are left after successful write."""
        test_path = tmp_path / "clean.txt"
        atomic_write_text(test_path, "content")
        tmp_files = list(tmp_path.glob("*.tmp"))
        assert len(tmp_files) == 0
