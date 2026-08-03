import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const isCloudflare = Boolean(process.env.CF_PAGES);
const isPreview = isCloudflare && process.env.CF_PAGES_BRANCH !== 'main';
const configuredSite = process.env.SITE_URL;

if (isCloudflare && !configuredSite) {
  throw new Error('Cloudflare Pages builds require the SITE_URL environment variable.');
}

const site = configuredSite || 'http://localhost:4321';
const dailyLastModified = new Map();
const dailyDirectory = fileURLToPath(new URL('./src/content/daily/', import.meta.url));

try {
  for (const filename of readdirSync(dailyDirectory).filter((name) => name.endsWith('.md'))) {
    const markdown = readFileSync(`${dailyDirectory}/${filename}`, 'utf8');
    const date = markdown.match(/^date:\s*['"]?(\d{4}-\d{2}-\d{2})/m)?.[1];
    const updatedAt = markdown.match(/^updatedAt:\s*['"]?([^'"\n]+)/m)?.[1];
    if (date && updatedAt) {
      dailyLastModified.set(`/daily/${date}/`, new Date(updatedAt));
    }
  }
} catch (error) {
  if (error?.code !== 'ENOENT') throw error;
}

export default defineConfig({
  site,
  output: 'static',
  trailingSlash: 'always',
  integrations: isPreview
    ? []
    : [
        sitemap({
          filter: (page) => !page.endsWith('/404/'),
          serialize(item) {
            const pathname = new URL(item.url).pathname;
            const lastmod = dailyLastModified.get(pathname);
            return lastmod ? { ...item, lastmod } : item;
          },
        }),
      ],
});
