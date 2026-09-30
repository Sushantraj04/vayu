const API_BASE = (((import.meta as any).env?.VITE_API_URL as string) || '/api/v1').replace(/\/$/, '');

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  let token = localStorage.getItem('vayunet_token');
  const role = localStorage.getItem('vayunet_role') || 'admin';
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  // Only set Content-Type to application/json if body is not FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Auto-obtain valid JWT token if not present and not an auth call
  if (!token && !endpoint.includes('/auth/')) {
    try {
      const tokenRes = await fetch(`${API_BASE}/auth/role-token?role=${encodeURIComponent(role)}`, {
        method: 'POST',
      });
      if (tokenRes.ok) {
        const data = await tokenRes.json();
        const newToken: string | undefined = data.access_token;
        if (newToken) {
          token = newToken;
          localStorage.setItem('vayunet_token', newToken);
        }
      }
    } catch (err) {
      console.warn('Auto token acquisition fallback:', err);
    }
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  // Attach user role header for authenticated context
  headers['X-User-Role'] = role;

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Auth & Roles
  getRoleToken: (role: string = 'admin') => fetchApi<any>(`/auth/role-token?role=${encodeURIComponent(role)}`, { method: 'POST' }),

  // Observability & Health
  getHealth: () => fetchApi<{ status: string; environment: string; version: string; timestamp: string }>('/health'),
  getReady: () => fetchApi<{ status: string; database: string; redis: string; minio: string; timestamp: string }>('/ready'),
  getSourcesStatus: () => fetchApi<any[]>('/sources/status'),

  // Corridors & Stations Telemetry
  getCorridors: () => fetchApi<any[]>('/corridors/'),
  getCorridorSummary: (id: string) => fetchApi<any>(`/corridors/${id}/summary`),
  getStations: (city?: string) => fetchApi<any[]>(`/stations/${city ? `?city=${encodeURIComponent(city)}` : ''}`),
  getStationByCity: (city: string) => fetchApi<any>(`/stations/city/${encodeURIComponent(city)}`),
  getStationReadings: (id: string) => fetchApi<{ station_id: string; count: number; readings: any[] }>(`/stations/${id}/readings`),
  getFires: (hours: number = 24) => fetchApi<{ count: number; hours_lookback: number; fires: any[] }>(`/fires/?hours=${hours}`),
  getWeather: (city?: string) => fetchApi<any[]>(`/weather/${city ? `?city=${encodeURIComponent(city)}` : ''}`),

  // Intelligence & Modeling (Phase 2)
  getHotspots: (corridorId?: string) => fetchApi<any[]>(`/hotspots/${corridorId ? `?corridor_id=${encodeURIComponent(corridorId)}` : ''}`),
  detectHotspots: (hours: number = 48) => fetchApi<any>(`/hotspots/detect?hours=${hours}`, { method: 'POST' }),
  getAttribution: (city: string) => fetchApi<any>(`/attribution/?city=${encodeURIComponent(city)}`),
  getForecasts: (city?: string, horizon?: number) => {
    const params = new URLSearchParams();
    if (city) params.set('city', city);
    if (horizon) params.set('horizon', horizon.toString());
    const q = params.toString() ? `?${params.toString()}` : '';
    return fetchApi<any[]>(`/forecasts/${q}`);
  },
  generateForecast: (city: string) => fetchApi<any>(`/forecasts/generate?city=${encodeURIComponent(city)}`, { method: 'POST' }),
  getModels: (city?: string) => fetchApi<any[]>(`/models/${city ? `?city=${encodeURIComponent(city)}` : ''}`),

  // Alerts & Citizen Reports (Phase 3)
  getAlerts: () => fetchApi<any[]>('/alerts/'),
  evaluateAlerts: () => fetchApi<any>('/alerts/evaluate', { method: 'POST' }),
  acknowledgeAlert: (id: string) => fetchApi<any>(`/alerts/${id}/acknowledge`, { method: 'PUT' }),
  resolveAlert: (id: string) => fetchApi<any>(`/alerts/${id}/resolve`, { method: 'PUT' }),
  getReports: (status?: string) => fetchApi<any[]>(`/reports/${status ? `?status=${status}` : ''}`),
  submitReportJSON: (payload: { latitude: number; longitude: number; category: string; user_pm25?: number; consent: boolean }) =>
    fetchApi<any>('/reports/json', { method: 'POST', body: JSON.stringify(payload) }),
  submitReportForm: (formData: FormData) => fetchApi<any>('/reports/', { method: 'POST', body: formData }),
  moderateReport: (id: string, payload: { status: string; rationale?: string }) =>
    fetchApi<any>(`/reports/${id}/moderate`, { method: 'PATCH', body: JSON.stringify(payload) }),

  // Federated Learning & DPG (Phase 4)
  getFederatedStatus: () => fetchApi<any>('/federated/status'),
  runFederatedRound: () => fetchApi<any>('/federated/rounds/run', { method: 'POST' }),
  getFederatedRounds: () => fetchApi<any[]>('/federated/rounds'),

  // Audit Logs
  getAuditLogs: () => fetchApi<any[]>('/audit/'),
};
