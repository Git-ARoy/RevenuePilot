const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    });
  } catch (err: any) {
    throw new Error(`Failed to connect to backend server: ${err?.message || 'Network error'}`);
  }

  let json: any;
  try {
    json = await res.json();
  } catch {
    if (!res.ok) {
      throw new Error(`API request failed with status ${res.status}: ${res.statusText}`);
    }
    throw new Error('Failed to parse API response');
  }

  if (!res.ok) {
    const errorMsg =
      json?.error?.message ||
      (typeof json?.detail === 'string'
        ? json.detail
        : Array.isArray(json?.detail)
        ? json.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
        : json?.message) ||
      `API request failed with status ${res.status}`;
    throw new Error(errorMsg);
  }

  if (json?.error) {
    throw new Error(json.error.message || json.error.code || 'API Error');
  }

  if (json && typeof json === 'object' && 'data' in json) {
    return json.data as T;
  }

  return json as T;
}

