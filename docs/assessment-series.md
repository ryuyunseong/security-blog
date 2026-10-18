# 주통기 항목 데이터

2026 KISA 가이드의 12개 대상과 382개 항목입니다.

| 순서 | 대상 ID | 표시 이름 | 항목 | 편수 |
| --- | --- | --- | --- | --- |
| 1 | unix | Unix | U-01~U-67 | 67 |
| 2 | windows | Windows 서버 | W-01~W-64 | 64 |
| 3 | web-service | 웹 서비스 | WEB-01~WEB-26 | 26 |
| 4 | security-device | 보안 장비 | S-01~S-23 | 23 |
| 5 | network-device | 네트워크 장비 | N-01~N-38 | 38 |
| 6 | control-system | 제어시스템 | C-01~C-51 | 51 |
| 7 | pc | PC | PC-01~PC-18 | 18 |
| 8 | dbms | DBMS | D-01~D-26 | 26 |
| 9 | mobile | 이동통신 | M-01~M-04 | 4 |
| 10 | web-application | 웹 애플리케이션 | CI, SI 등 가이드 항목순 | 21 |
| 11 | virtualization | 가상화 장비 | HV-01~HV-25 | 25 |
| 12 | cloud | 클라우드 | CA-01~CA-19 | 19 |

원본은 [KISA 공식 게시물](https://www.kisa.kr/2060204/form?postSeq=22&page=1)의 첨부 PDF입니다. SHA-256은 `44fe393981b244147be6af7423d99dc15633c089fad0bcb296cbe2371dde812d`입니다.

C-39·HV-09의 중요도는 항목표와 본문이 달라 항목표 471·788쪽의 하·중을 사용합니다. 자동화 공격의 본문 777쪽 코드는 CC이지만 항목표 678쪽의 AU를 사용합니다. 차이는 `importanceNote`, `pdfCode`, `codeNote`에 보관되어 있습니다.

`src/data/assessment-catalog-2026.json`은 대상별 코드·제목·중요도·PDF 페이지 범위를 담고 있습니다.

대상별 목록은 `/categories/critical-infrastructure/대상-ID/`, 연도별 목차는 `/series/critical-infrastructure-대상-ID-2026/`입니다. 공개 글이 있는 목록만 생성됩니다. 웹 서비스(`web-service`, WEB 코드)와 웹 애플리케이션(`web-application`, CI·SI 등)은 별도 대상입니다.
