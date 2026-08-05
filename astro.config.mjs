import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const isCloudflare = Boolean(process.env.CF_PAGES);
const isPreview = isCloudflare && process.env.CF_PAGES_BRANCH !== 'main';
const configuredSite = process.env.SITE_URL;

if (isCloudflare && !configuredSite) {
  throw new Error('Cloudflare Pages builds require the SITE_URL environment variable.');
}

const site = configuredSite || 'http://localhost:4321';
const articleLastModified = new Map();
const dailyLastModified = new Map();
const sourceArticleCounts = new Map();
const articleDirectory = fileURLToPath(new URL('./src/content/articles/', import.meta.url));

function markdownFiles(directory) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...markdownFiles(path));
    else if (entry.isFile() && entry.name.endsWith('.md')) files.push(path);
  }
  return files;
}

try {
  for (const filename of markdownFiles(articleDirectory)) {
    const markdown = readFileSync(filename, 'utf8');
    const date = markdown.match(/^dateJst:\s*['"]?(\d{4}-\d{2}-\d{2})/m)?.[1];
    const articleId = markdown.match(/^articleId:\s*['"]?([^'"\n]+)/m)?.[1];
    const sourceId = markdown.match(/^sourceId:\s*['"]?([^'"\n]+)/m)?.[1];
    const updatedAt = markdown.match(/^updatedAt:\s*['"]?([^'"\n]+)/m)?.[1];
    if (sourceId) {
      sourceArticleCounts.set(sourceId, (sourceArticleCounts.get(sourceId) || 0) + 1);
    }
    if (date && articleId && updatedAt) {
      const updated = new Date(updatedAt);
      const [year, month, day] = date.split('-');
      articleLastModified.set(`/articles/${year}/${month}/${day}/${articleId}/`, updated);
      const dailyPath = `/daily/${date}/`;
      const previous = dailyLastModified.get(dailyPath);
      if (!previous || updated > previous) dailyLastModified.set(dailyPath, updated);
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
          filter: (page) => {
            const pathname = new URL(page).pathname;
            if (pathname.endsWith('/404/')) return false;
            const sourceId = pathname.match(/^\/sources\/([^/]+)\/$/)?.[1];
            return !sourceId || (sourceArticleCounts.get(sourceId) || 0) >= 2;
          },
          serialize(item) {
            const pathname = new URL(item.url).pathname;
            const lastmod = articleLastModified.get(pathname) || dailyLastModified.get(pathname);
            return lastmod ? { ...item, lastmod } : item;
          },
        }),
      ],
});
