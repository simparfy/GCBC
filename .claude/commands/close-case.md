# /close-case — Archive the current case

Close and archive the current open case.

## Process

### Step 1: Load active case

Run:
```bash
python -m gcbc.cli status
```
If no active case: "No open case to close." Then stop.

### Step 2: Check for verdict

Check if `.gcbc/cases/{slug}/verdict.md` exists by reading it.

If verdict.md does NOT exist:
```
Warning: This case has no verdict yet.

Options:
- Run /debate to generate a verdict first
- Run /interrogate to continue investigation
- Type /close-case again to close anyway without a verdict
```

Check if `$ARGUMENTS` contains "force" or if this is a second invocation. If not, stop and let the user decide.

### Step 3: Close

```bash
python -m gcbc.cli close
```

Display:
```
Case closed: [slug] — [title]

Files preserved in .gcbc/cases/[slug]/
Reopen with: /reopen-case [slug]
```
