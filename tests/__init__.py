import sys
from unittest.mock import MagicMock

# Mock heavy external dependencies before any project modules are imported
_binance_mock = MagicMock()
sys.modules.setdefault("binance", _binance_mock)
sys.modules.setdefault("binance.client", _binance_mock)

_torch_mock = MagicMock()
sys.modules.setdefault("torch", _torch_mock)

_transformers_mock = MagicMock()
sys.modules.setdefault("transformers", _transformers_mock)
