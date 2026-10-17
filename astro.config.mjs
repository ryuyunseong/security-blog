import { defineConfig } from 'astro/config';
import { articleMarkdownOptions } from './src/lib/article-markdown.mjs';

const repository = process.env.GITHUB_REPOSITORY;
const owner = process.env.GITHUB_REPOSITORY_OWNER;
const repoName = repository?.split('/')[1];
const site = process.env.SITE_URL || (owner ? `https://${owner}.github.io` : 'http://localhost:4321');
const base = process.env.BASE_PATH || (repoName && repoName.toLowerCase() !== `${owner}.github.io`.toLowerCase() ? `/${repoName}/` : '/');

if (process.env.GITHUB_ACTIONS === 'true' && (!owner || !repoName)) {
  throw new Error('GitHub Pages 빌드에는 저장소 정보가 필요합니다.');
}
if (!/^https?:\/\//.test(site) || !base.startsWith('/') || /[?#\\]/.test(base)) {
  throw new Error('SITE_URL과 BASE_PATH 형식을 확인하세요.');
}

export default defineConfig({
  site,
  base,
  output: 'static',
  trailingSlash: 'always',
  markdown: articleMarkdownOptions,
  devToolbar: { enabled: false },
});
