/** Barebone card shell — easy to reskin */
export default function Card({ title, children, style = {} }) {
  return (
    <div style={{
      background: '#1e1e2e',
      border: '1px solid #2e2e42',
      borderRadius: 10,
      padding: '20px 24px',
      marginBottom: 20,
      ...style,
    }}>
      {title && (
        <h3 style={{ margin: '0 0 14px', fontSize: 14, textTransform: 'uppercase',
                     letterSpacing: 1, color: '#8888aa' }}>
          {title}
        </h3>
      )}
      {children}
    </div>
  );
}
