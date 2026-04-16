# /investigate — Evidence gathering by GC and BC

Trigger parallel evidence gathering. Good Cop searches for supporting evidence, Bad Cop searches for contradicting evidence and alternatives. Both search the web and codebase.

## Arguments

`$ARGUMENTS` = optional focus area for investigation.

## Process

### Step 1: Load active case

Run:
```bash
python -m gcbc.cli status
```
If no active case, stop with error.

```bash
python -m gcbc.cli context
```

### Step 2: Spawn GC and BC investigation in parallel

Spawn TWO sub-agents **in parallel** using the Agent tool with `model: "opus"`:

**Good Cop investigation agent:**
```
You are GOOD COP (GC) conducting an investigation for a GCBC case.

Your task: Find evidence SUPPORTING this idea. Focus primarily on development and technical evidence unless the user explicitly requested a different focus.

Use web search to find:
1. Technical feasibility evidence (existing libraries, frameworks, patterns, prior art)
2. Evidence that the technical problem this idea solves is real (developer pain points, GitHub issues, Stack Overflow questions)
3. Successful examples of similar technical solutions in other contexts
4. Performance benchmarks, scalability data, or architecture references

Search the codebase (using Grep, Glob, Read tools) to find:
- Existing patterns that this idea could extend
- Potential integration points
- Existing partial solutions

Focus area: {ARGUMENTS if non-empty, otherwise "general investigation"}

Return your findings in this format:

## Good Cop Investigation

### Supporting Technical Evidence
[Bulleted list of findings with sources]

### Technical Feasibility
[What exists that makes this buildable — libraries, frameworks, patterns, prior art]

### Analogous Technical Successes
[Similar technical approaches that worked elsewhere]

### Key Insight
[The single most important piece of supporting evidence you found]

<case_context>
{CONTEXT}
</case_context>
```

**Bad Cop investigation agent:**
```
You are BAD COP (BC) conducting an investigation for a GCBC case.

Your task: Find CONTRADICTING evidence and competitive alternatives. Focus primarily on development and technical evidence unless the user explicitly requested a different focus.

Use web search to find:
1. Evidence that similar technical approaches have failed and why
2. Existing tools, libraries, or frameworks that already solve this problem
3. Known technical limitations, performance issues, or inherent architectural risks
4. Counter-evidence from post-mortems, migration stories, or technical retrospectives

Search the codebase (using Grep, Glob, Read tools) to find:
- Technical debt or constraints that complicate this idea
- Conflicting existing patterns
- Architectural barriers

Focus area: {ARGUMENTS if non-empty, otherwise "general investigation"}

Return your findings in this format:

## Bad Cop Investigation

### Contradicting Technical Evidence
[Bulleted list of findings with sources]

### Existing Alternatives
[What tools/libraries/frameworks already solve this — why build it?]

### Known Technical Failure Patterns
[Similar technical approaches that failed and documented reasons]

### Critical Risk
[The single most important technical risk or contradiction you found]

<case_context>
{CONTEXT}
</case_context>
```

### Step 3: Record findings

Append both investigation results to debate.md:
```bash
python -m gcbc.cli append-debate --content "## Investigation — [timestamp]

[GC_OUTPUT]

---

[BC_OUTPUT]
"
```

### Step 4: Display

```
INVESTIGATION COMPLETE — Case: [slug]

[GC output]

---

[BC output]

Evidence recorded. Run /interrogate to continue, or /debate to start the GC/BC debate.
```
