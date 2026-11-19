function Field({ label, value }) {
  return (
    <div className="field">
      <span className="muted">{label}</span>
      <span>{value || "Not provided"}</span>
    </div>
  );
}

export default function LeadDetail({ lead, stages, onEdit, onDelete, onStage }) {
  if (!lead) {
    return (
      <section className="panel detail-panel">
        <p className="empty">Select a prospect to see their company profile.</p>
      </section>
    );
  }

  return (
    <section className="panel detail-panel" aria-label="Company profile">
      <header className="detail-head">
        <div>
          <h2>{lead.company_name}</h2>
          <p className="muted">
            {[lead.industry, lead.funding_stage].filter(Boolean).join(" · ") || "No industry set"}
          </p>
        </div>
        <div className="row">
          <button className="btn" onClick={onEdit}>Edit</button>
          <button className="btn danger" onClick={onDelete}>Delete</button>
        </div>
      </header>

      <label className="stage-select">
        <span className="muted">Sales stage</span>
        <select value={lead.lead_status} onChange={(e) => onStage(e.target.value)}>
          {stages.map((s) => (
            <option key={s}>{s}</option>
          ))}
        </select>
      </label>

      <div className="stage-track" aria-hidden="true">
        {stages.slice(0, 6).map((s, i) => (
          <span key={s} className={i <= stages.indexOf(lead.lead_status) ? "done" : ""} title={s} />
        ))}
      </div>

      <div className="grid">
        <Field label="Company size" value={lead.company_size && `${lead.company_size} employees`} />
        <Field label="Annual revenue" value={lead.annual_revenue} />
        <Field label="Location" value={lead.location} />
        <Field label="Funding stage" value={lead.funding_stage} />
        <Field label="Contact" value={[lead.contact_name, lead.contact_title].filter(Boolean).join(", ")} />
        <Field label="Email" value={lead.email} />
        <Field label="Phone" value={lead.phone} />
        <Field label="Website" value={lead.website} />
      </div>

      <h3>Technology stack</h3>
      <div className="chips">
        {lead.tech_stack?.length ? lead.tech_stack.map((t) => <span className="chip" key={t}>{t}</span>) : <span className="muted">None listed</span>}
      </div>

      {lead.notes && (
        <>
          <h3>Notes</h3>
          <p className="notes">{lead.notes}</p>
        </>
      )}

      <p className="muted small">
        Added {new Date(lead.created_at).toLocaleDateString()}
        {lead.updated_at && ` · Updated ${new Date(lead.updated_at).toLocaleString()}`}
      </p>
    </section>
  );
}
