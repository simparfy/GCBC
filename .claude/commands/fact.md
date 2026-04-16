# /fact — Add a non-negotiable constraint

Record a non-negotiable constraint or hard requirement. Facts are global across all cases and appear in every verdict's Non-Negotiables section.

## Arguments

`$ARGUMENTS` = the fact statement.

## Process

### Step 1: Validate

If `$ARGUMENTS` is empty:
```
Usage: /fact <statement>
Example: /fact Must support offline mode
Example: /fact API response time must be under 200ms
```
Then stop.

### Step 2: Add fact

Run:
```bash
python -m gcbc.cli add-fact --statement "$ARGUMENTS"
```

Parse the JSON result.

If `added` is `false` and `reason` is `"duplicate"`:
```
This fact is already recorded. Existing facts:
```
Then read and display the contents of `facts.md`.

If `added` is `true`:
```
Fact recorded: "$ARGUMENTS"

This will appear in the Non-Negotiables section of all verdicts.
```
