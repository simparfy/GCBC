# GCBC (Good Cop Bad Cop) — Implementation Plan

## Context

Building a structured AI-powered idea investigation framework as Claude Code custom skills. When a user has an idea, they "open a case" and two AI personas — Good Cop (supportive) and Bad Cop (skeptical) — interrogate them through multiple rounds, gather evidence, debate each other, and produce a final spec with a go/no-go verdict.

The core insight: GC and BC have **asymmetric communication styles**. GC builds context first then asks (supportive), BC questions first then explains why (confrontational). Both challenge the USER directly — not just the idea abstractly.

---

## Decisions Summary

| Decision | Choice |
|---|---|
| Tech stack | Python (Typer CLI) + Claude Code skills |
| Delivery | `.claude/commands/*.md` slash commands |
| AI provider | Provider-agnostic, Anthropic first |
| Model routing | **Opus**: interrogation, debate, investigation, verdict. **Sonnet**: file writing, formatting, case management |
| Storage | Markdown files in `/cases/{slug}/` |
| GC/BC execution | Parallel sub-agent calls |
| Round structure | Alternating rounds, 5+ deep questions with reasoning |
| GC format | Reasoning first, then question |
| BC format | Question first, then reasoning |
| Debate trigger | Min 3 rounds, agents suggest readiness, user confirms before debate starts |
| Debate style | Multi-turn AI debate (3-5 turns), visible transcript |
| Case IDs | Slug from title |
| Multi-case | One active at a time |
| Codebase | Always codebase-aware |
| Conclusion | Living document with changelog |
| Team | Parallel use, no author tracking, timestamps only |
| Branding | Professional/neutral (no detective theme) |
| Verdict | Separate `/verdict` command |
| Case hierarchy | Parent-child via split, intelligent merge rewrites files |
| Agent autonomy | GC/BC can suggest split/reopen during debate |

---

## Commands

| Command | Description |
|---|---|
| `/open-case <idea>` | Create case, run first interrogation round |
| `/interrogate [answers]` | Continue interrogation, record answers, get next questions |
| `/gc <message>` | Talk directly to Good Cop |
| `/bc <message>` | Talk directly to Bad Cop |
| `/investigate [focus]` | GC and BC independently search web + codebase for evidence |
| `/fact <statement>` | Add non-negotiable to facts.md |
| `/case` | Show case dashboard (status, rounds, facts, links) |
| `/debate` | Trigger GC/BC background debate to reach consensus and write verdict |
| `/verdict` | Generate GO / NO-GO / CONDITIONAL recommendation |
| `/close-case` | Archive current case |
| `/reopen-case <slug>` | Reopen archived case |
| `/link-case <slug> [note]` | Link current case to another |
| `/split-case <child1> <child2> [...]` | Split active case into child cases (parent gets status: split) |
| `/merge-case <slug>` | Intelligently merge target case into active case — GC/BC rewrite all files |

---

## Project Structure

```
GCBC/
├── .claude/
│   └── commands/
│       ├── open-case.md
│       ├── close-case.md
│       ├── reopen-case.md
│       ├── link-case.md
│       ├── investigate.md
│       ├── interrogate.md
│       ├── gc.md
│       ├── bc.md
│       ├── fact.md
│       ├── case.md              # /case status dashboard
│       ├── verdict.md
│       ├── debate.md
│       ├── split-case.md
│       └── merge-case.md
├── src/
│   └── gcbc/
│       ├── __init__.py
│       ├── case.py              # Case CRUD, slug, state machine
│       ├── templates.py         # Markdown file templates
│       └── cli.py               # Typer CLI (JSON output)
├── cases/                       # Auto-created, one subdir per case
│   └── {slug}/
│       ├── case.md
│       ├── interrogation.md
│       ├── links.md
│       ├── debate.md
│       └── verdict.md           # Written at consensus
├── facts.md                     # GLOBAL — shared across all cases
├── pyproject.toml
├── CLAUDE.md
├── .gitignore
├── plan.md
├── LICENSE
└── README.md
```

---

## Phase 1: Python Foundation

### 1.1 `pyproject.toml`
- Package: `gcbc`, version `0.1.0`
- Dependencies: `typer>=0.12`, `python-slugify>=8.0`, `rich>=13.0`
- Entry point: `gcbc = "gcbc.cli:app"`
- Build: hatchling, packages from `src/gcbc`

### 1.2 `src/gcbc/templates.py`
Markdown templates for 5 per-case files + 1 global file. Uses `{slug}`, `{title}`, `{description}`, `{timestamp}` placeholders.

