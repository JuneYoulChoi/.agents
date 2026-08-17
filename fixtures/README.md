# Harness fixture runner

A fixture is a controlled integration-test scenario for the engineering
harness itself. It is not a product test. Router fixtures supply a context and
expected activated/suppressed skills, gates, feedback, revisions, and events.
Bootstrap fixtures create isolated target directories and assert install,
idempotence, preservation, and conflict results.

Run the optional standard-library reference provider from the harness root:

```sh
python3 -B scripts/fixture_runner.py
```

The runner discovers JSON fixtures recursively under `fixtures/`, invokes a
Router adapter with `--input <json> --output <json>` or a Bootstrap provider's
`install` command, and exits nonzero if any assertion fails. It prints the
fixture ID, expected state, actual state, durable temporary artifact path, and
final pass/fail count. Each provider call has a 30-second default timeout; use
`--timeout-seconds` only when a reviewed adapter needs a different bound.

Python is not a Core or target-project requirement. Test another conforming
adapter by replacing the command:

```sh
python3 -B scripts/fixture_runner.py \
  --adapter-command './path/to/native-router'
```

Use `--bootstrap-command` in the same way for another conforming installer.

The alternate command may be implemented in C++, Rust, Go, Java, Shell, or a
platform-native runtime. It passes only when it implements the same JSON file
transport and observable routing semantics. Do not put secrets or live
production endpoints in fixture inputs.

Current executable coverage is 22 cases: four F-017 routing cases, four
Bootstrap-conflict cases, five configuration-routing cases, six
technology-composition cases, and three adaptive execution-profile cases.
`python3 -B -m unittest discover -s tests -v` adds seven focused
State/Runner/Validator checks. This bounded suite does not
claim platform-native hooks, external runtime availability, or every possible
technology/configuration Cartesian product.
