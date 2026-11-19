import { useState } from "react";

const EMPTY = {
  company_name: "", industry: "", contact_name: "", contact_title: "", email: "", phone: "",
  website: "", company_size: "", annual_revenue: "", location: "", funding_stage: "",
  tech_stack: "", notes: "", lead_status: "New",
};

export default function LeadForm({ lead, stages, onSave, onClose }) {
  const [form, setForm] = useState(
    lead ? { ...EMPTY, ...Object.fromEntries(Object.entries(lead).map(([k, v]) => [k, v ?? ""])), tech_stack: (lead.tech_stack || []).join(", ") } : EMPTY
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    if (!form.company_name.trim()) return setError("Company name is required.");
    if (form.email && !/^\S+@\S+\.\S+$/.test(form.email)) return setError("Enter a valid email address.");
    setSaving(true);
    try {
      const payload = {
        ...Object.fromEntries(Object.entries(form).map(([k, v]) => [k, typeof v === "string" ? v.trim() || null : v])),
        company_name: form.company_name.trim(),
        lead_status: form.lead_status,
        tech_stack: form.tech_stack.split(",").map((t) => t.trim()).filter(Boolean),
      };
      await onSave(payload);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  const input = (key, label, props = {}) => (
    <label className="form-field">
      <span>{label}</span>
      <input value={form[key]} onChange={set(key)} {...props} />
    </label>
  );

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={lead ? "Edit prospect" : "Add prospect"}>
      <form className="modal" onSubmit={submit}>
        <h2>{lead ? "Edit prospect" : "Add prospect"}</h2>
        <div className="form-grid">
          {input("company_name", "Company name *", { autoFocus: true })}
          {input("industry", "Industry")}
          {input("contact_name", "Contact name")}
          {input("contact_title", "Contact title")}
          {input("email", "Email", { type: "email" })}
          {input("phone", "Phone")}
          {input("website", "Website")}
          {input("location", "Location")}
          {input("company_size", "Company size", { placeholder: "e.g. 250-500" })}
          {input("annual_revenue", "Annual revenue", { placeholder: "e.g. $45M - $60M" })}
          <label className="form-field">
            <span>Funding stage</span>
            <select value={form.funding_stage} onChange={set("funding_stage")}>
              <option value="">Unknown</option>
              {["Bootstrapped", "Seed", "Series A", "Series B", "Series C", "Series D+", "Public"].map((s) => (
                <option key={s}>{s}</option>
              ))}
            </select>
          </label>
          <label className="form-field">
            <span>Sales stage</span>
            <select value={form.lead_status} onChange={set("lead_status")}>
              {stages.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
        </div>
        {input("tech_stack", "Technology stack (comma separated)", { placeholder: "AWS, Python, React" })}
        <label className="form-field">
          <span>Notes</span>
          <textarea rows="3" value={form.notes} onChange={set("notes")} />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="row end">
          <button type="button" className="btn" onClick={onClose}>Cancel</button>
          <button className="btn primary" disabled={saving}>{saving ? "Saving…" : "Save prospect"}</button>
        </div>
      </form>
    </div>
  );
}
