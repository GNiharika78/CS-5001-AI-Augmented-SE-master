<!-- You are a software engineer refactoring Python code.

## Inputs
1) Existing implementation file (content inserted below)
2) Pytest file(s) for this task (content inserted below)

## Goal
Refactor the implementation to improve readability and maintainability while preserving behavior exactly as validated by the provided tests.


## Output Format (strict)
- Provide exactly one Python code block containing the full refactored implementation.
- After the code block, provide the checklist in 5 to 10 bullets.
- Do NOT include any additional text.

---

## Implementation file content
<<<IMPLEMENTATION>>> -->
<!-- You are a software engineer refactoring Python code.

## Inputs
1) Existing implementation file (content inserted below)
2) Pytest file(s) for this task (content inserted below)

## Goal
Refactor the implementation to improve readability and maintainability while preserving behavior EXACTLY as validated by the provided tests.

Behavior preservation is mandatory. Readability improvements are secondary.

## Mandatory Rules (must follow all)
1) Preserve the public API exactly:
   - Do NOT rename, remove, or add any functions referenced by the tests.
   - Keep function names, parameters, return values, and exceptions unchanged.
2) Preserve semantics exactly:
   - Do NOT fix bugs, correct formulas, or change logic even if it seems wrong.
   - Preserve edge cases, quirks, and unusual behavior.
   - Preserve distinctions such as None vs False, int vs float, ordering, ties, and rounding.
3) Keep all functions at module scope:
   - Do NOT nest functions or wrap code inside classes.
4) Do NOT change imports in a way that affects test imports:
   - No new dependencies.
   - Use only Python standard library.
5) No side effects:
   - No print statements, logging, input/output, randomness, or timing.
6) Refactor conservatively:
   - Prefer renaming local variables, simplifying control flow, removing duplication.
   - Avoid algorithm changes or “Pythonic” rewrites unless behavior is provably identical.
7) If behavior is unclear, defer to the original implementation and tests.

## Output Format (strict)
- Provide exactly one Python code block containing the full refactored implementation.
- After the code block, provide a checklist with 5 to 10 bullets confirming the above rules were followed.
- Do NOT include any additional text.

---

## Implementation file content
<<<IMPLEMENTATION>>> -->


You are a software engineer refactoring Python code.

## Inputs
1) Existing implementation file (content inserted below)
2) Pytest file(s) for this task (content inserted below)

## Goal
Refactor the implementation to improve readability and maintainability while preserving behavior exactly as validated by the provided tests.

Behavior preservation is mandatory. Readability is secondary.

## Mandatory Rules (must follow all)
1) Preserve the public API exactly:
   - Do NOT rename, remove, or add any functions referenced by tests.
   - Keep the same function names, parameters, defaults, return values/types, and raised exceptions.
2) Preserve semantics exactly:
   - Do NOT fix bugs, “correct” math, or change logic even if it seems wrong.
   - Preserve quirks and edge cases (including None vs False, ordering, ties, rounding, int vs float).
3) Keep functions at module scope:
   - Do NOT wrap code in classes.
   - Do NOT nest the main function inside another function.
4) No new dependencies:
   - Use only Python standard library.
   - Do not introduce third-party imports.
5) No side effects:
   - No print/logging, no input/output, no randomness, no time-based behavior.
6) Refactor conservatively:
   - Prefer renaming local variables, simplifying control flow, removing duplication.
   - Avoid algorithm substitutions unless obviously equivalent to the original.

## Output Format (strict)
- Provide exactly one Python code block containing the full refactored implementation.
- After the code block, provide the checklist in 5 to 10 bullets confirming you followed the rules above.
- Do NOT include any additional text.

---

## Implementation file content
<<<IMPLEMENTATION>>>
