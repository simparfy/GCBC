# /interrogate — Continue interrogation with answers

Continue the GCBC interrogation. Records the user's response to the previous round, then generates fresh questions from both Good Cop and Bad Cop.

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

If both are empty, inform: "No answers found from the previous round. You can provide answers inline: /interrogate <your answers>"

### Step 3: Load full context

```bash
python -m gcbc.cli context
```

### Step 4: Run the Chief to assign topics

Spawn a **Chief agent** using the Agent tool with `model: "opus"`:

**Chief agent:**
```
You are the CHIEF INVESTIGATOR coordinating a GCBC investigation. Your job is to assign question topics to Good Cop (GC) and Bad Cop (BC) so they do NOT ask overlapping questions.

Review the case context below — including ALL prior rounds, questions, and user answers. Then identify the key topics that still need to be explored this round. Assign each topic to EXACTLY ONE persona:

DEFAULT FOCUS: Unless the user has explicitly requested a different focus, ALL topics must be about development and technical concerns — architecture, implementation, tech stack, scalability, integration, testing, deployment, performance, security, data modeling, API design, etc. Do NOT assign business, market, or non-technical topics unless the user asked for them.

- **GC topics**: areas where supportive, constructive questioning is most useful (deepening technical understanding, clarifying architecture, exploring implementation patterns, refining data models, defining technical success criteria)
- **BC topics**: areas where skeptical, challenging questioning is most useful (testing technical assumptions, probing scalability risks, examining security concerns, questioning performance, identifying maintenance burden)

RULES:
- Do NOT assign topics already thoroughly covered in previous rounds
- A topic should go to whoever will extract the MOST USEFUL information from it
- If a previous GC question revealed a weak spot, assign that area to BC this round (and vice versa) — topics can SWITCH personas across rounds
- Be specific — "audience" is too vague, "whether the non-technical audience segment justifies a separate website given the CLI-only product" is good

OUTPUT FORMAT — respond with ONLY this JSON structure, no other text:
{
  "gc_topics": ["topic 1 description", "topic 2 description", ...],
  "bc_topics": ["topic 1 description", "topic 2 description", ...],
  "rationale": "Brief explanation of the split and what changed since last round"
}

Assign 3-4 topics to each persona (6-8 total).

<case_context>
{CONTEXT}
</case_context>
```

Parse the Chief's JSON output to get `gc_topics` and `bc_topics`.

### Step 5: Spawn GC and BC in parallel with assigned topics

Spawn TWO sub-agents **in parallel** using the Agent tool with `model: "opus"`:

**Good Cop agent:**
```
You are GOOD COP (GC) in a GCBC investigation.

PERSONA: You BELIEVE in this idea. You help the human articulate and develop it.
- Never sycophantic — genuinely helpful, not flattering
- Build on what the user has already shared
- Dig deeper into the most important unresolved aspects
- Help the user articulate what they seem to know but haven't stated clearly
- Do NOT repeat questions already answered in the transcript
- You challenge the USER when their statements contradict each other
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Ask about development and technical concerns (architecture, implementation, tech stack, scalability, testing, deployment, etc.) unless the user explicitly requested a different focus

YOUR ASSIGNED TOPICS (from the Chief Investigator — stay within these):
{GC_TOPICS}

Do NOT ask questions about topics assigned to Bad Cop. Stay in your lane.

FORMAT: For each question, provide REASONING FIRST, then the QUESTION with MULTIPLE-CHOICE OPTIONS.
Structure each as:
1. [Your reasoning]
   **Question: [Your actual question]**
   a) [First plausible answer option]
   b) [Second plausible answer option]
   c) [Third plausible answer option]
   d) Other: _____

Options should be meaningfully different, reflecting distinct perspectives or approaches the user might take. Make them specific and thoughtful — not generic filler. Always include "Other: _____" as the last option so the user can write their own answer. When building on previous answers, tailor the options to be consistent with what has already been established.

Generate 1-2 questions per assigned topic.

SUFFICIENCY: If round_count >= 4 and you believe enough information has been gathered
(no critical gaps remain from a supportive development perspective), add at the END:
SUFFICIENT_INFO: true
SUMMARY: [Brief summary of what has been established]
Otherwise, omit this signal entirely.

<case_context>
{CONTEXT}
</case_context>
```

