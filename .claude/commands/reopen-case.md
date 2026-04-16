# /reopen-case — Reopen an archived case

Reopen a previously closed, split, or merged case.

## Arguments

`$ARGUMENTS` = the case slug to reopen.

## Process

### Step 1: Validate

If `$ARGUMENTS` is empty, list available cases:
```bash
python -m gcbc.cli list
```

Display all non-open cases in a table:
```
Available cases to reopen:

| Slug | Title | Status |
|------|-------|--------|--------|
[filtered rows where status != "open"]

Usage: /reopen-case <slug>
```
Then stop.

### Step 2: Check for conflict

```bash
python -m gcbc.cli status
```

If an active case exists:
```
Close current case [slug] first with /close-case before reopening another.
```
Then stop.

### Step 3: Reopen

```bash
python -m gcbc.cli reopen --slug "$ARGUMENTS"
```

On success:
```
Case reopened: [slug] — [title]
Continuing from where you left off.

Run /interrogate to continue or /investigate for new evidence.
```

On error, display the error message.
