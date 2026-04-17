"""Checkpoint management service and Flask API for AI model states.

Provides file-based checkpoint storage for saving, loading, listing, and
deleting model snapshots produced during training and retraining cycles.
"""

import json
import os
import pickle
import threading
import time
from pathlib import Path

from flask import Blueprint, jsonify, request
from langgraph.checkpoint.memory import InMemorySaver

# ---------------------------------------------------------------------------
# Default storage directory
# ---------------------------------------------------------------------------

DEFAULT_CHECKPOINT_DIR = os.getenv(
    "CHECKPOINT_DIR",
    os.path.join(os.path.dirname(__file__), os.pardir, "data", "checkpoints"),
)

# Maximum number of checkpoints to keep per model (0 = unlimited)
MAX_CHECKPOINTS_PER_MODEL = int(os.getenv("MAX_CHECKPOINTS_PER_MODEL", "10"))


# ---------------------------------------------------------------------------
# CheckpointerService
# ---------------------------------------------------------------------------


class CheckpointerService:
    """Manage model checkpoint files on disk.

    Each checkpoint is stored as a pair of files under
    ``<checkpoint_dir>/<model_name>/``:

    * ``<version>.pkl``  – serialised model data (pickle)
    * ``<version>.meta.json`` – human-readable metadata
    """

    def __init__(self, checkpoint_dir=None, max_kept=None):
        self.checkpoint_dir = Path(
            checkpoint_dir or DEFAULT_CHECKPOINT_DIR
        ).resolve()
        self.max_kept = (
            max_kept if max_kept is not None else MAX_CHECKPOINTS_PER_MODEL
        )
        self._version_lock = threading.Lock()
        self._last_version = 0
        self.saver = InMemorySaver()

    def get_saver(self):
        """Return a LangGraph-compatible ``BaseCheckpointSaver``.

        LangGraph's ``workflow.compile(checkpointer=...)`` requires an
        instance of ``BaseCheckpointSaver``.  This wrapper is **not** a
        ``BaseCheckpointSaver`` itself, so pass ``get_saver()`` instead::

            manager = CheckpointerService()
            graph = workflow.compile(checkpointer=manager.get_saver())

        .. note::

           The returned ``InMemorySaver`` manages LangGraph **graph
           execution state** independently of the file-based model
           checkpoints stored by the other methods on this class.
        """
        return self.saver

    # -- helpers -------------------------------------------------------------

    def _model_dir(self, model_name):
        """Return (and create) the directory for *model_name*."""
        d = self.checkpoint_dir / model_name
        d.mkdir(parents=True, exist_ok=True)
        return d

    @staticmethod
    def _version_key(version):
        """Sort key so versions are ordered chronologically."""
        try:
            return float(version)
        except (TypeError, ValueError):
            return 0.0

    # -- core API ------------------------------------------------------------

    def save(self, model_name, data, metadata=None):
        """Persist a checkpoint and return its version string.

        Parameters
        ----------
        model_name : str
            Identifier for the model (e.g. ``"rl_agent"``).
        data : object
            Picklable model state (weights, parameters, …).
        metadata : dict, optional
            Extra information stored alongside the checkpoint.

        Returns
        -------
        str
            The version identifier (Unix timestamp).
        """
        with self._version_lock:
            timestamp_ms = int(time.time() * 1000)
            if timestamp_ms <= self._last_version:
                timestamp_ms = self._last_version + 1
            self._last_version = timestamp_ms
        version = str(timestamp_ms)
        model_dir = self._model_dir(model_name)

        data_path = model_dir / f"{version}.pkl"
        meta_path = model_dir / f"{version}.meta.json"

        meta = {
            "model_name": model_name,
            "version": version,
            "created_at": time.time(),
            **(metadata or {}),
        }

        with open(data_path, "wb") as fh:
            pickle.dump(data, fh)

        with open(meta_path, "w") as fh:
            json.dump(meta, fh, indent=2)

        self._enforce_retention(model_name)

        return version

    def load(self, model_name, version=None):
        """Load a checkpoint's data.

        Parameters
        ----------
        model_name : str
        version : str, optional
            If *None*, the latest checkpoint is loaded.

        Returns
        -------
        object
            The deserialised model state.

        Raises
        ------
        FileNotFoundError
            If the requested checkpoint does not exist.
        """
        if version is None:
            version = self.get_latest_version(model_name)

        data_path = self._model_dir(model_name) / f"{version}.pkl"
        if not data_path.exists():
            raise FileNotFoundError(
                f"Checkpoint {version} not found for model '{model_name}'"
            )

        with open(data_path, "rb") as fh:
            return pickle.load(fh)  # noqa: S301

    def get_metadata(self, model_name, version):
        """Return the metadata dict for a specific checkpoint."""
        meta_path = self._model_dir(model_name) / f"{version}.meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(
                f"Metadata for checkpoint {version} not found "
                f"for model '{model_name}'"
            )
        with open(meta_path, "r") as fh:
            return json.load(fh)

    def list_checkpoints(self, model_name):
        """Return metadata dicts for every checkpoint of *model_name*,
        sorted oldest-first."""
        model_dir = self._model_dir(model_name)
        metas = []
        for meta_file in sorted(model_dir.glob("*.meta.json")):
            with open(meta_file, "r") as fh:
                metas.append(json.load(fh))
        metas.sort(key=lambda m: self._version_key(m.get("version")))
        return metas

    def delete(self, model_name, version):
        """Remove a single checkpoint (data + metadata)."""
        model_dir = self._model_dir(model_name)
        data_path = model_dir / f"{version}.pkl"
        meta_path = model_dir / f"{version}.meta.json"

        if not data_path.exists() and not meta_path.exists():
            raise FileNotFoundError(
                f"Checkpoint {version} not found for model '{model_name}'"
            )

        if data_path.exists():
            data_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

    def get_latest_version(self, model_name):
        """Return the version string of the most recent checkpoint.

        Raises
        ------
        FileNotFoundError
            If no checkpoints exist for *model_name*.
        """
        checkpoints = self.list_checkpoints(model_name)
        if not checkpoints:
            raise FileNotFoundError(
                f"No checkpoints found for model '{model_name}'"
            )
        return checkpoints[-1]["version"]

    def _enforce_retention(self, model_name):
        """Delete oldest checkpoints that exceed *max_kept*."""
        if self.max_kept <= 0:
            return
        checkpoints = self.list_checkpoints(model_name)
        while len(checkpoints) > self.max_kept:
            oldest = checkpoints.pop(0)
            self.delete(model_name, oldest["version"])


