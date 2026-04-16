from unittest.mock import patch
from execution.trade_executor import execute_trade

# quantity = risk_amount / 10000 = 1000 / 10000 = 0.1
_EXPECTED_QUANTITY = 0.1


@patch(
    "execution.trade_executor.place_order", return_value={"status": "filled"}
)
@patch("execution.trade_executor.apply_risk_management", return_value=1000)
@patch("execution.trade_executor.get_balance", return_value=10000)
def test_execute_trade_buy(mock_balance, mock_risk, mock_order):
    result = execute_trade("BUY")
    assert result == {"status": "filled"}
    mock_order.assert_called_once_with(side="BUY", quantity=_EXPECTED_QUANTITY)


@patch(
    "execution.trade_executor.place_order", return_value={"status": "filled"}
)
@patch("execution.trade_executor.apply_risk_management", return_value=1000)
@patch("execution.trade_executor.get_balance", return_value=10000)
def test_execute_trade_sell(mock_balance, mock_risk, mock_order):
    result = execute_trade("SELL")
    assert result == {"status": "filled"}
    mock_order.assert_called_once_with(
        side="SELL", quantity=_EXPECTED_QUANTITY
    )


@patch("execution.trade_executor.apply_risk_management", return_value=1000)
@patch("execution.trade_executor.get_balance", return_value=10000)
def test_execute_trade_hold(mock_balance, mock_risk):
    result = execute_trade("HOLD")
    assert result == "No trade"
