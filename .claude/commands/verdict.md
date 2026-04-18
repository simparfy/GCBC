# /verdict — Generate GO / NO-GO / CONDITIONAL recommendation

Generate a final verdict with a clear go/no-go recommendation based on all gathered evidence and debate outcomes.

## Process

### Step 1: Load active case

```bash
python -m gcbc.cli status
```
If no active case, stop with error.

Check if `cases/{slug}/verdict.md` exists. If NOT:
```
No verdict has been written yet. Run /debate first to have GC and BC reach consensus.
```
Then stop.

```bash
python -m gcbc.cli context
```

Also read the global `facts.md` from the project root.

### Step 2: Generate verdict

Spawn TWO sub-agents **in parallel** using the Agent tool with `model: "opus"`:

**GC verdict agent:**
```
You are GOOD COP writing your final verdict for this case.

Review all evidence, the debate transcript, the existing verdict, and all facts.
Write your recommendation:

RECOMMENDATION: [GO / NO-GO / CONDITIONAL]
CONFIDENCE: [HIGH / MEDIUM / LOW]
KEY_CONDITIONS: [If CONDITIONAL, what must be true for GO]
TOP_STRENGTHS: [3 bullet points]
RECOMMENDED_NEXT_STEPS: [What to do if GO]

<case_context>
{CONTEXT}
</case_context>
```

**BC verdict agent:**
```
You are BAD COP writing your final verdict for this case.

Review all evidence, the debate transcript, the existing verdict, and all facts.
Write your recommendation:

RECOMMENDATION: [GO / NO-GO / CONDITIONAL]
CONFIDENCE: [HIGH / MEDIUM / LOW]
KEY_CONDITIONS: [If CONDITIONAL, what must be true for GO]
TOP_RISKS: [3 bullet points]
RECOMMENDED_MITIGATIONS: [What to do to reduce risk]

<case_context>
{CONTEXT}
</case_context>
```

### Step 3: Synthesize

Compare both verdicts:

- If both say GO: **GO** (high confidence)
- If both say NO-GO: **NO-GO** (high confidence)
- If they disagree: **CONDITIONAL** — list conditions from both
- If either says CONDITIONAL: **CONDITIONAL** — merge conditions

Write the synthesized verdict to the existing verdict.md as an appended section:

```
## Verdict

**Recommendation: [GO / NO-GO / CONDITIONAL]**
**Confidence: [HIGH / MEDIUM / LOW]**

### Conditions (if CONDITIONAL)
[merged conditions]

### Strengths (from Good Cop)
[GC strengths]

### Risks (from Bad Cop)
[BC risks]

### Next Steps
[merged recommendations]
```

Update verdict.md:
```bash
python -m gcbc.cli write-verdict --content "[updated content]"
```

### Step 4: Display

```
VERDICT — Case: [slug]

Recommendation: [GO / NO-GO / CONDITIONAL]
Confidence: [HIGH / MEDIUM / LOW]

[Show key conditions if CONDITIONAL]
[Show top strengths]
[Show top risks]
[Show next steps]

Full verdict written to cases/[slug]/verdict.md
```
