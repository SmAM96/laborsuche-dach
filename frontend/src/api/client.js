const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000';

export async function fetchDatasets() {
  const res = await fetch(`${API_BASE}/api/datasets`);
  if (!res.ok) throw new Error('Failed to load datasets');
  return res.json();
}

export async function fetchProviders({ city, category, status } = {}) {
  const url = new URL(`${API_BASE}/api/providers`);
  if (city) url.searchParams.set('city', city);
  if (category && category !== 'all')
    url.searchParams.set('category', category);
  if (status) url.searchParams.set('status', status);

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to load providers');
  return res.json();
}
