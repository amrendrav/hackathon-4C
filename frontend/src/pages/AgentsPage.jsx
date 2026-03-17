import { useState } from 'react';
import { getAgent, AGENT_NAMES } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/Card';
import Spinner from '../components/Spinner';

const AGENT_META = {
  category_gap:     { label: 'Category Gap',      emoji: '📊', desc: 'Low-AGP / high-markdown categories' },
  demand_signal:    { label: 'Demand Signal',      emoji: '📈', desc: 'Customer segment velocity trends'   },
  diet_affinity:    { label: 'Diet Affinity',      emoji: '🥗', desc: 'GF / vegan / keto / dairy-free gaps'},
  promotion_gap:    { label: 'Promotion Gap',      emoji: '🎫', desc: 'Clip-to-redemption failure analysis' },
  seasonal_trend:   { label: 'Seasonal Trend',     emoji: '📅', desc: 'Celebration demand + Google Trends'  },
  low_productivity: { label: 'Low Productivity',   emoji: '⚠️', desc: 'Bottom-quartile SKU rationalization' },
  store_recommender:{ label: 'Store Recommender',  emoji: '🏪', desc: 'Network gap → store add/remove'     },
};

function AgentPanel({ name }) {
  const meta = AGENT_META[name];
  const [storeId, setStoreId] = useState(36);
  const [triggered, setTriggered] = useState(false);
  const { data, loading, error, refetch } = useApi(() => getAgent(name, storeId), false);

  const result = data?.result;

  return (
    <Card style={{ marginBottom: 16 }}>
      {/* Agent header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <span style={{ fontSize: 22 }}>{meta.emoji}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>{meta.label}</div>
          <div style={{ fontSize: 12, color: '#8888aa' }}>{meta.desc}</div>
        </div>
        <input
          type="number" value={storeId}
          onChange={e => setStoreId(Number(e.target.value))}
          style={{ width: 64, padding: '4px 8px', background: '#12121f',
            border: '1px solid #2e2e42', borderRadius: 5, color: '#fff', fontSize: 13 }}
        />
        <button
          onClick={() => { setTriggered(true); refetch(); }}
          disabled={loading}
          style={{ padding: '5px 16px', background: '#7c3aed', color: '#fff',
            border: 'none', borderRadius: 5, cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: 13, fontWeight: 600, opacity: loading ? 0.6 : 1 }}
        >
          {loading ? '…' : 'Run'}
        </button>
      </div>

      {/* Output */}
      {!triggered && <p style={{ color: '#555', fontSize: 13, margin: 0 }}>Not yet run.</p>}
      {loading && <Spinner label={`Running ${meta.label}…`} />}
      {error && <p style={{ color: '#ef4444', fontSize: 13, margin: 0 }}>⚠ {error}</p>}
      {result && !loading && (
        <pre style={{
          background: '#12121f', border: '1px solid #2e2e42',
          borderRadius: 6, padding: 14, margin: 0,
          fontSize: 12, overflowX: 'auto', color: '#ccc',
          maxHeight: 320, overflowY: 'auto',
        }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </Card>
  );
}

export default function AgentsPage() {
  return (
    <div style={{ maxWidth: 860, margin: '32px auto', padding: '0 24px' }}>
      <h1 style={{ margin: '0 0 6px', fontSize: 22, fontWeight: 700 }}>Agent Explorer</h1>
      <p style={{ color: '#8888aa', fontSize: 13, marginBottom: 28 }}>
        Run any specialist agent in isolation. Each takes 5–15 s and uses an Anthropic API call.
      </p>
      {AGENT_NAMES.map(name => <AgentPanel key={name} name={name} />)}
    </div>
  );
}
