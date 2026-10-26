# 요청한 7개 스킬 소스 비교 — 2026-10-26

## 결론

현재 하네스 전체를 대체할 근거는 없다. **Vercel의 React 성능 규칙을 우선 보강 후보로**, **Addy의 공식 문서 확인·컨텍스트 관리 절차를 두 번째 후보로** 추천한다. 기존 Matt Pocock 설계·진단·TDD 연결은 유지한다. 이는 원문 정적 비교에 따른 판단이며, 모델별 결과 품질·토큰 절감량·실행 성능을 측정한 결론은 아니다.

이번 요청은 다운로드와 비교다. incoming에만 원본을 배치했으며, 새 스킬 활성화, 코어 교체, CLI·의존성 설치, MCP 등록, 훅 실행은 하지 않았다. 기존 5개 레이어와 G0–G7 라우팅을 유지한다.

## 다운로드 결과

7개 공식 소스에서 435개 패키지를 처리했다. 427개 신규 + 기존 Matt Pocock 8개 갱신이며, 전체 incoming은 **538개 패키지 / 554개 SKILL.md**다. 이번 선택 원본 파일 1,787개를 고정 커밋의 Git blob SHA-1과 대조했다. 실행 권한도 Git tree 모드에 맞췄다. 기존 8개는 이미 같은 커밋이므로 내용 변경을 최신화 성과로 주장하지 않는다.

