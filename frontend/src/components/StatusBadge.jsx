/** Tiny coloured pill — green / yellow / red based on value */
export default function StatusBadge({ label, ok }) {
  const colour = ok === null ? '#888' : ok ? '#22c55e' : '#ef4444';
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 12,
      background: colour,
      color: '#fff',
      fontSize: 12,
      fontWeight: 600,
      letterSpacing: 0.5,
    }}>
      {label}
    </span>
  );
}
