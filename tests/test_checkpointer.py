"""Tests for the checkpointer API service."""

import json
import tempfile

import pytest

from services.checkpointer_api import CheckpointerService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_dir():
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture()
def svc(tmp_dir):
    """Provide a fresh :class:`CheckpointerService` using a temp directory."""
    return CheckpointerService(checkpoint_dir=tmp_dir, max_kept=0)


# ---------------------------------------------------------------------------
# CheckpointerService — core operations
# ---------------------------------------------------------------------------


class TestSaveAndLoad:
    def test_save_returns_version(self, svc):
        version = svc.save("test_model", {"weights": [1, 2, 3]})
        assert version is not None
        assert isinstance(version, str)

    def test_load_returns_saved_data(self, svc):
        data = {"weights": [4, 5, 6]}
        version = svc.save("test_model", data)
        loaded = svc.load("test_model", version)
        assert loaded == data

    def test_load_latest(self, svc):
        svc.save("test_model", {"v": 1})
        svc.save("test_model", {"v": 2})
        loaded = svc.load("test_model")
        assert loaded == {"v": 2}

    def test_load_nonexistent_raises(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.load("test_model", "999999")

    def test_load_no_checkpoints_raises(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.load("empty_model")


class TestMetadata:
    def test_default_metadata(self, svc):
        version = svc.save("m", {"x": 1})
        meta = svc.get_metadata("m", version)
        assert meta["model_name"] == "m"
        assert meta["version"] == version
        assert "created_at" in meta

    def test_custom_metadata(self, svc):
        version = svc.save("m", {}, metadata={"epoch": 10, "loss": 0.05})
        meta = svc.get_metadata("m", version)
        assert meta["epoch"] == 10
        assert meta["loss"] == 0.05

    def test_metadata_nonexistent_raises(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.get_metadata("m", "0")


class TestListCheckpoints:
    def test_empty_list(self, svc):
        result = svc.list_checkpoints("no_model")
        assert result == []

    def test_lists_in_order(self, svc):
        v1 = svc.save("m", {"v": 1})
        v2 = svc.save("m", {"v": 2})
        items = svc.list_checkpoints("m")
        versions = [i["version"] for i in items]
        assert versions == sorted(versions, key=float)
        assert v1 in versions
        assert v2 in versions


class TestDeleteCheckpoint:
    def test_delete_existing(self, svc):
        version = svc.save("m", {"x": 1})
        svc.delete("m", version)
        assert svc.list_checkpoints("m") == []

    def test_delete_nonexistent_raises(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.delete("m", "missing")


class TestRetention:
    def test_max_kept_enforced(self, tmp_dir):
        svc = CheckpointerService(checkpoint_dir=tmp_dir, max_kept=2)
        svc.save("m", {"v": 1})
        svc.save("m", {"v": 2})
        svc.save("m", {"v": 3})
        items = svc.list_checkpoints("m")
        assert len(items) == 2
        # Oldest should have been pruned; newest two remain
        assert items[-1]["version"] is not None

    def test_unlimited_retention(self, tmp_dir):
        svc = CheckpointerService(checkpoint_dir=tmp_dir, max_kept=0)
        for i in range(5):
            svc.save("m", {"v": i})
        assert len(svc.list_checkpoints("m")) == 5


class TestGetLatestVersion:
    def test_latest_version(self, svc):
        svc.save("m", {"v": 1})
        v2 = svc.save("m", {"v": 2})
        assert svc.get_latest_version("m") == v2

    def test_latest_version_no_checkpoints(self, svc):
        with pytest.raises(FileNotFoundError):
            svc.get_latest_version("empty")


class TestGetSaver:
    def test_get_saver_returns_in_memory_saver(self, svc):
        from langgraph.checkpoint.memory import InMemorySaver
        saver = svc.get_saver()
        assert isinstance(saver, InMemorySaver)

    def test_get_saver_returns_same_instance(self, svc):
        assert svc.get_saver() is svc.get_saver()


# ---------------------------------------------------------------------------
# Flask blueprint
# ---------------------------------------------------------------------------


@pytest.fixture()
def flask_client(tmp_dir):
    """Provide a Flask test client with the checkpointer blueprint."""
    from flask import Flask

    from services.checkpointer_api import checkpointer_bp, _service

    # Point the module-level service at our temp directory
    _service.__init__(checkpoint_dir=tmp_dir, max_kept=0)

    app = Flask(__name__)
    app.register_blueprint(checkpointer_bp)
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestFlaskSave:
    def test_save_success(self, flask_client):
        resp = flask_client.post(
            "/checkpoints/my_model",
            data=json.dumps({"data": {"w": [1]}}),
            content_type="application/json",
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["model_name"] == "my_model"
        assert "version" in body

    def test_save_missing_data(self, flask_client):
        resp = flask_client.post(
            "/checkpoints/my_model",
            data=json.dumps({"metadata": {}}),
            content_type="application/json",
        )
        assert resp.status_code == 400


class TestFlaskList:
    def test_list_empty(self, flask_client):
        resp = flask_client.get("/checkpoints/my_model")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["checkpoints"] == []

    def test_list_after_save(self, flask_client):
        flask_client.post(
            "/checkpoints/my_model",
            data=json.dumps({"data": {"w": 1}}),
            content_type="application/json",
        )
        resp = flask_client.get("/checkpoints/my_model")
        body = resp.get_json()
        assert len(body["checkpoints"]) == 1


class TestFlaskLatest:
    def test_latest_not_found(self, flask_client):
        resp = flask_client.get("/checkpoints/my_model/latest")
        assert resp.status_code == 404

    def test_latest_success(self, flask_client):
        flask_client.post(
            "/checkpoints/my_model",
            data=json.dumps({"data": {"w": 1}}),
            content_type="application/json",
        )
        resp = flask_client.get("/checkpoints/my_model/latest")
        assert resp.status_code == 200
        assert resp.get_json()["model_name"] == "my_model"


class TestFlaskGetMeta:
    def test_get_meta_not_found(self, flask_client):
        resp = flask_client.get("/checkpoints/my_model/000")
        assert resp.status_code == 404

    def test_get_meta_success(self, flask_client):
        post_resp = flask_client.post(
            "/checkpoints/my_model",
            data=json.dumps({"data": {"w": 1}}),
            content_type="application/json",
        )
        version = post_resp.get_json()["version"]
        resp = flask_client.get(f"/checkpoints/my_model/{version}")
        assert resp.status_code == 200


class TestFlaskDelete:
    def test_delete_not_found(self, flask_client):
        resp = flask_client.delete("/checkpoints/my_model/000")
        assert resp.status_code == 404

    def test_delete_success(self, flask_client):
        post_resp = flask_client.post(
            "/checkpoints/my_model",
            data=json.dumps({"data": {"w": 1}}),
            content_type="application/json",
        )
        version = post_resp.get_json()["version"]
        resp = flask_client.delete(f"/checkpoints/my_model/{version}")
        assert resp.status_code == 200
        assert resp.get_json()["deleted"] is True
