import assessmentCatalog from '../data/assessment-catalog-2026.json' with { type: 'json' };

export { assessmentCatalog };
export const categories = [
  { id: 'critical-infrastructure', label: '주통기', description: '주요정보통신기반시설 점검 항목을 대상과 기준 연도별로 정리합니다.' },
  { id: 'unix', label: 'Unix', description: 'Unix·Linux의 파일 권한, 계정과 셸 동작을 다룹니다.' },
  { id: 'application-security', label: '애플리케이션 보안', description: 'CORS, 접근 제어, 파일 경로와 압축 입력의 안전한 처리를 다룹니다.' },
  { id: 'infrastructure', label: '인프라 보안', description: 'TLS와 인증서 등 시스템·네트워크의 보안 설정을 다룹니다.' },
  { id: 'qualys', label: 'Qualys', description: '인증 스캔, 자산 태그, Cloud Agent 등 Qualys 기능과 공식 문서를 설명합니다.' },
  { id: 'cs-study', label: '전산·NCS', description: '데이터베이스·운영체제·네트워크와 NCS 개념을 예제와 연습문제로 다룹니다.' },
  { id: 'coding-test', label: '코딩 테스트', description: '자료구조·알고리즘 문제를 풀고 복잡도와 경계 조건을 검증합니다.' },
];

// 공식 가이드의 장 순서를 사용하고, 공개 글이 있는 대상·목차만 노출한다.
export const assessmentTargets = assessmentCatalog.targets.map(({ id, label }) => ({ id, label }));
export const assessmentSeries = assessmentCatalog.targets.map((target) => ({
  id: target.series, target: target.id, year: target.year, maxOrder: target.topics.length,
  title: `${target.year} 주요정보통신기반시설 · ${target.label}`,
  route: `critical-infrastructure-${target.id}-${target.year}`,
}));
export const categoryLabel = (id) => categories.find((item) => item.id === id)?.label ?? id;
export const assessmentTargetLabel = (id) => assessmentTargets.find((item) => item.id === id)?.label ?? id;
export const populatedAssessmentTargets = (posts) => assessmentTargets.filter((target) =>
  posts.some((post) => post.category === 'critical-infrastructure' && post.assessmentTarget === target.id));

export function classificationError(data) {
  const target = assessmentTargets.find((item) => item.id === data.assessmentTarget);
  if (data.category === 'critical-infrastructure' && !target) return '주통기 글에는 등록된 점검 대상을 지정하세요.';
  if (data.category !== 'critical-infrastructure' && data.assessmentTarget) return '점검 대상은 주통기 글에만 지정하세요.';
  if (Boolean(data.series) !== Boolean(data.seriesOrder)) return '시리즈와 시리즈 순서를 함께 지정하세요.';
  if (data.series) {
    const series = assessmentSeries.find((item) => item.id === data.series);
    if (!series || data.category !== 'critical-infrastructure' || series.target !== data.assessmentTarget ||
      !Number.isInteger(data.seriesOrder) || data.seriesOrder < 1 || data.seriesOrder > series.maxOrder) return '시리즈의 점검 대상·항목 번호를 대조하세요.';
  }
  return null;
}

// 생성 작업의 kind와 독자가 보는 카테고리는 별도로 관리한다.
export const publicationCategory = (kind) => ({ assessment: 'critical-infrastructure', web: 'application-security',
  qualys: 'qualys', infrastructure: 'infrastructure' })[kind];
