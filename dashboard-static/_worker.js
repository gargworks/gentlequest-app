const RENDER_API = 'https://gentlequest.onrender.com';

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Proxy /api/* to Render backend
    if (url.pathname.startsWith('/api/')) {
      const targetUrl = RENDER_API + url.pathname + url.search;
      try {
        const resp = await fetch(targetUrl, {
          method: request.method,
          headers: { 'Accept': 'application/json' },
        });
        const body = await resp.text();
        return new Response(body, {
          status: resp.status,
          headers: {
            'Content-Type': resp.headers.get('Content-Type') || 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': '*',
            'Cache-Control': 'no-cache',
          },
        });
      } catch (err) {
        return new Response(JSON.stringify({ error: 'Proxy failed: ' + err.message }), {
          status: 502,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
        });
      }
    }
    
    // For everything else, use Pages static asset handling
    // Fall through to the asset fetcher
    return env.ASSETS.fetch(request);
  },
};
