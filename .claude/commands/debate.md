# /debate — Trigger GC/BC background debate

Start the structured debate between Good Cop and Bad Cop. They exchange arguments over 3-5 sequential turns, attempting to reach consensus. If consensus is reached, verdict.md is written. If not, another interrogation round is suggested.

## Process

### Step 1: Load active case

Run:
```bash
python -m gcbc.cli status
```
If no active case, stop with error.

Extract `round_count` from the status JSON.

If `round_count` < 3:
```
Not enough interrogation has been done yet. Run a few more rounds with /interrogate before starting the debate.
```
Then stop.

Load full context:
```bash
python -m gcbc.cli context
```

Also read the global `.gcbc/facts.md`.

### Step 2: Run debate turns

The debate runs 5 sequential turns. Each turn is a SINGLE sub-agent call with `model: "opus"`. Turns are NOT parallel — each reads the previous turn's output.

Collect all debate output in a running transcript variable.

**Turn 1 — GC opens:**
```
You are GOOD COP (GC) in a GCBC debate. Turn 1 of 5.

Summarize the strongest case FOR this idea based on everything learned in interrogation and investigation. Be specific — cite evidence, reference what the user said, make the affirmative case.

Structure your argument clearly with headers and bullet points.

<case_context>
{CONTEXT}
</case_context>
```

**Turn 2 — BC counters:**
```
You are BAD COP (BC) in a GCBC debate. Turn 2 of 5.

Good Cop has presented their case. Respond to their specific points. Identify weaknesses, counter with evidence, and present the strongest challenges that remain.

<gc_argument>
{TURN_1_OUTPUT}
</gc_argument>

<case_context>
{CONTEXT}
</case_context>
```

**Turn 3 — GC refines:**
```
You are GOOD COP (GC) in a GCBC debate. Turn 3 of 5.

Bad Cop has countered your position. Address their specific points:
- Concede where they are right
- Maintain what you still believe with evidence
- Focus on the strongest remaining disagreement

You may also emit these optional signals if appropriate:
- SUGGEST_SPLIT: true — if the case covers multiple distinct concerns that should be separate cases. Include proposed child names and rationale.
- SUGGEST_REOPEN: [slug] — if a previously closed case's spec needs revision based on this debate. Include rationale.

If you believe a verdict can now be written that honestly captures the problem, solution, and real risks, add:
CONSENSUS: true

<bc_counter>
{TURN_2_OUTPUT}
</bc_counter>

<debate_so_far>
{TURN_1_OUTPUT}
---
{TURN_2_OUTPUT}
</debate_so_far>

<case_context>
{CONTEXT}
</case_context>
```

**Turn 4 — BC responds:**
```
You are BAD COP (BC) in a GCBC debate. Turn 4 of 5.

Address Good Cop's refined position:
- Concede points that have been adequately addressed
- Maintain remaining concerns with evidence
- State clearly what is still unresolved

You may also emit these optional signals if appropriate:
- SUGGEST_SPLIT: true — if the case covers multiple distinct concerns. Include proposed child names and rationale.
- SUGGEST_REOPEN: [slug] — if a previously closed case needs revision. Include rationale.

If you believe a verdict can now be written (even with open questions), add:
CONSENSUS: true

<gc_refined>
{TURN_3_OUTPUT}
</gc_refined>

<debate_so_far>
{TURNS_1_THROUGH_3}
</debate_so_far>

<case_context>
{CONTEXT}
</case_context>
```

**Turn 5 — Synthesis (both):**

Spawn TWO sub-agents in parallel with `model: "opus"`:

GC synthesis:
```
You are GOOD COP (GC) in a GCBC debate. Turn 5 (final).

Based on the full debate, write your proposed verdict. Output:

CONSENSUS: true (or false if you genuinely cannot agree)

If CONSENSUS: true, write:
VERDICT_CONTENT:
[Full verdict in this structure:]

# Verdict — [case title]

## Problem
[What problem this solves]

## Solution
[The agreed approach]

## Non-Negotiables
[Pull from global facts.md]

## Open Questions
[Unresolved risks and questions to carry forward]

## Links
[Related cases]

## Changelog
- [timestamp] Initial verdict after [N] rounds and [M] debate turns

<debate_transcript>
{ALL_TURNS}
</debate_transcript>

<case_context>
{CONTEXT}
</case_context>
```

BC synthesis (same structure but from BC perspective).

### Step 3: Process signals

**SUGGEST_SPLIT detection:**
If any turn contains `SUGGEST_SPLIT: true`, present to user:
```
GC/BC recommend splitting this case into: [proposed children]
Reason: [rationale]

Accept? Use /split-case [child1, child2, ...] to split, or continue the debate.
```

**SUGGEST_REOPEN detection:**
If any turn contains `SUGGEST_REOPEN:`, present to user:
```
GC/BC recommend reopening case [slug] because: [rationale]

Accept? Use /reopen-case [slug] to reopen.
```

### Step 4: Consensus check

If BOTH Turn 5 agents output `CONSENSUS: true`:
- Take the GC verdict content (or merge both if they differ)
- Write verdict.md:
```bash
python -m gcbc.cli write-verdict --content "[VERDICT_CONTENT]"
```
- Increment debate counter:
```bash
python -m gcbc.cli increment-debate
```
- Display: "Consensus reached! Verdict written to .gcbc/cases/[slug]/verdict.md"
- Show the verdict content

If consensus NOT reached:
- Increment debate counter:
```bash
python -m gcbc.cli increment-debate
```
- Check if the returned `debate_attempts` >= 3. If so:
```
Three debate cycles without consensus. Consider:
- /gc [question] and /bc [question] to explore the core disagreement
- /interrogate to gather more information
- /fact [constraint] to add non-negotiables that narrow the solution space
```
- Otherwise:
```
No consensus reached. The core disagreement: [summarize from debate]
Run /interrogate to gather more information, then try /debate again.
```

### Step 5: Record full debate

Append the entire debate transcript to debate.md:
```bash
python -m gcbc.cli append-debate --content "## Debate — [timestamp]

### Turn 1 — Good Cop Opens
[TURN_1]

### Turn 2 — Bad Cop Counters
[TURN_2]

### Turn 3 — Good Cop Refines
[TURN_3]

### Turn 4 — Bad Cop Responds
[TURN_4]

### Turn 5 — Synthesis
**Good Cop:** [TURN_5_GC]
**Bad Cop:** [TURN_5_BC]

### Outcome: [Consensus reached / No consensus]
"
```
