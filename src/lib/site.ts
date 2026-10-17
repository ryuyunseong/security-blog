import { createPath } from './core.mjs';

export const siteInfo = {
  title: '보안 노트',
  description: 'Unix 점검 방법, 웹 보안 실습, Qualys 기능을 정리합니다.',
  github: 'https://github.com/ryuyunseong',
  portfolio: 'https://ryuyunseong.github.io/security-portfolio/',
};

export const categories = [
  { id: 'unix', label: 'Unix', description: '계정·그룹, 파일 권한, SSH 설정과 주통기 점검 항목을 다룹니다.' },
  { id: 'web', label: '웹 보안', description: 'CORS, 인증·권한 검사, 파일 다운로드와 압축 해제의 보안 문제를 다룹니다.' },
  { id: 'infrastructure', label: '인프라 보안', description: 'TLS 인증서 검증, CIDR 주소 조회, 로그인 실패 로그 분석을 다룹니다.' },
  { id: 'qualys', label: 'Qualys', description: '인증 스캔, 자산 태그, Cloud Agent 등 Qualys 기능과 공식 문서를 설명합니다.' },
] as const;

export const path = createPath(import.meta.env.BASE_URL);
export const postsPerPage = 12;
export const archivePath = (page = 1) => path(`archive/${page}/`);
export const unixSeries = {
  id: 'unix-2026',
  title: '2026 주요정보통신기반시설 · Unix',
  path: path('series/critical-infrastructure-unix-2026/'),
};
export const categoryLabel = (id: string) => categories.find((category) => category.id === id)?.label ?? id;
export const tagPath = (tag: string) => path(`tags/${encodeURIComponent(tag)}/`);
export const postPath = (id: string) => path(`posts/${id.split('/').map(encodeURIComponent).join('/')}/`);
export const dateLabel = (date: Date) => new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Seoul' }).format(date).replaceAll('-', '.');
