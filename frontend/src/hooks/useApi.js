import { useState, useEffect, useCallback } from 'react';

/**
 * Generic data-fetching hook.
 * @param {Function} fetcher  - async function that returns an axios response
 * @param {boolean}  eager    - fetch immediately on mount (default true)
 */
export function useApi(fetcher, eager = true) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(eager);
  const [error,   setError]   = useState(null);

  const fetch = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetcher(...args);
      setData(res.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => { if (eager) fetch(); }, []); // eslint-disable-line

  return { data, loading, error, refetch: fetch };
}
