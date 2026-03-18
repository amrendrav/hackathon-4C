import { useState } from 'react';
import { getMondayBriefing } from '../api/client';
import { useApi } from '../hooks/useApi';
import Card from '../components/Card';
import ScoreRing from '../components/ScoreRing';
import Spinner from '../components/Spinner';

export default function BriefingPage() {
  const [storeId, setStoreId] = useState(36);
  const [triggered, setTriggered] = useState(false);
  const { data, loading, error, refetch } = useApi(
    () => getMondayBriefing(storeId), false
  );

  function run() {
    setTriggered(true);
    refetch();
  }

  // Real API shape: data.synthesis holds the AI output
  const synthesis = data?.synthesis;
  const snap      = synthesis?.performance_snapshot || {};

  return (
    <div style={{ maxWidth: 960, margin: '32px auto', padding: '0 24px' }}>

      {/* ── Header ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Monday Morning Briefing</h1>
          <p style={{ margin: '4px 0 0', color: '#8888aa', fontSize: 13 }}>
            7 AI agents run in parallel → synthesised into one prioritised brief
          </p>
        </div>
        <div style={{ flex: 1 }} />
        <label style={{ color: '#8888aa', fontSize: 13 }}>Store</label>
        <input
          type="number" value={storeId}
          onChange={e => setStoreId(Number(e.target.value))}
          style={{
            width: 72, padding: '6px 10px', background: '#1e1e2e',
            border: '1px solid #2e2e42', borderRadius: 6, color: '#fff', fontSize: 14,
          }}
        />
        <button onClick={run} disabled={loading} style={{
          padding: '8px 20px', background: '#7c3aed', color: '#fff',
          border: 'none', borderRadius: 6, fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: 14, opacity: loading ? 0.6 : 1,
        }}>
          {loading ? 'Running…' : 'Run Briefing'}
        </button>
      </div>

      {/* ── Idle state ─────────────────────────────────────────────── */}
      {!triggered && !loading && (
        <Card>
          <p style={{ color: '#8888aa', textAlign: 'center', margin: 0 }}>
            Press <strong style={{ color: '#7c3aed' }}>Run Briefing</strong> to fetch the AI analysis.
            <br /><span style={{ fontSize: 12 }}>First run takes 60–90 seconds.</span>
          </p>
        </Card>
      )}

      {loading && <Spinner label="Running 7 agents in parallel… (~60–90 s)" />}

      {error && (
        <Card style={{ borderColor: '#ef4444' }}>
          <p style={{ color: '#ef4444', margin: 0 }}>⚠ {error}</p>
        </Card>
      )}

      {/* ── Results ────────────────────────────────────────────────── */}
      {synthesis && !loading && (
        <>
          {/* Score + headline */}
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
              <ScoreRing score={synthesis.overall_score} />
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 6 }}>
                  <span style={{
                    background: snap.status === 'Needs Attention' ? '#92400e' : '#14532d',
                    color: snap.status === 'Needs Attention' ? '#fbbf24' : '#4ade80',
                    borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 600,
                  }}>{snap.status}</span>
                  <span style={{ fontSize: 12, color: '#8888aa' }}>Store {data.store_id}</span>
                  {data.elapsed_seconds && (
                    <span style={{ fontSize: 12, color: '#8888aa' }}>
                      · {data.elapsed_seconds.toFixed(1)}s
                    </span>
                  )}
                </div>
                <p style={{ fontSize: 16, fontWeight: 600, margin: '0 0 8px', lineHeight: 1.5 }}>
                  {synthesis.headline}
                </p>
                {snap.key_metric && (
                  <p style={{ fontSize: 12, color: '#8888aa', margin: 0 }}>
                    {snap.key_metric}
                  </p>
                )}
              </div>
            </div>
          </Card>

          {/* Opportunities + Risks */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <Card title="Top Opportunities">
              {(synthesis.top_3_opportunities || []).map((o, i) => (
                <div key={i} style={{
                  marginBottom: 14, paddingBottom: 14,
                  borderBottom: i < 2 ? '1px solid #2e2e42' : 'none',
                }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                    {i + 1}. {o.title}
                  </div>
                  <div style={{ fontSize: 12, color: '#22c55e', marginBottom: 3 }}>{o.impact}</div>
                  <div style={{ fontSize: 12, color: '#8888aa', marginBottom: 3 }}>{o.action}</div>
                  {o.agent && (
                    <div style={{ fontSize: 11, color: '#6b6b88' }}>via {o.agent}</div>
                  )}
                </div>
              ))}
            </Card>

            <Card title="Top Risks">
              {(synthesis.top_3_risks || []).map((r, i) => (
                <div key={i} style={{
                  marginBottom: 14, paddingBottom: 14,
                  borderBottom: i < 2 ? '1px solid #2e2e42' : 'none',
                }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                    {i + 1}. {r.title}
                  </div>
                  {r.severity && (
                    <div style={{
                      fontSize: 11, fontWeight: 600, marginBottom: 3,
                      color: r.severity === 'High' ? '#ef4444' :
                             r.severity === 'Medium' ? '#f59e0b' : '#8888aa',
                    }}>{r.severity} severity</div>
                  )}
                  <div style={{ fontSize: 12, color: '#8888aa', marginBottom: 3 }}>{r.action}</div>
                  {r.agent && (
                    <div style={{ fontSize: 11, color: '#6b6b88' }}>via {r.agent}</div>
                  )}
                </div>
              ))}
            </Card>
          </div>

          {/* This week watchlist */}
          {synthesis.this_week_watchlist?.length > 0 && (
            <Card title="This Week's Watchlist">
              {synthesis.this_week_watchlist.map((item, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 10, alignItems: 'flex-start',
                  marginBottom: 10, paddingBottom: 10,
                  borderBottom: i < synthesis.this_week_watchlist.length - 1 ? '1px solid #2e2e42' : 'none',
                }}>
                  <span style={{
                    background: '#1e1e2e', border: '1px solid #7c3aed',
                    color: '#7c3aed', borderRadius: 4, padding: '1px 7px',
                    fontSize: 11, fontWeight: 700, flexShrink: 0,
                  }}>{i + 1}</span>
                  <span style={{ fontSize: 13, color: '#ccc', lineHeight: 1.5 }}>{item}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Marketing partnership */}
          {synthesis.marketing_partnership && (
            <Card title="Marketing Partnership Recommendation">
              <p style={{ margin: 0, fontSize: 14, lineHeight: 1.7, color: '#ccc' }}>
                {synthesis.marketing_partnership}
              </p>
            </Card>
          )}

          {/* Agent confidence scores */}
          <Card title="Agent Confidence Scores">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {Object.entries(synthesis.agent_confidence || {}).map(([name, conf]) => {
                const score = Math.round(conf * 100);
                const colour = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444';
                return (
                  <div key={name} style={{
                    background: '#12121f', border: '1px solid #2e2e42',
                    borderRadius: 8, padding: '10px 16px', textAlign: 'center', minWidth: 120,
                  }}>
                    <div style={{ fontSize: 22, fontWeight: 700, color: colour }}>{score}</div>
                    <div style={{ fontSize: 11, color: '#8888aa', marginTop: 2 }}>
                      {name.replace(/_/g, ' ')}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* vs last week context */}
          {snap.vs_last_week && (
            <Card title="Performance Context">
              <p style={{ margin: 0, fontSize: 13, color: '#8888aa', lineHeight: 1.6 }}>
                {snap.vs_last_week}
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