# ---------------------------------------------------------------------------
# Flask Blueprint
# ---------------------------------------------------------------------------

checkpointer_bp = Blueprint(
    "checkpointer", __name__, url_prefix="/checkpoints"
)

# Module-level service instance used by the blueprint.
_service = CheckpointerService()


def get_service():
    """Return the module-level :class:`CheckpointerService`."""
    return _service


@checkpointer_bp.route("/<model_name>", methods=["POST"])
def save_checkpoint(model_name):
    """Save a new checkpoint for *model_name*.

    Expects JSON body with:
    * ``data`` – the model state (stored as-is via pickle)
    * ``metadata`` – (optional) extra info
    """
    body = request.get_json(force=True)
    if body is None or "data" not in body:
        return (
            jsonify({"error": "Request body must contain 'data'"}),
            400,
        )

    version = _service.save(
        model_name,
        body["data"],
        metadata=body.get("metadata"),
    )
    return jsonify({"model_name": model_name, "version": version}), 201


@checkpointer_bp.route("/<model_name>", methods=["GET"])
def list_checkpoints(model_name):
    """List all checkpoints for *model_name*."""
    checkpoints = _service.list_checkpoints(model_name)
    return jsonify({"model_name": model_name, "checkpoints": checkpoints})


@checkpointer_bp.route("/<model_name>/latest", methods=["GET"])
def get_latest_checkpoint(model_name):
    """Return metadata for the most recent checkpoint."""
    try:
        version = _service.get_latest_version(model_name)
        meta = _service.get_metadata(model_name, version)
        return jsonify(meta)
    except FileNotFoundError:
        return jsonify({"error": "Checkpoint not found"}), 404


@checkpointer_bp.route("/<model_name>/<version>", methods=["GET"])
def get_checkpoint_metadata(model_name, version):
    """Return metadata for a specific checkpoint."""
    try:
        meta = _service.get_metadata(model_name, version)
        return jsonify(meta)
    except FileNotFoundError:
        return jsonify({"error": "Checkpoint not found"}), 404


@checkpointer_bp.route("/<model_name>/<version>", methods=["DELETE"])
def delete_checkpoint(model_name, version):
    """Delete a specific checkpoint."""
    try:
        _service.delete(model_name, version)
        return jsonify({"deleted": True, "version": version})
    except FileNotFoundError:
        return jsonify({"error": "Checkpoint not found"}), 404
