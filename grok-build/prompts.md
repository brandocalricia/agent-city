# Agent City prompts for Grok Build

Copy-paste prompts from the city's Prompt Workshop, adapted for coding in Grok Build. Fill the `<brackets>`. Short prompts with a clear finish line cost fewer tokens than long back-and-forth. Every change prompt names its checks (before and after) and the tests that must pass.

## 1. Delegate a coding task
```
Goal: <what should change>
Where: <repo path, files or folders>
Context: <issue link, error text, constraints>
Done when: <behavior I can see>
Checks (run before and after): every new file/symbol is referenced and every reference resolves; imports/config load; <lint/typecheck/build command>
Tests (must pass): <1-2 tests that prove it; add them to the test suite, or a scripted smoke test if there is none>
Don't: <files not to touch, no new dependencies, no push>
```

## 2. Plan before editing
```
Before editing anything, read the relevant files and give me a plan in 3-6 steps: files you will touch, the wiring checks you will run before and after (references resolve, nothing orphaned or duplicated, lint/typecheck/build), the 1-2 tests that will prove it, and your assumptions. Wait for my OK.
```

## 3. Check the work
```
Review the diff you just made as a strict reviewer: bugs, edge cases, missing tests, anything that does not match my request. Check the wiring: grep that every new symbol and file is referenced and every reference resolves, no orphaned or duplicate definitions, lint/typecheck/build pass. Fix what you find, run the tests again, and show me the final output.
```

## 4. Let the council decide
```
/city-council Should we <decision>? Repo: <path>. Checks: <before/after wiring checks>. Tests: <1-2 tests that prove it>. Treat it as <Quick|Full>.
```

## 5. Apply the city's suggestions now
```
/city-apply
```

## 6. Explain code for class (intro to CS)
```
Explain <file or function> line by line like a tutor: what each variable holds after each step, for the input <example>. Then give me one tracing question to answer myself, and wait.
```

## 7. Fix a failing test, smallest change
```
Run <test command>. For the first failure, find the root cause, make the smallest fix, and re-run. Do not change the test unless it is wrong; if it is, tell me why first. Then run lint/typecheck/build and the full suite so nothing else broke.
```
