# Keeping documents and code in agreement

Use whenever a task creates or changes architecture documents or authored code.
The aim is that a structural code change and its document change always land
together, and that neither side is edited more than the change requires.

## 1. Documents hold structure, code holds detail

| Belongs in a design document | Belongs only in code and its comments |
| --- | --- |
| module and component names, responsibilities | field lists, parameter lists, default values |
| public interfaces and their contracts | conditions, branches, algorithms |
| dependency direction, data ownership | helper functions, private state |
| decisions and their reasons (ADR) | values that the code already states |

A document that restates code detail goes stale on the next local edit. Remove
the restatement and point to the code path instead.

## 2. One owner per fact

Every fact has one owning document; other documents link to it and do not copy
it. When code owns the fact (an enumeration, a schema, a default), the document
names the code path and does not list the values.

## 3. Edit in place, by keyword

- Change the sentence or table row that states the old fact, where it stands.
  Do not append a dated section that leaves the old statement in place; history
  belongs to version control and one change log.
- Touch only the lines that contain the changed structural keyword (the
  component, interface or path name). Do not reword or reformat neighbours.
- Search every document for the old keyword before finishing; a removed or
  renamed name must not survive anywhere.

## 4. What a code change requires of the documents

| Code change | Document change |
| --- | --- |
| function body, private helper, bug fix inside a component | none |
| new, removed, moved or renamed code file inside an existing component path | none when the path in the module map still covers it; otherwise that row's path |
| new, removed, renamed or split component or module | the module map row, and the views or LLD entries that name it |
| changed public interface or contract | the owning interface entry only |
| changed dependency direction or data owner | the owning view or LLD entry, and an ADR when it is a decision |

## 5. Module map: the link between both sides

Keep one table at `docs/architecture/module-map.md` (another path may be passed
to the checker). It is the owner of module and component names:

```markdown
| 모듈 | 컴포넌트 | 책임 | 코드 경로 |
| --- | --- | --- | --- |
| 주문 처리 (order) | 결제 검증기 | 결제 요청의 금액과 한도를 검증한다 | `src/order/payment` |
| 주문 처리 (order) | 주문 저장소 | 주문을 저장하고 조회한다 | `src/order/repo.py`, `src/order/schema.py` |
```

- `코드 경로` lists project-relative files or directories, comma-separated.
  Prefer a directory so that files can come and go without a document edit.
- The `모듈:` and `컴포넌트:` lines of every code file header repeat a row of
  this table exactly, and the file lies under that row's path.

## 6. Check

```text
python3 -B <harness>/scripts/harness_doc_sync.py --target-root <project> \
  [--map docs/architecture/module-map.md] [--base <revision>] [<changed code files...>]
```

It reports a header that names no map row, a file outside its row's path, a map
path that no longer exists, and a backticked code path in the documents beside
the map that no longer exists. With `--base` it also checks every code file
added or modified since that revision, except files in the map's own document
folder and `--exclude` prefixes (generated or vendored code). The Runner runs it when G6 completes.
It compares names, paths and existence; whether a description still matches
the behavior is a reviewer's judgment.