**Per-case files (in `cases/{slug}/`):**
- **case.md**: YAML frontmatter (`status`, `title`, `slug`, `created`, `updated`, `round_count`, `debate_attempts`, `parent`, `children`, `merged_from`) + description body. Status values: `open`, `closed`, `split`, `merged`
- **interrogation.md**: Header + separator, ready for round entries
- **links.md**: Header for case links
- **debate.md**: Header for GC/BC debate transcript
- **verdict.md** (template only, written at consensus): Problem, Solution, Non-Negotiables (pulled from global facts.md), Open Questions, Links, Changelog sections

**Global file (project root):**
- **facts.md**: Shared non-negotiables across ALL cases. When writing any verdict.md, relevant facts are pulled from this global file. Created on first `/fact` call if it doesn't exist.

### 1.3 `src/gcbc/case.py` — Core Logic

Key functions:

```
slugify_title(title) -> str              # python-slugify, truncate 50 chars
find_active_case(cases_dir) -> Path|None # scan case.md frontmatter for status=open
list_all_cases(cases_dir) -> list[dict]  # all cases with meta
create_case(cases_dir, title, desc) -> (slug, path)  # handle slug collisions (-2, -3)
close_case(case_path)                    # set status=closed
reopen_case(cases_dir, slug) -> Path     # validate closed, set open
increment_round(case_path) -> int        # bump round_count
append_to_transcript(case_path, content) # append to interrogation.md
append_to_debate(case_path, content)     # append to debate.md
append_fact(project_root, statement)     # dedupe check, append to GLOBAL facts.md
append_link(case_path, target_slug, note)# bidirectional: writes to BOTH cases' links.md
write_verdict(case_path, content)        # create/update verdict.md, append changelog
read_full_case_context(case_path) -> str # all files combined in tagged blocks
```

Error classes: `CaseError`, `CaseNotFoundError`, `CaseAlreadyOpenError`, `NoCaseOpenError`

### 1.4 `src/gcbc/cli.py` — Typer CLI

All commands output JSON to stdout, errors to stderr. Commands:

```
gcbc open --title "..." [--description "..."]
gcbc close
gcbc reopen --slug "..."
gcbc status                    # active case meta or {"active": false}
gcbc list                      # all cases
gcbc increment-round
gcbc append-transcript --content "..."
gcbc append-debate --content "..."
gcbc add-fact --statement "..."        # writes to global facts.md
gcbc add-link --target-slug "..." [--note "..."]
gcbc write-verdict --content "..."     # writes/updates verdict.md
gcbc context                   # full case context dump
gcbc slug --title "..."        # preview slug generation
gcbc split --children "child1,child2,..."  # split active case into children
gcbc merge --source-slug "..."             # merge source into active case
gcbc get-case --slug "..."                 # read specific case context (for merge)
```

Environment: `GCBC_CASES_DIR` (defaults to `./cases/`)

### 1.5 `.gitignore`
- `cases/` (optional — can be committed per preference)
- `__pycache__/`, `*.egg-info/`, `.venv/`

---

## Phase 2: Skill Files

### 2.1 `/open-case` (`.claude/commands/open-case.md`)

Flow:
1. Validate `$ARGUMENTS` non-empty
2. Check no active case exists (`gcbc status`)
3. Create case (`gcbc open --title "$ARGUMENTS"`)
4. Load context (`gcbc context`)
5. **Spawn GC and BC sub-agents in parallel** — each generates 5+ opening questions
6. Increment round, append to transcript
7. Display both question sets to user

GC prompt: Generate opening questions using **reasoning-first, then question** format. Focus on motivation, problem understanding, expected outcomes.

BC prompt: Generate opening challenges using **question-first, then reasoning** format. Focus on critical assumptions, risks, existing alternatives.

Both are codebase-aware — if code exists, they can reference it.

### 2.2 `/interrogate` (`.claude/commands/interrogate.md`)

Flow:
1. Load active case
2. Record user's `$ARGUMENTS` as their response to previous round
3. Load full context
4. Spawn GC and BC in parallel — each generates next questions based on full transcript
5. **Sufficiency detection**: After round 3+, agents can signal `SUFFICIENT_INFO: true`
   - Both sufficient → **suggest** debate to user: "GC and BC believe enough info has been gathered. Start the debate? Use /interrogate to continue, or /debate to begin."
   - One sufficient → note which agent wants more, continue with questions from both
   - Neither → normal round
   - Interrogation continues indefinitely until the user explicitly triggers `/debate`
6. Increment round, update transcript, display

