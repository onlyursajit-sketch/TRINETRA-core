import { useEffect, useState } from "react";
import "./App.css";

import {
  fetchMarketContext,
  fetchMarketDecision,
  fetchProviderHealth,
  fetchOptionChain,
} from "./services/api";

function App() {
  const [symbol, setSymbol] = useState(() => {
    return localStorage.getItem("trinetra:symbol") || "NIFTY";
  });
  const [context, setContext] = useState(null);
  const [decision, setDecision] = useState(null);
  const [providers, setProviders] = useState(null);
  const [optionChain, setOptionChain] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  const [lastUpdated, setLastUpdated] = useState(() => {
    const saved = localStorage.getItem("trinetra:lastUpdated");
    return saved ? new Date(saved) : null;
  });
  const [autoRefresh, setAutoRefresh] = useState(() => {
    return localStorage.getItem("trinetra:autoRefresh") === "true";
  });

  useEffect(() => {
    localStorage.setItem(
      "trinetra:autoRefresh",
      String(autoRefresh)
    );
  }, [autoRefresh]);

  useEffect(() => {
    localStorage.setItem("trinetra:symbol", symbol);
  }, [symbol]);

  useEffect(() => {
    if (!autoRefresh) {
      return undefined;
    }

    const timer = setInterval(() => {
      setRefreshKey((value) => value + 1);
    }, 30000);

    return () => clearInterval(timer);
  }, [autoRefresh]);

  useEffect(() => {
    async function loadDashboard() {
      try {
        setError("");
        setLoading(true);

      const [
        contextData,
        decisionData,
        providerData,
        optionChainData,
      ] = await Promise.all([
        fetchMarketContext(symbol),
        fetchMarketDecision(symbol),
        fetchProviderHealth(),
        fetchOptionChain(symbol),
      ]);

        setContext(contextData);
        setDecision(decisionData);
        setProviders(providerData);
      setOptionChain(optionChainData);
        const updatedAt = new Date();
      setLastUpdated(updatedAt);
      localStorage.setItem(
        "trinetra:lastUpdated",
        updatedAt.toISOString()
      );
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    }

    loadDashboard();
  }, [symbol]);

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">TRINETRA</p>
          <h1>Market Intelligence Dashboard</h1>

          <span
            className={`status ${
              loading
                ? "status-loading"
                : providers?.summary?.status === "HEALTHY"
                  ? "status-online"
                  : "status-warning"
            }`}
          >
            {loading
              ? "LOADING DATA"
              : providers?.summary?.status === "HEALTHY" &&
                  decision?.market_status !== "NO_DATA"
                ? "SYSTEM HEALTHY"
                : providers?.summary?.status === "HEALTHY"
                  ? "SYSTEM ONLINE · MARKET DATA LIMITED"
                  : "SYSTEM DEGRADED"}
          </span>
        </div>

        <div className="dashboard-controls">
          <select
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
          >
            <option value="NIFTY">NIFTY</option>
            <option value="BANKNIFTY">BANKNIFTY</option>
          </select>

          <button
            type="button"
            onClick={() => setRefreshKey((value) => value + 1)}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>

          <button
            type="button"
            onClick={() => setAutoRefresh((value) => !value)}
          >
            Auto Refresh: {autoRefresh ? "ON" : "OFF"}
          </button>

          <span className="updated-at">
            {lastUpdated
              ? `Updated ${lastUpdated.toLocaleTimeString()}`
              : "Not updated yet"}
          </span>
        </div>
      </header>

      {error && (
        <section className="error-box">
          <strong>Dashboard data unavailable</strong>
          <p>{error}</p>

          {lastUpdated && (
            <p className="stale-warning">
              Showing last successful data from{" "}
              {lastUpdated.toLocaleTimeString()}.
            </p>
          )}

          <button
            type="button"
            onClick={() => setRefreshKey((value) => value + 1)}
            disabled={loading}
          >
            {loading ? "Retrying..." : "Retry"}
          </button>
        </section>
      )}

      <section className="grid">
        <article className="card">
          <h2>Market Context</h2>
          <p>Symbol: {context?.symbol ?? "Loading..."}</p>
          <p>
            Confidence: {context?.confidence ?? "Loading..."}
          </p>
          <p>
            Regime: {context?.regime ?? "Loading..."}
          </p>
          <p>
            VIX: {context?.vix ?? "N/A"}
          </p>
          <p>
            Market Status:{" "}
            {decision?.market_status ?? "Loading..."}
          </p>
        </article>

        <article className="card">
          <h2>AI Decision</h2>
          <p>
            Decision: {decision?.decision ?? "Loading..."}
          </p>
          <p>
            Confidence:{" "}
            {decision?.confidence_score ?? "Loading..."}
          </p>
          <p>
            Risk: {decision?.risk_score ?? "Loading..."}
          </p>
          <p>
            Quality:{" "}
            {decision?.trade_quality_score ?? "Loading..."}
          </p>

          {decision?.explanation?.summary && (
            <div className="explanation-box">
              <strong>Explanation</strong>
              <p>{decision.explanation.summary}</p>

              {decision.explanation.reasons?.length > 0 && (
                <ul>
                  {decision.explanation.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </article>

        <article className="card">
          <h2>Provider Health</h2>

          <p>
            Status:{" "}
            {providers?.summary?.status ?? "Loading..."}
          </p>

          <div className="provider-list">
            {providers?.providers
              ? Object.entries(providers.providers).map(
                  ([name, health]) => (
                    <div className="provider-row" key={name}>
                      <span>{name}</span>
                      <span
                        className={
                          health.available
                            ? "provider-badge available"
                            : "provider-badge unavailable"
                        }
                      >
                        {health.available
                          ? "AVAILABLE"
                          : "UNAVAILABLE"}
                      </span>
                    </div>
                  )
                )
              : "Loading..."}
          </div>
        </article>

        <article className="card">
          <h2>Option Chain Intelligence</h2>
          <p>PCR: {optionChain?.pcr != null ? Number(optionChain.pcr).toFixed(2) : "N/A"}</p>
          <p>Max Pain: {optionChain?.max_pain ?? "N/A"}</p>
          <p>
              OI Bias:{" "}
              {!optionChain
                ? "Loading..."
                : optionChain.oi_bias ?? optionChain.pcr_bias ?? "NO DATA"}
            </p>
          <p>
              Volume Bias:{" "}
              {!optionChain
                ? "Loading..."
                : optionChain.volume_bias ?? "NO DATA"}
            </p>
        <p>Data Status: {optionChain?.data_status ?? "Loading..."}</p>
        <p>Source: {optionChain?.source ?? "N/A"}</p>
        <p>Provider: {optionChain?.provider_used ?? "N/A"}</p>
        <p>
          Records:{" "}
          {Array.isArray(optionChain?.records)
            ? optionChain.records.length
            : 0}
        </p>

        {Array.isArray(optionChain?.records) &&
          optionChain.records.length > 0 && (
            <div className="option-chain-mini-table">
              <div className="option-chain-mini-row option-chain-mini-head">
                <span>CE OI</span>
                <span>Strike</span>
                <span>PE OI</span>
              </div>

              {optionChain.records.slice(0, 5).map((row, index) => (
                <div
                  className="option-chain-mini-row"
                  key={`${row.strike_price ?? "strike"}-${index}`}
                >
                  <span>{row.ce?.openInterest ?? "-"}</span>
                  <strong>{row.strike_price ?? "-"}</strong>
                  <span>{row.pe?.openInterest ?? "-"}</span>
                </div>
              ))}
            </div>
          )}
        </article>

        <article className="card">
          <h2>Institutional Flow</h2>
          <p>FII Bias: {context?.fii_bias ?? "Loading..."}</p>
          <p>DII Bias: {context?.dii_bias ?? "Loading..."}</p>
          <p>FII Cash: {context?.fii_cash ?? "Loading..."}</p>
          <p>DII Cash: {context?.dii_cash ?? "Loading..."}</p>
          <p>
            Index Futures:{" "}
            {context?.fii_index_futures ?? "Loading..."}
          </p>
          <p>
            Stock Futures:{" "}
            {context?.fii_stock_futures ?? "Loading..."}
          </p>
          <p>
            Confidence:{" "}
            {context?.institutional_confidence ??
              "Loading..."}
          </p>
        </article>


      </section>
    </main>
  );
}

export default App;
