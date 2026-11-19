import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import LeadList from "./components/LeadList.jsx";
import LeadDetail from "./components/LeadDetail.jsx";
import IntelligencePanel from "./components/IntelligencePanel.jsx";
import LeadForm from "./components/LeadForm.jsx";

export default function App() {
  const [stages, setStages] = useState([]);
  const [leads, setLeads] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [intel, setIntel] = useState(null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [form, setForm] = useState(null); // null | "new" | "edit"
  const [toast, setToast] = useState(null);

  const notify = (message, error = false) => {
    setToast({ message, error });
    setTimeout(() => setToast(null), 3500);
  };

  const refresh = useCallback(async () => {
    try {
      const [list, s] = await Promise.all([api.listLeads(query, status), api.stats()]);
      setLeads(list);
      setStats(s);
    } catch (e) {
      notify(`Could not load prospects. ${e.message}`, true);
    } finally {
      setLoading(false);
    }
  }, [query, status]);

  useEffect(() => { api.stages().then(setStages).catch(() => {}); }, []);

  useEffect(() => {
    const t = setTimeout(refresh, 250); // debounce search
    return () => clearTimeout(t);
  }, [refresh]);

  useEffect(() => {
    if (!selectedId && leads.length) setSelectedId(leads[0].lead_id);
  }, [leads, selectedId]);

  useEffect(() => {
    setIntel(null);
    if (selectedId) api.getIntelligence(selectedId).then(setIntel).catch(() => {});
  }, [selectedId]);

  const selected = leads.find((l) => l.lead_id === selectedId) || null;

  async function save(data) {
    if (form === "edit") {
      await api.updateLead(selectedId, data);
      notify("Prospect updated");
    } else {
      const created = await api.createLead(data);
      setSelectedId(created.lead_id);
      notify("Prospect added");
    }
    setForm(null);
    refresh();
  }

  async function remove() {
    if (!window.confirm(`Delete ${selected.company_name}? This also removes its insights and scores.`)) return;
    try {
      await api.deleteLead(selectedId);
      setSelectedId(null);
      notify("Prospect deleted");
      refresh();
    } catch (e) {
      notify(e.message, true);
    }
  }

  async function changeStage(lead_status) {
    try {
      await api.updateLead(selectedId, { ...selected, lead_status });
      refresh();
    } catch (e) {
      notify(e.message, true);
    }
  }

  async function analyze() {
    setAnalyzing(true);
    try {
      setIntel(await api.analyzeLead(selectedId));
      refresh();
    } catch (e) {
      notify(`Analysis failed. ${e.message}`, true);
    } finally {
      setAnalyzing(false);
    }
  }

  async function importCsv(file) {
    try {
      const r = await api.importCsv(file);
      notify(`Imported ${r.imported} prospects${r.skipped.length ? `, skipped ${r.skipped.length}` : ""}`);
      refresh();
    } catch (e) {
      notify(`Import failed. ${e.message}`, true);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>SalesGenie AI</h1>
        {stats && (
          <dl className="stats">
            <div><dt>Prospects</dt><dd>{stats.total}</dd></div>
            <div><dt>Analysed</dt><dd>{stats.analyzed}</dd></div>
            <div><dt>Hot leads</dt><dd>{stats.hot}</dd></div>
            <div><dt>Avg score</dt><dd>{stats.avg_score ?? "–"}</dd></div>
          </dl>
        )}
      </header>

      <main className="layout">
        <LeadList
          leads={leads} selectedId={selectedId} onSelect={setSelectedId}
          query={query} onQuery={setQuery} status={status} onStatus={setStatus}
          stages={stages} onNew={() => setForm("new")} onImport={importCsv} loading={loading}
        />
        <LeadDetail lead={selected} stages={stages} onEdit={() => setForm("edit")} onDelete={remove} onStage={changeStage} />
        <IntelligencePanel lead={selected} intel={intel} analyzing={analyzing} onAnalyze={analyze} />
      </main>

      {form && (
        <LeadForm lead={form === "edit" ? selected : null} stages={stages} onSave={save} onClose={() => setForm(null)} />
      )}
      {toast && <div className={"toast" + (toast.error ? " error" : "")} role="status">{toast.message}</div>}
    </div>
  );
}
