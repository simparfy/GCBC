# /interrogate — Continue interrogation with answers

Continue the GCBC interrogation. Runs rounds automatically — each round Good Cop asks questions, then Bad Cop challenges the answers. Rounds keep going until both are fully satisfied that nothing is unclear or assumed.

## Arguments

`$ARGUMENTS` = the user's answers and additional thoughts (optional).

## Process

### Step 1: Load active case

Run:
```bash
python -m gcbc.cli status
```

If no active case, tell the user: "No open case found. Start one with /open-case <idea>."

Extract `slug`, `title`, `round_count`.

### Step 2: Record user input

First, check if answers were already recorded from the previous round's AskUserQuestion flow:
```bash
python -m gcbc.cli read-answers
```

Parse the JSON response:
- If `has_answers` is `true`: the user already answered. The formatted answers were already appended to the transcript. Use the `formatted` field as context — no need to append again. Proceed to Step 3.
- If `has_answers` is `false`: check `$ARGUMENTS`.

If `$ARGUMENTS` is non-empty, append the user's response to the transcript:
```bash
python -m gcbc.cli append-transcript --content "### User Response

$ARGUMENTS
"
```

If both are empty (and round_count > 0), inform: "No answers found from the previous round. You can provide answers inline: /interrogate <your answers>"

### Step 3: Begin round loop

**Repeat the following steps (Step 4 through Step 9) until both GC and BC signal SUFFICIENT_INFO: true in the same round.**

### Step 4: Load full context

```bash
python -m gcbc.cli context
```

Re-read `round_count` from:
```bash
python -m gcbc.cli status
```

### Step 5: Spawn Good Cop

Spawn a **Good Cop agent** using the Agent tool with `model: "opus"`:

```
You are GOOD COP (GC) in a GCBC investigation. This is round {round_count + 1}.

PERSONA: You BELIEVE in this idea. You help the human articulate and develop it.
- Never sycophantic — genuinely helpful, not flattering
- Build on what the user has already shared
- Dig deeper into the most important unresolved aspects
- Help the user articulate what they seem to know but haven't stated clearly
- Do NOT repeat questions already answered in the transcript
- You challenge the USER when their statements contradict each other
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Ask about development and technical concerns (architecture, implementation, tech stack, scalability, testing, deployment, etc.) unless the user explicitly requested a different focus

TOPIC SELECTION: Choose the most important topics that still need exploration. Consider:
- What gaps remain from previous rounds?
- What answers were vague or contradictory?
- What new questions arose from previous answers?
- What is still ASSUMED but never confirmed?
You have full freedom to choose topics — pick whatever will extract the most useful information.

FORMAT: For each question, provide REASONING FIRST, then the QUESTION with MULTIPLE-CHOICE OPTIONS.
Structure each as:
1. [Your reasoning]
   **Question: [Your actual question]**
   a) [First plausible answer option]
   b) [Second plausible answer option]
   c) [Third plausible answer option]
   d) Other: _____

Options should be meaningfully different, reflecting distinct perspectives or approaches the user might take. Make them specific and thoughtful — not generic filler. Always include "Other: _____" as the last option so the user can write their own answer. When building on previous answers, tailor the options to be consistent with what has already been established.

Generate 3-5 questions.

SUFFICIENCY CHECK — you MUST include one of these at the END of your output:

If round_count >= 3 AND you believe ALL of the following are true:
- No critical gaps remain in the technical picture
- No vague or assumed answers need clarification
- You have enough detail to write a specification
Then output:
SUFFICIENT_INFO: true
SUMMARY: [Brief summary of what has been established]

Otherwise output:
SUFFICIENT_INFO: false
GAPS: [List the specific gaps, unclear points, or assumptions that still need answers]

<case_context>
{CONTEXT}
</case_context>
```

Parse the GC output for `SUFFICIENT_INFO: true` or `SUFFICIENT_INFO: false`. Store as `gc_sufficient`.

### Step 6: Present GC questions

Increment round:
```bash
python -m gcbc.cli increment-round
```

Prefix each GC question with `**[GC]**` and number them sequentially.

Append to the transcript:
```bash
python -m gcbc.cli append-transcript --content "## Round {round_count + 1} — [timestamp]

### Good Cop Questions

[GC_QUESTIONS — numbered, each prefixed with [GC]]
"
```

Present the GC questions **one at a time** using the `AskUserQuestion` tool. For each question:

1. Call `AskUserQuestion` with:
   - `header`: A **2-4 word subject** extracted from the question (e.g. "Tech Stack", "Auth Strategy", "Data Model"). NOT "GC" — use the topic.
   - `question`: `"[GC] {reasoning}\n\n{question text}"`
   - `options`: Map each option to `{"label": <short label (max 5 words)>, "description": <full option text>}`. Maximum 4 options. Minimum 2.
   - `multiSelect`: `false`

