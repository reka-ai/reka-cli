# ABOUTME: Tests for output module — JSON/text formatting and exit code mapping
# ABOUTME: Verifies stdout/stderr routing and error serialization

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from reka.output import EXIT_CODES, ApiError, emit, emit_error


class TestExitCodes:
    def test_all_expected_codes_present(self):
        assert EXIT_CODES["authentication_error"] == 2
        assert EXIT_CODES["permission_error"] == 3
        assert EXIT_CODES["not_found_error"] == 4
        assert EXIT_CODES["validation_error"] == 5
        assert EXIT_CODES["rate_limit_error"] == 6
        assert EXIT_CODES["server_error"] == 7


class TestApiError:
    def test_stores_exit_code_and_error_data(self):
        err = ApiError(exit_code=4, error={"type": "not_found_error", "message": "not found"})
        assert err.exit_code == 4
        assert err.error["type"] == "not_found_error"

    def test_exit_code_defaults_to_7_for_unknown_type(self):
        err = ApiError.from_response({"error": {"type": "unknown_type", "message": "oops"}})
        assert err.exit_code == 7

    def test_maps_known_error_type_to_correct_code(self):
        err = ApiError.from_response({"error": {"type": "not_found_error", "message": "nope"}})
        assert err.exit_code == 4


class TestEmit:
    def test_json_format_writes_to_stdout(self, capsys):
        emit({"video_id": "abc"}, format="json", output_file=None)
        out = capsys.readouterr().out
        assert json.loads(out) == {"video_id": "abc"}

    def test_json_list_writes_to_stdout(self, capsys):
        emit([{"id": "1"}, {"id": "2"}], format="json", output_file=None)
        out = capsys.readouterr().out
        assert json.loads(out) == [{"id": "1"}, {"id": "2"}]

    def test_writes_to_file_when_output_file_given(self, tmp_path):
        out_file = tmp_path / "out.json"
        emit({"video_id": "abc"}, format="json", output_file=str(out_file))
        assert json.loads(out_file.read_text()) == {"video_id": "abc"}

    def test_text_format_does_not_crash(self, capsys):
        # text format renders a table — just verify it doesn't crash and prints something
        emit({"video_id": "abc", "status": "indexed"}, format="text", output_file=None)
        out = capsys.readouterr().out
        assert len(out) > 0


class TestEmitError:
    def test_writes_json_to_stderr(self, capsys):
        emit_error({"type": "not_found_error", "message": "Video not found"})
        err = capsys.readouterr().err
        data = json.loads(err)
        assert data["error"]["type"] == "not_found_error"

    def test_nothing_on_stdout(self, capsys):
        emit_error({"type": "server_error", "message": "oops"})
        out = capsys.readouterr().out
        assert out == ""
