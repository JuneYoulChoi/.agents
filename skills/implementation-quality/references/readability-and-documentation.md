# Readability and code documentation

Required for every authored code file that a task creates or modifies. It
applies with the `core` profile, in Greenfield and Brownfield work alike, and is
checked at G6 by `scripts/harness_code_docs.py`. Generated code, vendored or
third-party code, and files whose format has no comment syntax (JSON, lock
files, binary assets) are exempt; record the exemption with its reason.

## 1. Fix the readability standard before writing

Record one `readability_standard` in the implementation-quality result:

1. the project's formatter/linter configuration when it exists and is
   maintained (it wins over the defaults below);
2. otherwise the language's common guide (for example PEP 8, Google Java Style,
   Effective Go, the TypeScript/ESLint recommended set) plus these defaults.

Defaults that every change follows unless the recorded standard says otherwise:

- Names state intent in the domain's language; no unexplained abbreviations,
  single letters only for short loop indices or established math notation.
- One function does one thing at one level of abstraction. Treat more than
  about 40 lines, more than 3 levels of nesting or more than 4 parameters as a
  review trigger: split, return early or introduce a parameter object unless
  the recorded reason says the longer form is clearer.
- Prefer early returns and guard clauses over deep `else` chains.
- Replace magic numbers and strings with named constants or configuration.
- Keep error paths explicit and visible; never swallow an error silently.
- Order a file top-down: header, imports, constants, types, public entry
  points, then helpers. Keep related code together.
- Comments explain purpose, constraints and non-obvious decisions ("why"); do
  not restate the code. Never leave commented-out code.
- Follow the existing formatting of a Brownfield file; do not reformat
  unrelated lines.

## 2. File header (Korean, always)

Every authored code file that is created or modified starts with a Korean
header comment, placed after only a shebang, an encoding line or a
language-required first line. It has exactly these labelled lines:

- `모듈:` the architecture module (LLD/module record) the file belongs to;
- `컴포넌트:` the component inside that module;
- `역할:` what this file is responsible for, in one or two sentences.

Use the names from the architecture baseline. If the baseline has no module or
component for the file, that is a G2 gap: record it rather than inventing one.

```python
"""
모듈: 주문 처리 (order)
컴포넌트: 결제 검증기
역할: 결제 요청의 금액·통화·한도를 검증하고 거절 사유를 반환한다.
"""
```

## 3. Function comments (Korean, every function)

Every named function and method that is created or modified, public or
private, has a Korean doc comment directly above or inside it (by language
convention) containing:

- `역할:` what the function does and why it exists;
- `입력:` the meaning of each parameter (required when it has parameters;
  `self`/`cls`/receivers are excluded);
- `출력:` the meaning of the return value or produced output (required when it
  returns a value, yields, or writes the result for its caller);
- `예외:` the errors it raises or returns, when it has any.

A short private function without parameters or result still needs `역할:`.
Anonymous inline lambdas and closures passed as arguments are exempt. Describe
meaning and units, not the type that the signature already shows.

```python
def validate_amount(amount: int, limit: int) -> list[str]:
    """
    역할: 결제 금액이 0보다 크고 한도 이하인지 확인한다.

    입력:
        amount: 결제 금액(원)
        limit: 사용자 일일 한도(원)
    출력:
        위반 사유 목록. 비어 있으면 유효하다.
    """
```

## 4. Comment syntax by language

| Language | File header | Function comment |
| --- | --- | --- |
| Python | module docstring (or leading `#` block) | docstring as the first statement |
| JavaScript / TypeScript | `/** ... */` at the top | `/** ... */` (JSDoc) above the function |
| Java / C# / C / C++ | `/** ... */` or `//` block at the top | `/** ... */`, `///` or `//` block above the signature |
| Go | `//` block above `package` | `//` block above `func` |
| Rust | `//!` lines at the top | `///` lines above `fn` |
| Shell | `#` block after the shebang | `#` block above the function |
| HTML / CSS | `<!-- -->` / `/* */` at the top | not applicable |

Decorators, annotations and attributes may sit between the comment and the
signature.

## 5. Brownfield scope and verification

For a modified existing file, add or update the header and document every
function that the change creates or modifies; untouched functions are
documented when they are next changed. Do not reformat or re-comment the whole
file in an unrelated change.

Before completing G6 run:

```text
python3 -B <harness>/scripts/harness_code_docs.py --target-root <project> \
  [--base <revision>] <changed files...>
```

`--base` limits function checks to functions whose lines changed since that
Git revision; without it every function is checked. Submit the same files and
base in `implementation_quality.documentation_check`; the Runner re-runs the
check and rejects completion on any violation. The checker uses lightweight
parsing outside Python, so it can miss unusual signatures: it proves the
comments exist and carry the required labels, not that their content is
accurate. The reviewer still reads them.
