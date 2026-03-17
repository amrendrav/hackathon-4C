import { useState } from 'react';
import {
  getBriefingSummary, getCategoryGap, getStoreCoverage,
  getLowProductivity, getCelebrationDemand, getPromoPerformance,
} from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/Card';
import Spinner from '../components/Spinner';

function DataTable({ data }) {
  if (!data || data.length === 0) return <p style={{ color: '#555', fontSize: 13 }}>No data.</p>;
  const cols = Object.keys(data[0]);
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr>
            {cols.map(c => (
              <th key={c} style={{ padding: '6px 10px', textAlign: 'left',
                background: '#12121f', color: '#8888aa', borderBottom: '1px solid #2e2e42',
                whiteSpace: 'nowrap' }}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.slice(0, 50).map((row, i) => (
            <tr key={i} style={{ background: i % 2 ? '#1a1a2a' : 'transparent' }}>
              {cols.map(c => (
                <td key={c} style={{ padding: '5px 10px', color: '#ccc',
                  borderBottom: '1px solid #1e1e2e' }}>
                  {row[c] === null || row[c] === undefined ? '—' : String(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 50 && (
        <p style={{ color: '#8888aa', fontSize: 11, marginTop: 6 }}>
          Showing 50 of {data.length} rows.
        </p>
      )}
    </div>
  );
}

function DataSection({ title, fetcher, dataKey }) {
  const { data, loading, error } = useApi(fetcher);
  const rows = dataKey ? data?.[dataKey] : data?.data ?? (Array.isArray(data) ? data : null);
  return (
    <Card title={title}>
      {loading && <Spinner label="" />}
      {error && <p style={{ color: '#ef4444', fontSize: 13 }}>⚠ {error}</p>}
      {rows && <DataTable data={rows} />}
    </Card>
  );
}

export default function DataPage() {
  return (
    <div style={{ maxWidth: 1100, margin: '32px auto', padding: '0 24px' }}>
      <h1 style={{ margin: '0 0 6px', fontSize: 22, fontWeight: 700 }}>Raw Data Explorer</h1>
      <p style={{ color: '#8888aa', fontSize: 13, marginBottom: 28 }}>
        Live DuckDB queries — no LLM, &lt;1 s each.
      </p>

      <DataSection title="Briefing Summary (Sales KPIs)" fetcher={getBriefingSummary} dataKey="data" />
      <DataSection title="Category Gap Heatmap (82 categories)" fetcher={getCategoryGap} dataKey="data" />
      <DataSection title="Store Coverage" fetcher={getStoreCoverage} dataKey="data" />
      <DataSection title="Low Productivity SKUs (bottom 25%)" fetcher={getLowProductivity} dataKey="data" />
      <DataSection title="Celebration Demand (52 weeks)" fetcher={getCelebrationDemand} dataKey="data" />
      <DataSection title="Promo Performance (clip→redemption)" fetcher={getPromoPerformance} dataKey="data" />
    </div>
  );
}
