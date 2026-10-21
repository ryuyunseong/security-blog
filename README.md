# 보안 노트

주요정보통신기반시설 점검과 Unix·애플리케이션·인프라 보안을 공부하며 정리한 글입니다. Qualys 기능 해설, 코딩 테스트 풀이와 전산·NCS 학습 예제도 다룹니다.

[블로그](https://ryuyunseong.github.io/security-blog/) · [주통기 시리즈](https://ryuyunseong.github.io/security-blog/series/critical-infrastructure-unix-2026/) · [전산·NCS](https://ryuyunseong.github.io/security-blog/categories/cs-study/)

## 로컬 실행

Node.js 22.22 이상이 필요합니다.

```bash
npm ci
npm run dev
```

기본 주소는 http://localhost:4321/ 입니다.

```bash
npm run check
npm test
npm run build
npm run verify
```

타입·콘텐츠 검사 후 페이지의 링크·이미지·앵커와 검색·RSS·사이트맵을 대조합니다. main 변경은 검증을 거쳐 GitHub Pages로 배포됩니다.

## 구성

- `src/content/posts/`: 글 원문. 초안과 미래 날짜 글은 사이트에서 제외됩니다. 저장소의 원문은 공개됩니다.
- `src/data/article-visuals.json`: 설명 도식.
- `src/data/executions.json`: 예제의 실제 출력·환경·코드 해시.
- `src/data/execution-context.json`: 실습 범위와 결과 해석.
- `templates/post.md`: 글 메타데이터 예시.

```bash
node scripts/build-article-diagrams.mjs
```

Linux에서 기존 17편의 예제를 재현하는 명령입니다. Python·Bash·awk·GNU stat·OpenSSH·OpenSSL·libacl을 사용합니다. 가상 파일과 루프백만 사용하며 운영 계정·PAM·SSH 설정은 변경하지 않습니다. 사이트 빌드는 실습을 실행하지 않습니다.

```bash
python3 scripts/run-article-examples.py
```

- [콘텐츠 형식](docs/content-plan.md)
- [주통기 항목 데이터](docs/assessment-series.md)
- [도식과 실행 기록](docs/article-media.md)
- [검증과 배포](docs/publishing.md)

## 글별 실습 파일

각 글의 실습이 시작되는 부분에서 코드·입력 파일·실행 안내를 ZIP으로 내려받을 수 있습니다. 압축 안의 `README.md`에 도구, 실행 위치와 예상 종료 코드가 있습니다. [묶음 파일 형식과 생성 방법](docs/practice-bundles.md)을 참고하세요.
