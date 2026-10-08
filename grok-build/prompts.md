# Agent City prompts for Grok Build

Copy-paste prompts from the city's Prompt Workshop, adapted for coding in Grok Build. Fill the `<brackets>`. Short prompts with a clear finish line cost fewer tokens than long back-and-forth.

## 1. Delegate a coding task
```
Goal: <what should change>
Where: <repo path, files or folders>
Context: <issue link, error text, constraints>
Done when: <tests that pass / command output / behavior I can see>
Don't: <files not to touch, no new dependencies, no push>
```

## 2. Plan before editing
```
Before editing anything, read the relevant files and give me a plan in 3-6 steps: files you will touch, the test you will run, and your assumptions. Wait for my OK.
```

## 3. Check the work
```
Review the diff you just made as a strict reviewer: bugs, edge cases, missing tests, anything that does not match my request. Fix what you find, run the tests again, and show me the final test output.
```

## 4. Let the council decide
```
/city-council Should we <decision>? Repo: <path>. Treat it as <Quick|Full>.
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
Run <test command>. For the first failure, find the root cause, make the smallest fix, and re-run. Do not change the test unless it is wrong; if it is, tell me why first.
```
