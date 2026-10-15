import { createPath } from './core.mjs';

export const siteInfo = {
  title: '보안 노트',
  description: 'Unix부터 웹·인프라 보안까지, 실습과 코드로 쌓아가는 기술 노트.',
  github: 'https://github.com/ryuyunseong',
  tistory: 'https://neoflux.tistory.com/',
};

export const categories = [
  { id: 'unix', label: 'Unix', description: '파일, 권한, 계정을 확인하는 기초부터 기록합니다.' },
  { id: 'web', label: '웹 보안', description: 'HTTP와 웹 애플리케이션의 보안 동작을 살펴봅니다.' },
  { id: 'infrastructure', label: '인프라 보안', description: '설정 점검과 증적 관리 방법을 정리합니다.' },
  { id: 'cve', label: 'CVE', description: '공개 취약점의 근거와 영향 범위를 구분해 읽습니다.' },
  { id: 'qualys', label: 'Qualys', description: '탐지 결과를 해석하고 검토하는 방법을 정리합니다.' },
] as const;

export const path = createPath(import.meta.env.BASE_URL);
export const unixSeries = {
  id: 'unix-2026',
  title: '2026 주요정보통신기반시설 · Unix',
  path: path('series/critical-infrastructure-unix-2026/'),
};
export const categoryLabel = (id: string) => categories.find((category) => category.id === id)?.label ?? id;
export const tagPath = (tag: string) => path(`tags/${encodeURIComponent(tag)}/`);
export const postPath = (id: string) => path(`posts/${id.split('/').map(encodeURIComponent).join('/')}/`);
export const dateLabel = (date: Date) => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(date).replaceAll('-', '.');