| 소스 | 패키지 | 배치 묶음 | 기존 대비 판단 | 향후 연결 후보 — 아직 미적용 |
| --- | ---: | --- | --- | --- |
| [Archify](https://github.com/tt-a1i/archify) | 1 | documentation/archify | 검증 가능한 HTML 다이어그램 생성에 특화. 설계 판단 자체를 대체하지 않음 | harness-overview-html의 선택적 렌더러 |
| [Vercel React](https://github.com/vercel-labs/agent-skills/tree/063bee94c3f4df8453406c830b0a7df0f2860278/skills/react-best-practices) | 1 | frontend/vercel-agent-skills | 현재 React 코어보다 성능 예제·규칙이 구체적 | react-engineering의 성능 참고자료 |
| [Addy Osmani](https://github.com/addyosmani/agent-skills) | 25 | 각 카테고리/addyosmani-agent-skills | 버전별 공식 문서 확인, 단계별 컨텍스트 보존이 보강 가치 있음 | technology-selection-and-integration, workflow-composition의 조건부 참고자료 |
| [Matt Pocock](https://github.com/mattpocock/skills) | 38 | 각 카테고리/mattpocock-skills | 기존 채택한 설계·진단·TDD 절차 유지. 새 목록은 선택 확장 | to-spec → workflow-composition; writing-for-agents → 문서 지침 후보 |
| [Everything Claude Code / ECC](https://github.com/affaan-m/ECC) | 311 | 각 카테고리/everything-claude-code | 분야별 폭은 넓으나 제어·메모리·자동 실행 계층은 중복 | 언어/기술별 누락 항목만 language-engineering 등에서 검토 |
| [gstack](https://github.com/garrytan/gstack) | 58 | 각 카테고리/gstack | 브라우저 QA·리뷰 절차는 유용하나 공통 프리앰블과 실행 도구 의존 큼 | 브라우저 QA가 실제 필요한 경우 verify-and-handoff 보강 검토 |
| [REA](https://github.com/morluto/rea) | 1 | security/rea | 바이너리·배포 패키지 역공학이라는 별도 기능 공백을 보완 | technology-selection-and-integration에서 선택적 MCP/도구 검토 |

카테고리별 묶음이 반복되어도 소속이 보이도록 기존 `incoming/<category>/<source-bundle>/<package>/` 구조를 유지했다. 세부 전체 경로·커밋·해시는 [후보 레지스트리](../../registry/skill-candidate-review.json)에 있다. ECC의 비개발 업무 스킬도 요청한 묶음의 원본으로 보관하되, 소프트웨어 코어의 기능으로 간주하지 않았다. 카테고리는 탐색용 분류이며 자동 라우팅 조건이 아니다.

## 무엇을 연결하면 나아지는가

### 1. Vercel: 우선 보강

현재 [React 코어](../../skills/react-engineering/SKILL.md)는 상태 소유권, 접근성, 생명주기, 호스트 감지, 검증을 맡는다. Vercel은 70개 규칙을 8개 성능 범주로 나눠 waterfall, 번들, 서버·클라이언트 경계 등의 구체적 예제를 제공한다.

- 제안: React/Next.js 버전과 실제 성능 문제를 확인한 뒤 관련 `rules/*.md`만 선별한다.
- 제외: 전체 AGENTS.md 상시 로딩, Next.js 전용 조언의 React Native 적용, 근거 없는 미세 최적화.
- 기존 `0xbigboss-claude-code/react-best-practices`와 겹치는 성능 내용은 공식 Vercel 원본을 우선 출처로 삼는 것이 합리적이다. 기존 파일은 삭제하거나 대체하지 않았다.
- 접근성·상태 설계·검증 책임까지 Vercel로 교체하면 현재 코어의 범위를 잃으므로 보강으로 한정한다.

### 2. Addy: 작은 절차만 추출

`source-driven-development`의 프로젝트 버전 확인 → 해당 공식 문서 확인 → 구현 → 출처 기록은 API 추측을 줄이는 데 유용하다. 다만 모든 코드 결정마다 검색·인라인 인용을 강제하면 비용과 잡음이 늘 수 있으므로, 버전 의존 API나 불확실한 결정에만 적용하는 편이 맞다.

`context-engineering`은 관련 절만 읽고 세션 경계에서 승인된 결정·작업 상태·검증 근거를 보존한다. 현재 하네스에도 유사 장치가 있으므로 중복 정책 대신 누락된 체크 항목만 비교한다. 프로젝트 소스도 모델 지시 권한을 갖는 것은 아니므로 원문의 신뢰 수준 표현을 그대로 정책화하지 않는다.

`spec-driven-development`는 설치 없는 문서 기반 명세 후보지만, 현재 작업 계약 및 Matt `to-spec`과 중복한다. 작은 수정에 별도 명세 생성을 강제하지 않는다. `using-agent-skills`를 새 라우터로 연결하지 않는다.

### 3. Matt: 현재 선택 유지

기존 codebase-design / improve-codebase-architecture / diagnosing-bugs / tdd / code-review의 선택적 채택을 유지한다. 새 `to-spec`, `writing-for-agents`, `implement-spec` 등은 필요한 산출물에 한정해 비교할 후보다. `skills/in-progress/`의 7개는 실험 상태를 레지스트리에 표시했다. 새로운 패키지를 받았다는 이유로 기존 승인 절차를 확대하지 않는다.

### 4. ECC: 넓은 참고 도서관

`context-budget`은 실제 공급자 상태와 정적 추정치를 구분한다는 장점이 있다. 그러나 특정 앱의 명령을 모든 호스트에서 쓸 수 있다고 가정하면 안 된다. `strategic-compact`는 훅·트랜스크립트·모델별 임계값에 의존하므로 그대로 연결하지 않는다. 자연스러운 작업 경계에서 상태를 저장한다는 원칙만 현재 하네스와 비교한다.

언어·프레임워크별 스킬은 해당 버전 및 현재 프로파일의 빈틈이 확인될 때 읽는다. 자동 학습·메모리·복수 에이전트 오케스트레이션은 현재 상태/승인/Runner와 충돌 가능성이 있어 채택 보류다. 311개 전부를 내용·보안·실행 수준으로 감사한 것은 아니다.

### 5. Archify / gstack / REA: 도구 의존성을 분리

- Archify는 Node 기반 `bin/archify.mjs`와 생성·검증 리소스를 포함한다. 패키지는 받았으나 실행하지 않았다. 선택적 업데이트 조회가 있으며 `ARCHIFY_UPDATE_CHECK_DISABLED=1`로 비활성화하는 설정이 있다. 기존 Mermaid/HTML 표현으로 충분한 작업에는 추가하지 않는 것이 단순하다.
- gstack의 review 등은 `~/.claude/skills/gstack/bin/gstack-skill-start` 실행, 세션 상태, 온보딩·텔레메트리 분기를 포함한다. 이 하네스에 원문을 직접 연결하면 불필요한 초기화·질문·도구 호출을 유발할 수 있다. QA 체크리스트와 실제 브라우저 런타임은 별도로 검토해야 한다.
- REA 원문도 일반 소스 저장소 분석에는 사용하지 말라고 구분한다. 스킬 다운로드만으로 MCP 도구나 분석 엔진이 생기지 않는다. 바이너리/ASAR/펌웨어 분석 요구가 있을 때만 별도 도구 선정 대상으로 둔다.

## 인기도: 설치 수와 별 수를 구분

아래는 이번 조사에서 관찰한 skills.sh의 반올림된 표시값이다. 실시간 전체 사용자 수나 모든 설치 경로의 합계가 아니며, 페이지 캐시 시점도 다를 수 있다. GitHub 별 수를 다운로드 수로 대체하지 않는다. 서로 역할이 다른 스킬을 숫자 하나로 순위 매기지 않는다.

| skills.sh 항목 | 표시 설치 수 | 출처 |
| --- | ---: | --- |
| Vercel React | 839.8K | [카탈로그](https://www.skills.sh/vercel-labs/agent-skills/vercel-react-best-practices) |
| Archify | 175.8K | [카탈로그](https://www.skills.sh/tt-a1i/archify/archify) |
| Addy code-review-and-quality | 73.2K | [카탈로그](https://www.skills.sh/addyosmani/agent-skills/code-review-and-quality) |
| Addy spec-driven-development | 63.3K | [카탈로그](https://www.skills.sh/addyosmani/agent-skills/spec-driven-development) |
| REA | 11.0K | [카탈로그](https://www.skills.sh/morluto/rea/reverse-engineer-anything) |
| ECC strategic-compact | 3.7K | [카탈로그](https://www.skills.sh/affaan-m/ecc/strategic-compact) |
| gstack review | 459 | [카탈로그](https://www.skills.sh/garrytan/gstack/review) |

Matt의 기존 역할별 설치 수는 [10월 25일 비교](popular-skills-2026-10-25.md)를 참조한다. 이를 26일 재측정값으로 취급하지 않는다. 각 저장소의 GitHub 별 수·정확한 커밋은 아래 원본 기록에 별도 보존했다.

## 원본 범위·무결성·라이선스

- `tt-a1i/archify`: `81c6be8d87090670c45d08a8f97f9d29c5af0bec`, GitHub stars 89,544. [원본 매핑](../../incoming/_provenance/tt-a1i__archify/81c6be8d87090670c45d08a8f97f9d29c5af0bec/source-manifest.json).
- `vercel-labs/agent-skills`: `063bee94c3f4df8453406c830b0a7df0f2860278`, GitHub stars 33,033. [원본 매핑](../../incoming/_provenance/vercel-labs__agent-skills/063bee94c3f4df8453406c830b0a7df0f2860278/source-manifest.json).
- `addyosmani/agent-skills`: `aeac41d4d005999432bb7312f7ff06383a91d59d`, GitHub stars 110,643. [원본 매핑](../../incoming/_provenance/addyosmani__agent-skills/aeac41d4d005999432bb7312f7ff06383a91d59d/source-manifest.json).
- `mattpocock/skills`: `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, GitHub stars 303,677. [원본 매핑](../../incoming/_provenance/mattpocock__skills/5beb35b040e3de97e54fa9e386d7e42d15c295c2/source-manifest.json).
- `affaan-m/ECC`: `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, GitHub stars 289,233. [원본 매핑](../../incoming/_provenance/affaan-m__ECC/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b/source-manifest.json).
- `garrytan/gstack`: `8018ba52feab92262087e7236dc10d1b10e8c355`, GitHub stars 137,776. [원본 매핑](../../incoming/_provenance/garrytan__gstack/8018ba52feab92262087e7236dc10d1b10e8c355/source-manifest.json).
- `morluto/rea`: `b675073b731dc3209f59578fad5ca8fe85b104cc`, GitHub stars 388,302. [원본 매핑](../../incoming/_provenance/morluto__rea/b675073b731dc3209f59578fad5ca8fe85b104cc/source-manifest.json).

- ECC의 canonical 저장소는 `affaan-m/ECC`이며 이전 이름은 `affaan-m/everything-claude-code`다. 정식 `skills/`만 수집하고 번역·플랫폼별 중복 사본은 제외했다.
- gstack은 루트 진입점과 1단계 스킬 디렉터리, browser-skills의 제공 스킬을 보관했다. 테스트 fixture와 플랫폼 복제본은 제외했다. 루트 패키지는 SKILL.md만 보관하며 저장소 전체 런타임이 아니다.
- Archify/REA 저장소 내부의 개발 보조 스킬은 제품 스킬과 구분하여 제외했다.
- Addy의 공용 `references/` 원본은 같은 커밋의 `_provenance` 아래 보관했다. 분류로 인해 원문 상대 경로가 원래 저장소처럼 즉시 동작하는 설치 구조는 아니다. 승격 시 참고 파일 매핑을 명시적으로 해결해야 한다.
- 원본 LICENSE/NOTICE/README가 있는 저장소는 해당 파일을 `_provenance`에 보존했다. Vercel 스킬은 frontmatter에 MIT를 선언하지만 해당 커밋에 별도 LICENSE 전문은 발견되지 않았다. 이를 전문 확보 완료로 기록하지 않았으며 승격 전 확인 대상이다.
- 패키지 내부 파일은 수정하지 않았다. 공유 스크립트·외부 명령·런타임 의존성을 모두 실행 가능한 형태로 설치한 것은 아니다.

## 검증 범위

원본 1,787개 blob 대조, 패키지 스냅샷 해시·진입점 목록 확인, 기존 활성 스킬 목록 및 라우팅 불변 확인을 수행했다. 저장소의 문서/계약 단위 테스트와 라우팅 fixture로 인벤토리 변경의 영향을 확인했다. 다운로드된 스킬의 명령은 실행하지 않으며, 토큰 절감이나 모델 간 품질 개선을 실측했다고 주장하지 않는다.

검증 결과: 문서·계약 단위 테스트 **44/44 통과**, 결정적 라우팅 fixture **37/37 통과**, 새 보고서의 로컬 링크 모두 유효, 활성 스킬 정책은 무결성 revision/hash 외 변경 없음. 배치 후 원본 1,787개의 Git blob 및 파일 모드 재검증 통과. 작성한 하네스 문서·레지스트리의 공백 검사 통과. 커밋 전 새 원본 파일까지 포함한 검사에서는 upstream의 trailing whitespace가 검출되었으며 원본 무결성을 위해 그대로 보존했다. 실행 의존성·모델별 품질·토큰 절감량은 미검증이다.
