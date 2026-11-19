import { useRef } from "react";

export default function LeadList({ leads, selectedId, onSelect, query, onQuery, status, onStatus, stages, onNew, onImport, loading }) {
  const fileRef = useRef(null);

  return (
    <aside className="panel list-panel" aria-label="Prospects">
      <div className="list-tools">
        <input
          type="search"
          placeholder="Search prospects"
          aria-label="Search prospects"
          value={query}
          onChange={(e) => onQuery(e.target.value)}
        />
        <select aria-label="Filter by stage" value={status} onChange={(e) => onStatus(e.target.value)}>
          <option value="">All stages</option>
          {stages.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
        <div className="row">
          <button className="btn primary" onClick={onNew}>Add prospect</button>
          <button className="btn" onClick={() => fileRef.current?.click()}>Import CSV</button>
          <input
            ref={fileRef}
            type="file"
            accept=".csv"
            hidden
            onChange={(e) => {
              if (e.target.files[0]) onImport(e.target.files[0]);
              e.target.value = "";
            }}
          />
        </div>
      </div>

      <ul className="lead-list">
        {loading && <li className="empty">Loading prospects…</li>}
        {!loading && leads.length === 0 && (
          <li className="empty">No prospects match. Add one or import a CSV.</li>
        )}
        {leads.map((l) => (
          <li key={l.lead_id}>
            <button
              className={"lead-item" + (l.lead_id === selectedId ? " active" : "")}
              onClick={() => onSelect(l.lead_id)}
            >
              <span className="lead-top">
                <strong>{l.company_name}</strong>
                {l.latest_score != null && (
                  <span className={"pill " + (l.latest_priority || "").toLowerCase()}>{l.latest_score}</span>
                )}
              </span>
              <span className="muted">
                {[l.contact_name, l.contact_title].filter(Boolean).join(", ") || "No contact"}
              </span>
              <span className="stage">{l.lead_status}</span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
