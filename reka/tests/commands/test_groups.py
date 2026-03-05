# ABOUTME: Tests for the groups command group
# ABOUTME: Covers create, list, get, and delete

import json

import pytest
from typer.testing import CliRunner

from reka.main import app

runner = CliRunner()
BASE_ARGS = ["--token", "reka_test"]

SAMPLE_GROUP = {"group_id": "grp1", "name": "My Group"}
SAMPLE_GROUPS_RESPONSE = {"results": [SAMPLE_GROUP]}


class TestGroupsCreate:
    def test_creates_group_and_returns_json(self, monkeypatch):
        def fake_post(self_inner, path, **kwargs):
            return SAMPLE_GROUP

        monkeypatch.setattr("reka.client.RekaClient.post", fake_post)
        result = runner.invoke(app, BASE_ARGS + ["groups", "create", "--name", "My Group"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["group_id"] == "grp1"


class TestGroupsList:
    def test_returns_results_list(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_GROUPS_RESPONSE

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["groups", "list"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data == [SAMPLE_GROUP]


class TestGroupsGet:
    def test_returns_group(self, monkeypatch):
        def fake_get(self_inner, path, **kwargs):
            return SAMPLE_GROUP

        monkeypatch.setattr("reka.client.RekaClient.get", fake_get)
        result = runner.invoke(app, BASE_ARGS + ["groups", "get", "grp1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["group_id"] == "grp1"


class TestGroupsDelete:
    def test_outputs_success(self, monkeypatch):
        def fake_delete(self_inner, path, **kwargs):
            return {"status": "success", "message": "Video group deleted successfully"}

        monkeypatch.setattr("reka.client.RekaClient.delete", fake_delete)
        result = runner.invoke(app, BASE_ARGS + ["groups", "delete", "grp1"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["status"] == "success"
