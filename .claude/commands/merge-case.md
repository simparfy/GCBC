# /merge-case — Intelligently merge a case into the active case

Merge a target case into the active case. GC and BC rewrite all files to synthesize both cases — this is an intelligent merge, not a mechanical append.

## Arguments

`$ARGUMENTS` = the slug of the case to merge into the active case.

## Process

### Step 1: Validate

If `$ARGUMENTS` is empty:
```bash
python -m gcbc.cli list
```
Display available cases and usage. Then stop.

```bash
python -m gcbc.cli status
```
If no active case, stop with error.

### Step 2: Load both contexts

```bash
python -m gcbc.cli context
```
(active case context)

```bash
python -m gcbc.cli get-case --slug "$ARGUMENTS"
```
(target case context)

### Step 3: Spawn GC and BC for rewrite

Spawn TWO sub-agents **in parallel** using the Agent tool with `model: "opus"`:

**GC rewrite agent:**
```
You are GOOD COP performing a case merge. Two cases are being combined into one.

Your task: Rewrite these files for the merged case:
1. **case.md** — Write a unified description that captures both cases' scope
2. **verdict.md** — If both cases have verdicts, synthesize them into one

Be thorough but concise. The merged case should read as if it was always one case.

<active_case>
{ACTIVE_CONTEXT}
</active_case>

<merging_case>
{TARGET_CONTEXT}
</merging_case>

Return format:
CASE_MD_DESCRIPTION:
[unified description]

VERDICT_CONTENT:
[merged verdict if both have one, or "N/A" if neither/only one has a verdict]
```

**BC rewrite agent:**
```
You are BAD COP performing a case merge. Two cases are being combined into one.

Your task: Rewrite these files for the merged case:
1. **interrogation.md** — Synthesize key points from both transcripts (not full copy — extract the most important Q&A)
2. **debate.md** — Combine debate insights from both cases
3. **links.md** — Merge link lists, deduplicate

Be thorough but concise. Remove redundancy, keep what matters.

<active_case>
{ACTIVE_CONTEXT}
</active_case>

<merging_case>
{TARGET_CONTEXT}
</merging_case>

Return format:
INTERROGATION_CONTENT:
[synthesized transcript]

DEBATE_CONTENT:
[combined debate insights]

LINKS_CONTENT:
[merged links]
```

### Step 4: Write merged files

Use the agent outputs to rewrite the active case files. Use the Write tool for each file.

**Important:** `interrogation.md` and `debate.md` are stored externally in `~/.gcbc/cases/{slug}/`, not in the project. Use the CLI commands (`append-transcript`, `append-debate`) to write to them.

Update metadata:
```bash
python -m gcbc.cli merge --source-slug "$ARGUMENTS"
```

### Step 5: Display

```
Merge complete: [target-slug] -> [active-slug]

[target-slug] status set to "merged"
[active-slug] now contains synthesized content from both cases.

Files rewritten:
- case.md (unified description)
- interrogation transcript (synthesized key points)
- debate transcript (combined insights)
- links.md (merged)
[- verdict.md (merged) — if applicable]

Review with /case to see the updated dashboard.
```
