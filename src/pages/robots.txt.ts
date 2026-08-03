import type { APIRoute } from 'astro';
import { isPreviewBuild } from '../lib/site';

export const GET: APIRoute = ({ site }) => {
  const preview = isPreviewBuild();
  const lines = preview
    ? ['User-agent: *', 'Disallow: /']
    : ['User-agent: *', 'Allow: /', `Sitemap: ${new URL('/sitemap-index.xml', site).href}`];
  return new Response(`${lines.join('\n')}\n`, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
