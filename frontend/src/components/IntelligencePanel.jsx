function ScoreRing({ score, priority }) {
  const r = 44;
  const c = 2 * Math.PI * r;
  return (
    <div className={"ring " + (priority || "").toLowerCase()}>
      <svg viewBox="0 0 110 110" role="img" aria-label={`Qualification score ${score} out of 100`}>
        <circle cx="55" cy="55" r={r} className="ring-bg" />
        <circle
          cx="55" cy="55" r={r} className="ring-fg"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - score / 100)}
          transform="rotate(-90 55 55)"
        />
        <text x="55" y="62" textAnchor="middle" className="ring-num">{score}</text>
      </svg>
      <span className="muted">Qualification score</span>
    </div>
  );
}

export default function IntelligencePanel({ lead, intel, analyzing, onAnalyze }) {
  if (!lead) return <aside className="panel intel-panel" />;
  const { insight, score } = intel || {};

  return (
    <aside className="panel intel-panel" aria-label="Lead intelligence">
      <header className="detail-head">
        <h2>Lead intelligence</h2>
        {insight && <span className="badge">{insight.source === "gemini" ? "Gemini" : "Rules engine"}</span>}
      </header>

      <button className="btn primary wide" onClick={onAnalyze} disabled={analyzing}>
        {analyzing ? "Analysing…" : insight ? "Re-analyse prospect" : "Analyse prospect"}
      </button>

      {!insight && !analyzing && (
        <p className="empty">Run an analysis to get a qualification score, business needs, and opportunities.</p>
      )}

      {score && (
        <>
          <ScoreRing score={score.lead_score} priority={score.priority_level} />
          <div className="meter-row">
            <span>{score.priority_level} lead</span>
            <span>{score.conversion_probability}% likely to convert</span>
          </div>
          <div className="meter"><div style={{ width: `${score.conversion_probability}%` }} /></div>

          <h3>Scoring factors</h3>
          <ul className="factors">
            {score.factors.map((f) => (
              <li key={f.label}>
                <span><strong>{f.label}</strong><span className="muted small">{f.detail}</span></span>
                <span className="points">+{f.points}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      {insight && (
        <>
          {insight.highlights.map((h) => (
            <div className="highlight" key={h.title}>
              <strong>{h.title}</strong>
              <p>{h.detail}</p>
            </div>
          ))}

          <h3>Business needs</h3>
          <ul className="bullets">{insight.business_needs.map((n) => <li key={n}>{n}</li>)}</ul>

          <h3>Opportunities</h3>
          <div className="chips">{insight.opportunities.map((o) => <span className="chip" key={o}>{o}</span>)}</div>

          <h3>Industry analysis</h3>
          <p className="notes">{insight.industry_analysis}</p>
          <p className="muted small">Generated {new Date(insight.generated_at + "Z").toLocaleString()}</p>
        </>
      )}
    </aside>
  );
}
