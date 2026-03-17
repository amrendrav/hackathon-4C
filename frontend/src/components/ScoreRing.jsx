/** Circular score display — big number with colour band */
export default function ScoreRing({ score, size = 120 }) {
  const colour =
    score >= 80 ? '#22c55e' :
    score >= 60 ? '#f59e0b' : '#ef4444';

  const r = (size / 2) - 8;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size/2} cy={size/2} r={r}
          fill="none" stroke="#2e2e42" strokeWidth={8} />
        <circle cx={size/2} cy={size/2} r={r}
          fill="none" stroke={colour} strokeWidth={8}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round" />
      </svg>
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: size * 0.28, fontWeight: 700, color: colour }}>{score}</span>
        <span style={{ fontSize: size * 0.1, color: '#8888aa' }}>/100</span>
      </div>
    </div>
  );
}
