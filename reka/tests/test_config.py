# ABOUTME: Tests for config module — token resolution, URL derivation, file read/write
# ABOUTME: Covers priority order: CLI flag > env var > config file

import json
import os
from pathlib import Path

import pytest

from reka.config import (
    BASE_URLS,
    Config,
    load_config,
    resolve_base_url,
    resolve_token,
    save_config,
)


@pytest.fixture
def config_file(tmp_path):
    """Returns a config file path within a temp directory."""
    return tmp_path / "config.json"


class TestLoadConfig:
    def test_returns_empty_config_when_file_missing(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.json")
        assert config == Config()

    def test_reads_token_and_env(self, config_file):
        config_file.write_text(json.dumps({"token": "reka_saved", "env": "staging"}))
        config = load_config(config_file)
        assert config.token == "reka_saved"
        assert config.env == "staging"

    def test_handles_missing_fields_gracefully(self, config_file):
        config_file.write_text(json.dumps({"token": "reka_tok"}))
        config = load_config(config_file)
        assert config.token == "reka_tok"
        assert config.env == "prod"

    def test_handles_corrupted_file(self, config_file):
        config_file.write_text("not valid json{{{")
        config = load_config(config_file)
        assert config == Config()


class TestSaveConfig:
    def test_creates_file_and_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "config.json"
        save_config(Config(token="reka_tok", env="staging"), path)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["token"] == "reka_tok"
        assert data["env"] == "staging"

    def test_overwrites_existing_file(self, config_file):
        config_file.write_text(json.dumps({"token": "old"}))
        save_config(Config(token="new_tok"), config_file)
        data = json.loads(config_file.read_text())
        assert data["token"] == "new_tok"


class TestResolveToken:
    def test_cli_flag_takes_priority_over_all(self, config_file, monkeypatch):
        monkeypatch.setenv("REKA_API_TOKEN", "env_token")
        config_file.write_text(json.dumps({"token": "file_token"}))
        assert resolve_token("cli_token", config_file) == "cli_token"

    def test_env_var_takes_priority_over_file(self, config_file, monkeypatch):
        monkeypatch.setenv("REKA_API_TOKEN", "env_token")
        config_file.write_text(json.dumps({"token": "file_token"}))
        assert resolve_token(None, config_file) == "env_token"

    def test_file_token_used_when_no_flag_or_env(self, config_file, monkeypatch):
        monkeypatch.delenv("REKA_API_TOKEN", raising=False)
        config_file.write_text(json.dumps({"token": "file_token"}))
        assert resolve_token(None, config_file) == "file_token"

    def test_returns_none_when_no_token_anywhere(self, tmp_path, monkeypatch):
        monkeypatch.delenv("REKA_API_TOKEN", raising=False)
        assert resolve_token(None, tmp_path / "nonexistent.json") is None


class TestResolveBaseUrl:
    def test_env_var_overrides_derived_url(self, monkeypatch):
        monkeypatch.setenv("REKA_BASE_URL", "https://custom.example.com")
        assert resolve_base_url(None, "prod") == "https://custom.example.com"

    def test_explicit_base_url_takes_priority(self, monkeypatch):
        monkeypatch.setenv("REKA_BASE_URL", "https://env.example.com")
        assert resolve_base_url("https://flag.example.com", "prod") == "https://flag.example.com"

    def test_prod_env_maps_to_prod_url(self, monkeypatch):
        monkeypatch.delenv("REKA_BASE_URL", raising=False)
        assert resolve_base_url(None, "prod") == BASE_URLS["prod"]

    def test_staging_env_maps_to_staging_url(self, monkeypatch):
        monkeypatch.delenv("REKA_BASE_URL", raising=False)
        assert resolve_base_url(None, "staging") == BASE_URLS["staging"]
