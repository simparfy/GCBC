# /case — Show case dashboard

Display the current case status and a summary dashboard.

## Process

### Step 1: Load status

Run:
```bash
python -m gcbc.cli status
```

If no active case:
```bash
python -m gcbc.cli list
```

If no cases at all:
```
No cases found. Start one with /open-case <idea>.
```
Then stop.

If cases exist but none active, display the list:
```
No active case. Existing cases:

| Slug | Title | Status |
|------|-------|--------|
[table rows from list]

Reopen one with /reopen-case <slug>, or start new with /open-case <idea>.
```
Then stop.

### Step 2: Build dashboard

Read the active case files to count facts and links.

Read `.gcbc/facts.md` and count entries (lines starting with `- `).
Read `.gcbc/cases/{slug}/links.md` and count links (lines starting with `- [`).
Check if `.gcbc/cases/{slug}/verdict.md` exists.

Display:
```
GCBC Case: [slug]
Title: [title]
Status: [status]
Rounds: [round_count]
Facts: [N] non-negotiables (global)
Links: [N] linked cases
Verdict: [Written / Not yet written]
Parent: [parent slug or none]
Children: [child slugs or none]

Commands:
  /interrogate [answers]  — continue interrogation
  /gc [message]           — talk to Good Cop
  /bc [message]           — talk to Bad Cop
  /investigate [focus]    — gather evidence
  /fact [statement]       — add non-negotiable
  /debate                 — start GC/BC debate
  /verdict                — generate go/no-go
  /close-case             — archive this case
```
