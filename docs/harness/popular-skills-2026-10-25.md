# 설치 수를 참고한 스킬 선정과 연결 — 2026-10-25

사용자 요청: CLI 설치 없이 원본을 `incoming`에 다운로드하고, 같은 역할이면
더 많이 사용되는 스킬을 우선 구성한다. 목표는 요구사항 오해·추측성 수정·잘못된
완료 보고를 줄이면서 토큰 비용과 불필요한 설계를 억제하는 것이다.

## 선정 결과

수치는 확인 당시 skills.sh 페이지의 **Installs 표시값**이다. 반올림된 값이며
개별 페이지에 집계 기간은 명시되지 않았다. 고유 사용자 수·실제 실행 횟수·GitHub
별 수와 다르다. 전체 생태계 1위라는 주장 없이 비교한 역할별 후보 중 선정했다.

| 역할 | 선정 원본 / 설치 수 출처 | 표시값 | 실행 연결 |
| --- | --- | ---: | --- |
| 요구사항 구체화 | [superpowers / brainstorming](https://www.skills.sh/obra/superpowers/brainstorming) | 405.2K | G3 greenfield-planning → task-contract 참조 |
| 작고 명확한 구현 계획 | [superpowers / writing-plans](https://www.skills.sh/obra/superpowers/writing-plans) | 283.5K | G3 workflow-composition → 같은 task-contract 재사용 |
| 신규·기존 모듈 설계 | [mattpocock / codebase-design](https://www.skills.sh/mattpocock/skills/codebase-design) | 854.7K | G5 architecture-and-design-patterns → module-design 참조 |
| 기존 구조의 개선 판단 | [mattpocock / improve-codebase-architecture](https://www.skills.sh/mattpocock/skills/improve-codebase-architecture) | 1.2M | 구조 변경 근거가 있는 같은 G5 참조 |
| 원인 중심 버그 진단 | [mattpocock / diagnosing-bugs](https://www.skills.sh/mattpocock/skills/diagnosing-bugs) | 839.5K | G3 brownfield-impact-analysis → diagnosis 참조 |
| 행동 중심 테스트 | [mattpocock / tdd](https://www.skills.sh/mattpocock/skills/tdd) | 1.1M | G6 implementation-quality → behavior-tests 참조 |
| 요청·규칙 대비 리뷰 | [mattpocock / code-review](https://www.skills.sh/mattpocock/skills/code-review) | 794.0K | G7 verify-and-handoff → acceptance-review 참조 |
| 완료 주장 검증 | [superpowers / verification-before-completion](https://www.skills.sh/obra/superpowers/verification-before-completion) | 252.3K | 같은 G7 참조에서 증거 확인 |

## 비교와 제외 이유

| 비교 역할 | 다른 후보 / 표시값 | 결정 |
| --- | --- | --- |
| 버그 진단 | [systematic-debugging](https://www.skills.sh/obra/superpowers/systematic-debugging) 307.3K | 같은 역할에서 더 높은 diagnosing-bugs를 주 참조로 채택. 두 절차를 연속 실행하지 않음 |
| TDD | [test-driven-development](https://www.skills.sh/obra/superpowers/test-driven-development) 260.0K | 더 높은 mattpocock/tdd 채택. 기존 코드를 지우고 다시 쓰는 절차는 불필요 |
| 계획·상태 유지 | [planning-with-files](https://www.skills.sh/othmanadi/planning-with-files/planning-with-files) 46.9K | planning과 일부 역할 중복. 기존 task store와 hooks를 이중화하지 않고 writing-plans의 계획 원칙만 사용 |
| 완료 검사 | [verify-and-stop](https://www.skills.sh/juliusbrussee/caveman/verify-and-stop) 103.0K | 주 검증 근거는 verification-before-completion. 기존의 유효한 검사 재사용·종료 원칙은 유지 |
| 구현 단순화 | [lean-build](https://www.skills.sh/juliusbrussee/caveman/lean-build) 100.0K | 설계/TDD와 완전한 대체 관계가 아님. 기존 작은 완결 단위·과잉구현 금지 원칙을 보존하며 별도 실행 체인은 추가하지 않음 |
| 설계 인터뷰 | [grill-me](https://www.skills.sh/mattpocock/skills/grill-me) 1.4M, [grill-with-docs](https://www.skills.sh/mattpocock/skills/grill-with-docs) 1.2M | 높은 설치 수지만 현재 엔트리포인트는 다른 스킬 호출용. 기존 문서 우선 확인은 유지하고, 일반 작업의 주 경로에 추가 인터뷰 체인을 연결하지 않음 |

인기 점수로 라우팅하지 않는다. 동일 역할의 호환 가능한 후보를 선정할 때만
사용량을 참고한다. `code-review`는 요청 대비 리뷰이고
`verification-before-completion`은 완료 증거 확인이므로 둘은 서로를 대체하지 않는다.
원본 대안은 삭제하지 않고 기존 카테고리에 보관한다.

## 다운로드와 출처

8개 패키지의 총 26개 파일을 공식 최신 커밋에서 **실제로 다시 다운로드해 교체**했다.
Git blob SHA-1과 내려받은 모든 파일의 바이트를 대조했다. 기존 파일도 같은
내용이어서 원본 본문의 변경분은 없다. 새 커밋·라이선스·파일 해시·설치 지표는
[후보 레지스트리](../../registry/skill-candidate-review.json)에 기록했다.

- Superpowers: `2ce8aa15d05bd57213e6f746f953aafb7ded7a8b`, MIT.
  [원본 라이선스](../../incoming/_provenance/obra__superpowers/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/LICENSE)
- Matt Pocock: `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, MIT.
  [원본 라이선스](../../incoming/_provenance/mattpocock__skills/5beb35b040e3de97e54fa9e386d7e42d15c295c2/LICENSE)

분류는 `incoming/<category>/<bundle>/<package>/`를 유지한다.
brainstorming/writing-plans는 workflow/superpowers, verification은 quality/superpowers,
설계 두 패키지는 architecture/mattpocock-skills, 진단/TDD/리뷰는
quality/mattpocock-skills에 있다. 전체는 여전히 111개 패키지 / 127개 SKILL.md다.

## 실제 연결 방식과 비용 제한

```text
incoming 원본 + 고정 커밋·라이선스·설치 수
    → 검토한 절차만 기존 skills의 짧은 참조로 반영
    → 기존 G3 / G5 / G6 / G7에서 조건에 맞을 때 읽기
    → 기존 task record에 수락 조건과 실제 검증 증거 연결
```

연결된 참조:
[작업 계약](../../skills/workflow-composition/references/task-contract.md),
[진단](../../skills/brownfield-impact-analysis/references/diagnosis.md),
[모듈 설계](../../skills/architecture-and-design-patterns/references/module-design.md),
[행동 테스트](../../skills/implementation-quality/references/behavior-tests.md),
[수락·규칙 검토](../../skills/verify-and-handoff/references/acceptance-review.md).

원본은 실행하지 않는다. CLI·npm 의존성·MCP·자동 hook·전역 스킬을 설치하지 않았다.
5개 레이어, G0–G7, 25개 활성 스킬, Router/Runner와 adapter 계약을 유지한다.
추가된 네 후보(brainstorming, diagnosing-bugs, tdd, code-review)의 일부 절차를
검토·반영하여 선택적 adaptation 출처는 16개에서 20개가 되었다.

강제 질문·재승인, 전체 저장소 구조 탐색, 고정 가설 수, 병렬 설계 경쟁,
매 작업 다중 리뷰, 이슈 트래커 설정, CDN HTML, 자동 커밋, 기존 코드 삭제는
채택하지 않았다. 기존 SOLID/GRASP·오류/수명/동시성 기준은 그대로 적용한다.
테스트는 중요한 행동과 회귀를 증명할 때 사용하며, 단순 문서·외형 변경에는
구현을 그대로 따라 쓰는 테스트를 추가하지 않는다.

## 검증과 한계

2026-10-26 마무리 결과:

| 검사 | 결과 |
| --- | --- |
| `python3 -B -m unittest discover -s tests -v` | 44개 통과. 후보 해시·문서 링크·활성 스킬 배치·기존 런타임 검사 포함 |
| `python3 -B scripts/fixture_runner.py --artifact-dir <temporary-directory>` | 37개 통과. 기존 게이트·adapter·워크플로 fixture 회귀 확인 |
| 수정한 코어 6개의 `quick_validate.py` | 모두 통과 |
| 다운로드 파일·라이선스 | 26개 파일의 Git blob과 원본 실행 권한, 두 라이선스 원본 확인 |
| 연결 근거 | 원본 8개 → 승인된 참조 5개 → 코어 소유자 6개의 직접 링크 확인 |
| 무결성·변경 범위 | 소스/레지스트리 핀 갱신, `git diff --check`, OpenSpec 미설치 상태 확인 |

모델의 실제 판단·토큰 절감·모델 간 편차는 별도 검토 대상이며 이번 작업의
자동 검사 결과와 구분한다. 독립 모델 평가는 실행하지 않았다. 절차 연결은
스킬 지침 수준이며, 새로운 코드 기반 강제 게이트를 구현한 것은 아니다.
검토되지 않은 원본의 scripts/hooks와 sibling 스킬은 계속 비활성이다.
유지보수 근거는 `/tmp/popular-skills-20261025/`에 보관한다.

다른 모델은 원본을 실행하지 말고 이 문서의 선정/제외 범위, 승인 스킬의 조건부
참조, 일반 버그의 구조 리뷰 억제, 미실행 검증의 완료 오인 여부를 검토하면 된다.
커밋은 요청되지 않아 수행하지 않는다.
