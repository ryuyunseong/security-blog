import { createPath } from './core.mjs';
import { assessmentSeries } from './taxonomy.mjs';
export { categories, categoryLabel, assessmentTargets, assessmentTargetLabel, populatedAssessmentTargets } from './taxonomy.mjs';

export const siteInfo = {
  title: '보안 노트',
  description: '서버 보안 설정, 취약점 관리, SQL과 알고리즘을 실습 코드와 함께 설명합니다.',
  github: 'https://github.com/ryuyunseong',
  portfolio: 'https://ryuyunseong.github.io/security-portfolio/',
};

export const path = createPath(import.meta.env.BASE_URL);
export const assessmentTargetPath = (target: string) => path(`categories/critical-infrastructure/${target}/`);
export const postsPerPage = 12;
export const archivePath = (page = 1) => path(`archive/${page}/`);
export const seriesInfo = (id: string) => {
  const series = assessmentSeries.find((item) => item.id === id);
  return series ? { ...series, path: path(`series/${series.route}/`) } : undefined;
};
export const tagPath = (tag: string) => path(`tags/${encodeURIComponent(tag)}/`);
export const postPath = (id: string) => path(`posts/${id.split('/').map(encodeURIComponent).join('/')}/`);
export const dateLabel = (date: Date) => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(date).replaceAll('-', '.');
