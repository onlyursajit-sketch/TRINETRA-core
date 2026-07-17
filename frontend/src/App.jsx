import { useEffect, useState } from "react";
import "./App.css";

import {
  fetchMarketContext,
  fetchMarketDecision,
  fetchProviderHealth,
} from "./services/api";

function App() {
  const [symbol, setSymbol] = useState("NIFTY");
  const [context, setContext] = useState(null);
  const [decision, setDecision] = useState(null);
  const [providers, setProviders] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setError("");

        const [contextData, decisionData, providerData] =
          await Promise.all([
            fetchMarketContext(symbol),
            fetchMarketDecision(symbol),
            fetchProviderHealth(),
          ]);

        setContext(contextData);
        setDecision(decisionData);
        setProviders(providerData);
      } catch (err) {
        setError(err.message);
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
        </div>

        <select
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
        >
          <option value="NIFTY">NIFTY</option>
          <option value="BANKNIFTY">BANKNIFTY</option>
        </select>
      </header>

      {error && (
        <section className="error-box">
          API Error: {error}
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
            Regime: {context?.market_regime ?? "Loading..."}
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
        </article>

        <article className="card">
          <h2>Provider Health</h2>
          <p>
            Providers:{" "}
            {providers?.providers
              ? Object.keys(providers.providers).length
              : "Loading..."}
          </p>
          <p>
            Healthy:{" "}
            {providers?.summary?.healthy_providers ??
              "Loading..."}
          </p>
        </article>

        <article className="card">
          <h2>Institutional Flow</h2>
          <p>
            FII Cash: {context?.fii_cash ?? "Loading..."}
          </p>
          <p>
            DII Cash: {context?.dii_cash ?? "Loading..."}
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
