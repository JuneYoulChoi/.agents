# Harness module map

Owner of the module and component names that harness code file headers cite.
A file gains its Korean header when it is next modified; the row exists first.
Rules: [doc and code sync](../../skills/architecture-baseline-and-design/references/doc-code-sync.md).

| 모듈 | 컴포넌트 | 책임 | 코드 경로 |
| --- | --- | --- | --- |
| 하네스 런타임 (scripts) | 라우터 | intake를 G0–G7 게이트 결과와 활성 스킬로 바꾼다 | `scripts/harness_router.py` |
| 하네스 런타임 (scripts) | 작업 계획기 | 작업 단위를 검증하고 배치로 묶는다 | `scripts/harness_workflow.py` |
| 하네스 런타임 (scripts) | Runner | 스킬 결과를 검증하고 작업 상태를 진행한다 | `scripts/harness_runner.py` |
| 하네스 런타임 (scripts) | 위임 기록기 | 워커 패킷과 영수증을 준비·기록한다 | `scripts/harness_delegation.py` |
| 하네스 런타임 (scripts) | 상태 저장소 | 작업 상태와 이벤트를 잠금과 리비전으로 저장한다 | `scripts/harness_state.py` |
| 하네스 런타임 (scripts) | 계약 검증기 | 이식 가능한 계약의 형식을 검증한다 | `scripts/harness_validator.py` |
| 하네스 런타임 (scripts) | 설치기 | 대상 프로젝트에 진입 파일과 설정을 설치하고 소스 무결성을 확인한다 | `scripts/harness_bootstrap.py` |
| 하네스 런타임 (scripts) | 픽스처 실행기 | 픽스처를 라우터·설치기에 넣어 기대 결과와 비교한다 | `scripts/fixture_runner.py` |
| 하네스 런타임 (scripts) | 코드 문서화 검사기 | 한글 파일 헤더와 함수 주석을 검사한다 | `scripts/harness_code_docs.py` |
| 하네스 런타임 (scripts) | 문서 동기화 검사기 | 코드 헤더와 모듈 맵, 문서의 코드 경로 인용을 대조한다 | `scripts/harness_doc_sync.py` |
| 하네스 런타임 (scripts) | 마무리 검사 | 훅 없는 일반 변경의 주석·문서 동기화 검사와 큰 변경 신호 감지 | `scripts/harness_finish.py` |
| 하네스 런타임 (scripts) | 편집 가드 정책 | 두 어댑터의 작업 연동과 편집 판정 | `scripts/harness_edit_guard.py` |
| 하네스 런타임 (scripts) | 개요 스탬프 | 개요가 설명하는 소스의 지문을 계산·기록한다 | `scripts/harness_overview.py` |
| Claude 어댑터 (adapters/claude) | 편집 가드 훅 | 활성 작업 없는 프로젝트 파일 편집을 거부한다 | `adapters/claude/hooks/harness_guard.py` |
| Codex 어댑터 (adapters/codex) | 편집 가드 훅 | apply_patch 편집을 작업 상태에 따라 제한한다 | `adapters/codex/hooks/harness_codex_guard.py` |
| 하네스 테스트 (tests) | 런타임 회귀 테스트 | 라우터·Runner·상태·검증기의 기본 동작 | `tests/test_runtime.py` |
| 하네스 테스트 (tests) | 게이트 경계 회귀 테스트 | 증거·신뢰·순서·재시작 경계 | `tests/test_gate_boundaries.py` |
| 하네스 테스트 (tests) | 게이트 무결성 회귀 테스트 | 게이트 완료·재개·되돌림·라우팅 진입 | `tests/test_gate_integrity.py` |
| 하네스 테스트 (tests) | 코드 문서화 검사기 테스트 | 헤더·함수 주석 검사기 | `tests/test_code_docs.py` |
| 하네스 테스트 (tests) | 문서 동기화 테스트 | 문서 동기화 검사기, 하네스 자체의 맵·개요 일치 | `tests/test_doc_sync.py` |
| 하네스 테스트 (tests) | 강제 수준 테스트 | 큰 변경 판정, 권고 모드, 편집 가드 훅, 마무리 검사 | `tests/test_enforcement.py` |
| 하네스 테스트 (tests) | 기존 회귀 테스트 | 위임·워크플로·intake 결정·전문가 워크플로·문서·ROS MCP | `tests/test_delegation.py`, `tests/test_workflow.py`, `tests/test_intake_decisions.py`, `tests/test_expert_workflow.py`, `tests/test_documentation.py`, `tests/test_ros2_mcp.py` |