### 2.3 `/investigate` (`.claude/commands/investigate.md`)

Flow:
1. Load active case
2. Spawn GC and BC in parallel with WebSearch + codebase read access
   - GC: searches for **supporting** evidence (problem validation, similar successes, feasibility)
   - BC: searches for **contradicting** evidence (failure patterns, existing alternatives, risks)
3. Append findings to debate.md
4. Display both investigation reports

### 2.4 `/gc` (`.claude/commands/gc.md`)

Direct conversation with Good Cop persona. Uses **reasoning-first** style. Appends exchange to interrogation.md as "Direct GC Conversation".

### 2.5 `/bc` (`.claude/commands/bc.md`)

Direct conversation with Bad Cop persona. Uses **question-first** style. Appends exchange to interrogation.md as "Direct BC Conversation".

### 2.6 `/fact` (`.claude/commands/fact.md`)

1. Validate active case + non-empty argument
2. Call `gcbc add-fact`
3. Handle duplicates gracefully
4. Confirm recording

### 2.7 `/case` (`.claude/commands/case.md`)

Dashboard display:
```
GCBC Case: [add-dark-mode]
Status: Open | Round: 4 | Debate Attempts: 0
Facts: 3 non-negotiables
Links: 1 linked case
Verdict: Not yet written

Recent activity:
  Round 4 — 2026-04-16 19:45
  Investigation — 2026-04-16 19:30
```

### 2.8 `/verdict` (`.claude/commands/verdict.md`)

Flow:
1. Load active case, verify verdict.md exists
2. Spawn BOTH GC and BC in parallel — each writes their verdict independently
3. Synthesize into final verdict: **GO** / **NO-GO** / **CONDITIONAL**
4. Include: confidence level, key conditions, top risks, recommended next steps
5. Append verdict to verdict.md (with changelog entry)

### 2.9 `/close-case` (`.claude/commands/close-case.md`)

1. Warn if no verdict.md exists — offer to continue or close anyway
2. Set status=closed via `gcbc close`
3. Display archive confirmation

### 2.10 `/reopen-case` (`.claude/commands/reopen-case.md`)

1. If no argument, list all closed cases
2. Check no other case is active
3. Reopen via `gcbc reopen`

### 2.11 `/link-case` (`.claude/commands/link-case.md`)

1. Parse slug + optional note from arguments
2. Validate target case exists
3. Append link to **both** cases via `gcbc add-link` (bidirectional)
   - Active case's links.md: link to target
   - Target case's links.md: link back to active case
4. During `/investigate`, agents decide how deeply to explore linked cases based on relevance — they may read linked case context, pull evidence from linked conclusions, or ignore tangential links

### 2.12 `/split-case` (`.claude/commands/split-case.md`)

Split the active case into multiple child cases. Can be triggered by user OR suggested by GC/BC during debate.

Flow:
1. Load active case
2. Parse `$ARGUMENTS` for child case names (comma or space separated)
3. If no arguments, spawn GC and BC in parallel to **suggest a split** — each proposes how they'd divide the case and what each child should cover
4. If arguments provided:
   a. Create child cases: `cases/{parent-slug}--{child-name}/` for each child
   b. Children share global facts.md (no copy needed — facts are global)
   c. Each child gets a link back to parent in links.md
   d. Parent's status set to `split`, `children` field populated in frontmatter
   e. Spawn GC and BC to **distribute the interrogation content** — they rewrite each child's case.md description to scope it properly
5. Display new case structure

Child naming: `{parent-slug}--{child-slug}` (double dash separator)

### 2.13 `/merge-case` (`.claude/commands/merge-case.md`)

Intelligently merge a target case into the active case. GC and BC **rewrite all files** — this is not a mechanical append.

Flow:
1. Load active case context (`gcbc context`)
2. Load target case context (`gcbc get-case --slug "$ARGUMENTS"`)
3. Spawn GC and BC in parallel — each produces a **merged rewrite**:
   - GC rewrites: case.md (unified description), verdict.md (if both have one)
   - BC rewrites: interrogation.md (synthesized key points, not full transcript copy), debate.md (combined insights), links.md (merged)
4. Compare GC and BC rewrites — if they agree on structure, use the merged version. If they differ significantly, show both and let user choose (or run a quick debate).
5. Write merged files to active case
6. Set target case status to `merged`, add `merged_into: {active-slug}` to its frontmatter
7. Active case gets `merged_from: [{target-slug}]` in frontmatter
8. Display summary of what changed

---

## Phase 3: Debate Orchestration