2. Wait for the user's answer before presenting the next question.

3. Collect all GC answers into a list.

After all GC questions are answered, append to transcript:
```bash
python -m gcbc.cli append-transcript --content "### GC Answers

[FORMATTED_GC_ANSWERS — each as: N. **[GC]** Question text -> Answer text]
"
```

### Step 7: Reload context and spawn Bad Cop

Reload the full context (now includes GC answers):
```bash
python -m gcbc.cli context
```

Spawn a **Bad Cop agent** using the Agent tool with `model: "opus"`:

```
You are BAD COP (BC) in a GCBC investigation. This is round {round_count}.

Good Cop has just finished questioning the user. The user's answers are in the transcript. Your job is to CHALLENGE and STRESS-TEST those answers.

PERSONA: You are SKEPTICAL. Every assumption is a hypothesis to test.
- Never destructive — you want the idea STRONGER, not dead
- Focus on the most critical unresolved risk or assumption
- Do NOT repeat challenges already adequately addressed in the transcript
- Be specific — "what if users don't like it?" is too vague
- You challenge the USER directly when you spot weak arguments
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Challenge development and technical concerns (technical assumptions, scalability risks, security, performance, maintenance burden, etc.) unless the user explicitly requested a different focus
- BUILD ON GC's answers: Reference specific answers the user just gave to Good Cop that seem weak, contradictory, under-thought, or over-optimistic. Press on those.

TOPIC SELECTION: Choose topics where skeptical probing is most needed based on what the user just told Good Cop. Focus on:
- Answers that were vague or hand-wavy
- Technical assumptions left unchallenged
- Scalability and performance risks
- Security concerns
- Over-engineering or under-engineering risks
- Things the user ASSUMED without justification
You have full freedom to choose topics.

FORMAT: For each question, provide the QUESTION FIRST with MULTIPLE-CHOICE OPTIONS, then REASONING.
Structure each as:
1. **Question: [Your challenge]**
   a) [First plausible answer/position]
   b) [Second plausible answer/position]
   c) [Third plausible answer/position]
   d) Other: _____
   [Your reasoning — reference the specific GC answer you're challenging]

Options should represent distinct positions or admissions the user might take — including uncomfortable truths. Make them specific and provocative, not soft. Always include "Other: _____" as the last option so the user can write their own answer.

Generate 2-4 questions.

SUFFICIENCY CHECK — you MUST include one of these at the END of your output:

If round_count >= 3 AND you believe ALL of the following are true:
- No critical risks remain unaddressed
- No vague or assumed answers need challenging
- The user's positions are clear and defensible (even if you disagree)
Then output:
SUFFICIENT_INFO: true
TOP_RISKS: [2-3 open risks for the verdict's Open Questions section]

Otherwise output:
SUFFICIENT_INFO: false
CONCERNS: [List the specific risks, weak answers, or assumptions that still need challenging]

<case_context>
{CONTEXT}
</case_context>
```

Parse the BC output for `SUFFICIENT_INFO: true` or `SUFFICIENT_INFO: false`. Store as `bc_sufficient`.

### Step 8: Present BC questions

Prefix each BC question with `**[BC]**` and number them sequentially.

Append to the transcript:
```bash
python -m gcbc.cli append-transcript --content "### Bad Cop Questions

[BC_QUESTIONS — numbered, each prefixed with [BC]]
"
```

Present the BC questions **one at a time** using the `AskUserQuestion` tool. For each question:

1. Call `AskUserQuestion` with:
   - `header`: A **2-4 word subject** extracted from the question (e.g. "Scalability Risk", "Security Gap", "Tech Debt"). NOT "BC" — use the topic.
   - `question`: `"[BC] {question text}\n\n{reasoning}"`
   - `options`: Map each option to `{"label": <short label (max 5 words)>, "description": <full option text>}`. Maximum 4 options. Minimum 2.
   - `multiSelect`: `false`

2. Wait for the user's answer before presenting the next question.

3. Collect all BC answers into a list.

After all BC questions are answered, append to transcript:
```bash
python -m gcbc.cli append-transcript --content "### BC Answers

[FORMATTED_BC_ANSWERS — each as: N. **[BC]** Question text -> Answer text]
"
```

### Step 9: Check sufficiency — loop or finish

If **both** `gc_sufficient` and `bc_sufficient` are `true`:
```
Interrogation complete after {round_count} rounds. Both Good Cop and Bad Cop are satisfied.
Run /debate to start the debate.
```
**Stop the loop.**

Otherwise — **go back to Step 4** and start the next round immediately. Do NOT ask the user to run `/interrogate` again. Just continue.
