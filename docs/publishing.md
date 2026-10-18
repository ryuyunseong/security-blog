# 검증과 배포

```bash
npm run check
npm test
npm run build
npm run verify
```

각 명령은 타입, 콘텐츠·코드, 정적 페이지, 링크·이미지·검색·RSS·사이트맵을 검사합니다.

GitHub Actions는 main 변경을 검증한 뒤 GitHub Pages로 배포합니다. PR은 검증만 수행합니다. 프로젝트 경로를 적용한 로컬 빌드는 PowerShell에서 다음과 같습니다.

```powershell
$env:SITE_URL = 'https://ryuyunseong.github.io'
$env:BASE_PATH = '/security-blog/'
npm run build
npm run verify
```
