# /split-case — Split active case into child cases

Split the active case into multiple child cases. The parent gets status "split" and children inherit context.

## Arguments

`$ARGUMENTS` = comma-separated child case names.

## Process

### Step 1: Load active case

```bash
python -m gcbc.cli status
```
If no active case, stop with error.

```bash
python -m gcbc.cli context
```

### Step 2: Parse or suggest

If `$ARGUMENTS` is empty, spawn GC and BC in parallel with `model: "opus"` to **suggest** a split:

**GC agent:**
```
You are GOOD COP analyzing this case for a potential split.

Review the case context and propose how to divide it into separate, focused sub-cases.
For each proposed child, explain what it would cover and why splitting helps.

Return format:
PROPOSED_SPLIT: [child1], [child2], [child3 if needed]
RATIONALE: [Why this split makes sense]
CHILD_DESCRIPTIONS:
- child1: [what it covers]
- child2: [what it covers]

<case_context>
{CONTEXT}
</case_context>
```

**BC agent:** (same structure, independent perspective)

Display both proposals and ask the user to choose or provide their own:
```
GC suggests: [GC proposal]
BC suggests: [BC proposal]

Run /split-case [child1, child2, ...] with your chosen split.
```
Then stop.

### Step 3: Execute split

If `$ARGUMENTS` is provided:
```bash
python -m gcbc.cli split --children "$ARGUMENTS"
```

Then spawn GC and BC in parallel with `model: "sonnet"` to write scoped descriptions for each child case. For each child, the agent rewrites the child's case.md description to be focused on that specific aspect.

Display:
```
Case split: [parent-slug]

Children created:
- [child-slug-1]: [description]
- [child-slug-2]: [description]

Parent status set to "split". Open a child with /reopen-case [child-slug].
```
