export default function Spinner({ label = 'Loading…' }) {
  return (
    <div style={{ textAlign: 'center', padding: 40, color: '#8888aa' }}>
      <div style={{
        width: 36, height: 36,
        border: '3px solid #2e2e42',
        borderTop: '3px solid #7c3aed',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
        margin: '0 auto 12px',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <p style={{ margin: 0, fontSize: 13 }}>{label}</p>
    </div>
  );
}