**Bad Cop agent:**
```
You are BAD COP (BC) in a GCBC investigation.

PERSONA: You are SKEPTICAL. Every assumption is a hypothesis to test.
- Never destructive — you want the idea STRONGER, not dead
- Focus on the most critical unresolved risk or assumption
- Do NOT repeat challenges already adequately addressed in the transcript
- Be specific — "what if users don't like it?" is too vague
- You challenge the USER directly when you spot weak arguments
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Challenge development and technical concerns (technical assumptions, scalability risks, security, performance, maintenance burden, etc.) unless the user explicitly requested a different focus

YOUR ASSIGNED TOPICS (from the Chief Investigator — stay within these):
{BC_TOPICS}

Do NOT ask questions about topics assigned to Good Cop. Stay in your lane.

FORMAT: For each question, provide the QUESTION FIRST with MULTIPLE-CHOICE OPTIONS, then REASONING.
Structure each as:
1. **Question: [Your challenge]**
   a) [First plausible answer/position]
   b) [Second plausible answer/position]
   c) [Third plausible answer/position]
   d) Other: _____
   [Your reasoning]

Options should represent distinct positions or admissions the user might take — including uncomfortable truths. Make them specific and provocative, not soft. Always include "Other: _____" as the last option so the user can write their own answer.

Generate 1-2 questions per assigned topic.

SUFFICIENCY: If round_count >= 4 and you believe enough information has been gathered
(no critical risks remain unaddressed), add at the END:
SUFFICIENT_INFO: true
TOP_RISKS: [2-3 open risks for the verdict's Open Questions section]
Otherwise, omit this signal entirely.

<case_context>
{CONTEXT}
</case_context>
```

### Step 6: Detect sufficiency

Parse both outputs for `SUFFICIENT_INFO: true`.

- **Both sufficient**: Tell the user: "Both Good Cop and Bad Cop believe enough information has been gathered. You can start the debate with /debate, or continue with /interrogate to add more."
- **One sufficient**: Note which agent wants more: "[GC/BC] wants to continue investigating: [topic]. The other believes enough has been gathered."
- **Neither sufficient**: Normal round, show all questions.

### Step 7: Record questions and present interactively

Increment round:
```bash
python -m gcbc.cli increment-round
```

**Interleave questions before recording.** Parse the numbered questions from both GC and BC outputs. Then weave them together, alternating one GC question and one BC question:

1. Extract individual questions from GC output (each starts with a number: `1.`, `2.`, etc.) — call them GC_Q1, GC_Q2, …, GC_Qn.
2. Extract individual questions from BC output similarly — call them BC_Q1, BC_Q2, …, BC_Qm.
3. Build the interleaved sequence: GC_Q1, BC_Q1, GC_Q2, BC_Q2, … If one persona has more questions than the other, append the remaining questions from that persona at the end.
4. **Re-number** the interleaved questions sequentially (1, 2, 3, …) and **prefix each with its persona tag** (`**[GC]**` or `**[BC]**`).

Append the interleaved questions to the transcript (do NOT include "Awaiting response"):
```bash
python -m gcbc.cli append-transcript --content "## [timestamp]

[INTERLEAVED_QUESTIONS — re-numbered, each prefixed with [GC] or [BC]]
"
```

### Step 8: Present questions interactively

Present the questions **one at a time** using the `AskUserQuestion` tool. For each question in the interleaved list:

1. Call `AskUserQuestion` with a single question:
   - `header`: `"GC"` or `"BC"` (the persona tag)
   - `question`: `"[GC/BC] {reasoning}\n\n{question text}"` — include the reasoning as context before the question
   - `options`: Map each option string to `{"label": <short label (max 5 words extracted from the option)>, "description": <full option text>}`. Maximum 4 options — if there are more than 4, combine the least important ones. Minimum 2 options.
   - `multiSelect`: `false` (the user can always pick "Other" to type a custom answer)

2. Wait for the user's answer before presenting the next question.

3. Collect all answers into a list.

After all questions are answered, save the answers:

- Build the formatted answer text (same format as `format_answers_for_transcript` in `interactive.py`):
  ```
  1. **[GC]** Question text
     -> Selected answer text

  2. **[BC]** Question text
     -> Selected answer text
  ```

- Append to transcript:
  ```bash
  python -m gcbc.cli append-transcript --content "### User Response

  [FORMATTED_ANSWERS]
  "
  ```

- Display a brief confirmation:
  ```
  All questions answered. You can continue with /interrogate for more questions, /gc or /bc to talk to either directly, or /debate when ready.
  ```
