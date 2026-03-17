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

  const briefing = data?.briefing;

  return (
    <div style={{ maxWidth: 900, margin: '32px auto', padding: '0 24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700 }}>Monday Morning Briefing</h1>
          <p style={{ margin: '4px 0 0', color: '#8888aa', fontSize: 13 }}>
            7 AI agents run in parallel → synthesised into one prioritised brief
          </p>
        </div>
        <div style={{ flex: 1 }} />
        <label style={{ color: '#8888aa', fontSize: 13 }}>Store ID</label>
        <input
          type="number"
          value={storeId}
          onChange={e => setStoreId(Number(e.target.value))}
          style={{
            width: 72, padding: '6px 10px', background: '#1e1e2e',
            border: '1px solid #2e2e42', borderRadius: 6, color: '#fff', fontSize: 14,
          }}
        />
        <button onClick={run} disabled={loading} style={{
          padding: '8px 20px', background: '#7c3aed', color: '#fff',
          border: 'none', borderRadius: 6, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
          fontSize: 14, opacity: loading ? 0.6 : 1,
        }}>
          {loading ? 'Running…' : 'Run Briefing'}
        </button>
      </div>

      {/* States */}
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

      {briefing && !loading && (
        <>
          {/* Score + headline */}
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 28 }}>
              <ScoreRing score={briefing.overall_score} />
              <div>
                <div style={{ fontSize: 12, color: '#8888aa', marginBottom: 4 }}>
                  {briefing.store_context || `Store ${storeId}`}
                </div>
                <p style={{ fontSize: 17, fontWeight: 600, margin: '0 0 8px', lineHeight: 1.4 }}>
                  {briefing.headline}
                </p>
                <p style={{ fontSize: 13, color: '#8888aa', margin: 0 }}>
                  {briefing.store_profile || ''}
                </p>
              </div>
            </div>
          </Card>

          {/* Opportunities + Risks */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <Card title="Top Opportunities">
              {(briefing.top_3_opportunities || []).map((o, i) => (
                <div key={i} style={{ marginBottom: 12, paddingBottom: 12,
                  borderBottom: i < 2 ? '1px solid #2e2e42' : 'none' }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>
                    {i+1}. {o.opportunity}
                  </div>
                  <div style={{ fontSize: 12, color: '#22c55e' }}>{o.impact}</div>
                  <div style={{ fontSize: 12, color: '#8888aa' }}>{o.action}</div>
                </div>
              ))}
            </Card>

            <Card title="Top Risks">
              {(briefing.top_3_risks || []).map((r, i) => (
                <div key={i} style={{ marginBottom: 12, paddingBottom: 12,
                  borderBottom: i < 2 ? '1px solid #2e2e42' : 'none' }}>
                  <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 3 }}>
                    {i+1}. {r.risk}
                  </div>
                  <div style={{ fontSize: 12, color: '#ef4444' }}>{r.severity}</div>
                  <div style={{ fontSize: 12, color: '#8888aa' }}>{r.mitigation}</div>
                </div>
              ))}
            </Card>
          </div>

          {/* Immediate actions */}
          <Card title="Immediate Actions (Next 7 Days)">
            {(briefing.immediate_actions || []).map((a, i) => (
              <div key={i} style={{
                display: 'flex', gap: 12, alignItems: 'flex-start',
                marginBottom: 10, paddingBottom: 10,
                borderBottom: i < briefing.immediate_actions.length - 1 ? '1px solid #2e2e42' : 'none',
              }}>
                <span style={{ background: '#7c3aed', color: '#fff', borderRadius: 4,
                  padding: '1px 8px', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>
                  {i+1}
                </span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{a.action}</div>
                  <div style={{ fontSize: 12, color: '#8888aa' }}>{a.owner} · {a.deadline}</div>
                </div>
              </div>
            ))}
          </Card>

          {/* Agent scores */}
          <Card title="Agent Scores">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
              {Object.entries(briefing.agent_scores || {}).map(([name, score]) => {
                const colour = score >= 80 ? '#22c55e' : score >= 60 ? '#f59e0b' : '#ef4444';
                return (
                  <div key={name} style={{
                    background: '#12121f', border: '1px solid #2e2e42',
                    borderRadius: 8, padding: '10px 16px', textAlign: 'center', minWidth: 110,
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

          {/* Executive summary */}
          {briefing.executive_summary && (
            <Card title="Executive Summary">
              <p style={{ margin: 0, fontSize: 14, lineHeight: 1.7, color: '#ccc' }}>
                {briefing.executive_summary}
              </p>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
