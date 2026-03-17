import { Link, useLocation } from 'react-router-dom';
import { useApi } from '../hooks/useApi';
import { getHealth } from '../api/client';
import StatusBadge from './StatusBadge';

const LINKS = [
  { to: '/',          label: 'Briefing'  },
  { to: '/agents',    label: 'Agents'    },
  { to: '/data',      label: 'Raw Data'  },
];

export default function Navbar() {
  const { pathname } = useLocation();
  const { data }     = useApi(getHealth);

  return (
    <nav style={{
      display: 'flex', alignItems: 'center', gap: 0,
      background: '#12121f', borderBottom: '1px solid #2e2e42',
      padding: '0 28px', height: 54, position: 'sticky', top: 0, zIndex: 100,
    }}>
      {/* Logo */}
      <span style={{ fontWeight: 800, fontSize: 18, color: '#7c3aed', marginRight: 32 }}>
        ACI
      </span>

      {/* Nav links */}
      {LINKS.map(({ to, label }) => (
        <Link key={to} to={to} style={{
          padding: '0 16px', height: 54,
          display: 'flex', alignItems: 'center',
          color: pathname === to ? '#fff' : '#8888aa',
          borderBottom: pathname === to ? '2px solid #7c3aed' : '2px solid transparent',
          textDecoration: 'none', fontSize: 14, fontWeight: 500,
          transition: 'color 0.15s',
        }}>
          {label}
        </Link>
      ))}

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* API health */}
      <StatusBadge
        label={data ? `API ${data.db === 'connected' ? '● live' : '● db err'}` : '● checking'}
        ok={data ? data.db === 'connected' : null}
      />
    </nav>
  );
}