Triggered by user via `/debate` command (not auto-triggered).

### Debate Protocol

**Turn structure** (sequential, not parallel — each reads the previous):

| Turn | Agent | Task |
|---|---|---|
| 1 | GC | Open: summarize the case FOR the idea with evidence |
| 2 | BC | Counter: respond to GC's summary with weaknesses |
| 3 | GC | Refine: address BC's points, concede or maintain |
| 4 | BC | Respond: concede addressed points, maintain remaining |
| 5 | Both | Synthesis attempt — each outputs CONSENSUS: true/false |

### Consensus Detection
- Turns 3-5: check for `CONSENSUS: true` + `CONCLUSION:` block
- Both agree → write verdict.md with structured spec
- No consensus after 5 turns → trigger another interrogation round
- Track `debate_attempts` in case.md frontmatter
- After 3 failed debates, suggest user manually resolve via `/gc` and `/bc`

### Agent Autonomy: Split and Reopen Suggestions

During debate turns 3-5, GC and BC can emit additional signals:

**`SUGGEST_SPLIT: true`** + rationale + proposed children
- Triggered when the case covers multiple distinct concerns that would benefit from separate investigation
- The orchestrator presents the suggestion to the user: "GC/BC recommend splitting this case into: [child1], [child2]. Reason: [rationale]"
- User can accept (triggers `/split-case` flow) or reject and continue debate

**`SUGGEST_REOPEN: <slug>`** + rationale
- Triggered when the debate reveals that a previously closed case's spec needs revision
- The orchestrator presents: "GC/BC recommend reopening case [{slug}] because: [rationale]"
- User can accept (triggers `/reopen-case`) or reject

These signals are checked **alongside** the consensus signal — a turn can contain both `CONSENSUS: true` and `SUGGEST_REOPEN`. GC and BC are the owners of the specs; they proactively manage the case landscape.

### Verdict Changelog
When verdict.md is updated (by further interrogation or new debate), append:
```
## Changelog
- [2026-04-16 19:45] Initial verdict written after 4 rounds, 1 debate
- [2026-04-16 20:10] Updated after Round 6 — revised solution approach
```

---

## Phase 4: CLAUDE.md and Polish

### `CLAUDE.md`
```
# GCBC — Good Cop Bad Cop Framework
- Cases in /cases/{slug}/, managed by Python CLI
- CLI: python -m gcbc.cli <command> (outputs JSON)
- Install: pip install -e . from repo root
- Never write case files directly — always use the CLI
- One active case at a time
```

### `README.md`
- Project description, install instructions, command reference
- Example workflow walkthrough

---

## Implementation Order

1. **Python foundation**: `pyproject.toml`, `templates.py`, `case.py`, `cli.py`, `.gitignore`
2. **Core skills**: `open-case.md`, `interrogate.md`, `gc.md`, `bc.md`
3. **Supporting skills**: `fact.md`, `case.md` (dashboard), `investigate.md`
4. **Debate engine**: `debate.md` skill (including agent split/reopen signals)
5. **Lifecycle skills**: `close-case.md`, `reopen-case.md`, `link-case.md`
6. **Case hierarchy**: `split-case.md`, `merge-case.md` + CLI commands for split/merge
7. **Verdict**: `verdict.md`
8. **Polish**: `CLAUDE.md`, `README.md`, test full flow

---

## Verification

1. `pip install -e .` succeeds
2. `gcbc open --title "Test idea"` creates `cases/test-idea/` with all 5 per-case files
3. `/open-case Test idea` in Claude Code → creates case + shows Round 1 questions from both GC and BC
4. `/interrogate [answers]` → records answers, generates Round 2 questions
5. `/gc Why do you support this?` → GC responds in character with reasoning-first format
6. `/bc What's wrong with this?` → BC responds in character with question-first format
7. `/fact Must support offline` → appended to facts.md
8. `/investigate` → both agents search and return evidence
9. After 3+ rounds with SUFFICIENT_INFO → agents suggest debate, user confirms
10. `/debate` → debate runs 3-5 turns → verdict.md written
11. During debate, agents can suggest SPLIT or REOPEN — signals are detected and presented to user
12. `/verdict` → GO/NO-GO/CONDITIONAL generated
13. `/case` → shows full dashboard
14. `/close-case` → archives
15. `/reopen-case test-idea` → restores
16. `/link-case other-case` → recorded in links.md (bidirectional)
17. `/split-case frontend backend` → parent gets status:split, two children created (global facts.md shared)
18. `/merge-case other-case` → GC/BC rewrite all files to synthesize both cases into one
