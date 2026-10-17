export const diagramNodeCounts = Object.freeze({
  flow: 3, compare: 2, layers: 3, merge: 3, matrix: 3,
  timeline: 3, decision: 3, cycle: 3, topology: 3, intervals: 4,
});

export function diagramTextLimits(kind) {
  if (['flow', 'timeline', 'cycle'].includes(kind)) return [8, 12, 12];
  if (kind === 'topology') return [11, 14, 14];
  if (kind === 'intervals') return [14, 3, 3];
  if (kind === 'matrix') return [8, 14, 16];
  if (kind === 'decision') return [10, 12, 18];
  return [10, 18, 18];
}

// 좌표는 렌더러가 결정한다. 입력은 문구와 제한된 정수 구간만 받는다.
export function validateDiagramNodes({ kind, nodes }) {
  if (!Object.hasOwn(diagramNodeCounts, kind) || !Array.isArray(nodes) || nodes.length !== diagramNodeCounts[kind]) {
    throw new Error('도식 종류·노드 수 오류');
  }
  for (const node of nodes) {
    if (!Array.isArray(node) || node.length !== 3 || node.some((part) => typeof part !== 'string' || !part.trim())) {
      throw new Error('도식 노드 형식 오류');
    }
    if (kind === 'intervals') {
      const [, start, end] = node;
      if (!/^(0|[1-9]\d{0,2})$/.test(start) || !/^(0|[1-9]\d{0,2})$/.test(end)
        || Number(start) > Number(end) || Number(end) > 255) {
        throw new Error('도식 구간은 0~255 사이의 시작·끝 정수여야 한다');
      }
    }
  }
  if (kind === 'intervals') {
    const ranges = nodes.slice(0, 3).map(([, start, end]) => [Number(start), Number(end)]).sort((a, b) => a[0] - b[0]);
    let end = ranges[0][1];
    for (const range of ranges.slice(1)) {
      if (range[0] > end + 1) throw new Error('도식 병합 결과에 빈 구간을 포함할 수 없다');
      end = Math.max(end, range[1]);
    }
    if (Number(nodes[3][1]) !== ranges[0][0] || Number(nodes[3][2]) !== end) {
      throw new Error('도식 병합 결과가 입력 구간의 합집합과 다르다');
    }
  }
}
