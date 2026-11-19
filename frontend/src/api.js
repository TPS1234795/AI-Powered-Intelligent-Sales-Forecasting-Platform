const BASE = import.meta.env.VITE_API_URL || "/api";

async function request(path, options = {}) {
  const isForm = options.body instanceof FormData;
  const res = await fetch(BASE + path, {
    ...options,
    headers: isForm ? {} : { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = await res.json();
      message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  stages: () => request("/stages"),
  stats: () => request("/stats"),
  listLeads: (q = "", status = "") =>
    request(`/leads?${new URLSearchParams({ ...(q && { q }), ...(status && { status }) })}`),
  createLead: (data) => request("/leads", { method: "POST", body: JSON.stringify(data) }),
  updateLead: (id, data) => request(`/leads/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteLead: (id) => request(`/leads/${id}`, { method: "DELETE" }),
  getIntelligence: (id) => request(`/leads/${id}/intelligence`),
  analyzeLead: (id) => request(`/leads/${id}/analyze`, { method: "POST" }),
  importCsv: (file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/leads/import", { method: "POST", body: form });
  },
};
