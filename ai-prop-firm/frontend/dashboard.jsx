import React, { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function Dashboard() {
  const [health, setHealth] = useState(null);
  const [trades, setTrades] = useState([]);
  const [form, setForm] = useState({
    symbol: "EURUSD",
    side: "BUY",
    volume: 0.01,
  });
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  const submitSignal = async (e) => {
    e.preventDefault();
    setMessage("");
    try {
      const res = await fetch(`${API_URL}/webhook/signal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      setMessage(data.status);
      setTrades((prev) => [{ ...form, status: data.status }, ...prev]);
    } catch {
      setMessage("Error sending signal");
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>AI Prop Firm Dashboard</h1>

      <section>
        <h2>System Status</h2>
        <p>
          Backend:{" "}
          <strong>{health ? health.status : "checking..."}</strong>
        </p>
      </section>

      <section>
        <h2>Send Trade Signal</h2>
        <form onSubmit={submitSignal}>
          <label>
            Symbol:{" "}
            <input
              value={form.symbol}
              onChange={(e) => setForm({ ...form, symbol: e.target.value })}
            />
          </label>
          <br />
          <label>
            Side:{" "}
            <select
              value={form.side}
              onChange={(e) => setForm({ ...form, side: e.target.value })}
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </label>
          <br />
          <label>
            Volume:{" "}
            <input
              type="number"
              step="0.01"
              value={form.volume}
              onChange={(e) =>
                setForm({ ...form, volume: parseFloat(e.target.value) })
              }
            />
          </label>
          <br />
          <button type="submit">Submit Signal</button>
        </form>
        {message && <p>Result: {message}</p>}
      </section>

      <section>
        <h2>Recent Trades</h2>
        {trades.length === 0 ? (
          <p>No trades yet.</p>
        ) : (
          <ul>
            {trades.map((t, i) => (
              <li key={i}>
                {t.side} {t.symbol} @ {t.volume} &mdash; {t.status}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

export default Dashboard;
