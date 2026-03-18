import axios from 'axios';

// Use relative paths in dev so Vite proxy forwards /api/* → localhost:8000
// In production set VITE_API_URL to the deployed backend origin
const BASE_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min — monday-briefing can take ~90s
});

// ── DuckDB endpoints (fast) ──────────────────────────────────────────────────
export const getHealth          = ()         => api.get('/api/health');
export const getBriefingSummary = ()         => api.get('/api/briefing-summary');
export const getCategoryGap     = ()         => api.get('/api/category-gap');
export const getStoreCoverage   = ()         => api.get('/api/store-coverage');
export const getStoreRecs       = (id)       => api.get(`/api/store-recommendations/${id}`);
export const getLowProductivity = (pct=0.25) => api.get('/api/low-productivity-skus', { params: { bottom_pct: pct } });
export const getCelebrationDemand = ()       => api.get('/api/celebration-demand');
export const getPromoPerformance  = ()       => api.get('/api/promo-performance');

// ── LLM endpoints (slow) ────────────────────────────────────────────────────
export const getMondayBriefing  = (storeId=36) => api.get('/api/monday-briefing', { params: { store_id: storeId } });
export const getAgent           = (name, storeId=36) => api.get(`/api/agents/${name}`, { params: { store_id: storeId } });

export const AGENT_NAMES = [
  'category_gap',
  'demand_signal',
  'diet_affinity',
  'promotion_gap',
  'seasonal_trend',
  'low_productivity',
  'store_recommender',
];
