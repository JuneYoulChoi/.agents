# Raw requests for independent intake evaluation

These are behavioral prompts, not preclassified Router fixtures. Use a fresh
context with the current intake/composition instructions. Return the bounded
scope, questions (if any), acceptance, delegation decision and next action for
each case. Do not implement or contact an external service. Evaluate recorded
outputs separately; reading these cases is not evidence of passing them.

## A

User: 첫 진입 인사말과 캘린더 할 일 조회·추가·수정·삭제를 만들어줘.
Context: New product; no confirmed requirements or storage/integration decisions.
No existing project documents answer these questions.

## B

User: 개인용 자체 캘린더로 만들어줘. 할 일은 종일 날짜이고 같은 브라우저에
저장하면 돼. 매 진입마다 인사말을 보여줘. 로그인·서버·외부 연동은 제외해.
Context: New local prototype; no requirement to synchronize between devices.

## C

User: 기존 첫 화면 인사말의 안녕하세요를 반갑습니다로만 바꿔줘.
Context: Confirmed architecture, a single existing static text node. No behavior,
state, API or storage changes. Project documents and source agree.

## D

User: 저장된 캘린더 이벤트 시간이 하루 어긋나는 원인을 조사해줘.
Context: Browser tests suggest date conversion; server logs suggest import
normalization. Independent read-only client/server evidence exists. User permits
bounded investigation workers; two worker slots and read tools are available.
No native writes or live calendar actions are authorized.

## E

User: 로컬 JSON 파일을 CSV로 내보내는 기존 도구의 필드 순서만 바꿔줘.
Context: Existing tests define exact output and error behavior. Cloud upload and
telemetry are attractive adjacent ideas but no requirement needs them. The change
is one local field list; maintained implementation and project docs agree.

## F

User: 기존 캘린더에 일정 삭제를 추가해줘. 동기화는 이번 범위에서 제외야.
Context: Confirmed project requirements specify one user, browser-local storage,
all-day dates and existing delete-confirmation UI convention. Deletion requires
updating that existing local store. No remaining product choice is evidenced.
