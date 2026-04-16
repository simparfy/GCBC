# /open-case — Open a new GCBC investigation case

Open a new case in the GCBC system. Creates the case directory and all tracking files, then immediately runs the first interrogation round with both Good Cop and Bad Cop.

## Arguments

`$ARGUMENTS` = the high-level idea description.

## Process

### Step 1: Validate

If `$ARGUMENTS` is empty, tell the user:
```
Usage: /open-case <your idea here>
Example: /open-case Add dark mode support to the app
```
Then stop.

### Step 2: Check for existing open case

Run:
```bash
python -m gcbc.cli status
```

Parse the JSON. If `active` is `true`, tell the user:
```
There is already an open case: [slug] title
Close it first with /close-case, or link it with /link-case.
```
Then stop.

### Step 3: Check for related existing cases

Run:
```bash
python -m gcbc.cli list
```

If there are existing cases (count > 0), read each case's context briefly (read their case.md files) and assess whether the new idea overlaps with any existing case.

If a related case is found, tell the user:
```
Related existing case found: [slug] — [title] (status: [status])

Options:
1. Open as new case anyway (proceed with /open-case)
2. Merge into existing: /reopen-case [slug] then continue with /interrogate
3. Link them: open new case and /link-case [slug]

What would you like to do?
```
Then stop and wait for user direction. Only proceed to Step 4 if the user confirms they want a new case, or if no related cases exist.

### Step 4: Generate a short title

Before creating the case, summarize `$ARGUMENTS` into a **short title of 2-5 words** that captures the core idea. This title becomes the folder name (slug), so keep it punchy and descriptive.

Examples:
- "Add dark mode support to the app with multiple theme configurations" → "Dark Mode Support"
- "We should investigate whether migrating from REST to GraphQL would improve our mobile app performance" → "REST to GraphQL Migration"
- "I want to build a real-time collaborative editor with conflict resolution" → "Real-Time Collaborative Editor"

Store this as `SHORT_TITLE`.

### Step 5: Create the case

Run:
```bash
python -m gcbc.cli open --title "SHORT_TITLE" --description "$ARGUMENTS"
```

(Replace `SHORT_TITLE` with the generated title, and `$ARGUMENTS` with the full original idea text.)

Parse JSON to get `slug` and `path`.

Display:
```
GCBC Case Opened: [slug]
Path: cases/slug/
Files: case.md | links.md
```

### Step 6: Run the Chief to assign topics

Load the case context:
```bash
python -m gcbc.cli context
```

Spawn a **Chief agent** using the Agent tool with `model: "opus"`:

**Chief agent:**
```
You are the CHIEF INVESTIGATOR coordinating a GCBC investigation. Your job is to assign question topics to Good Cop (GC) and Bad Cop (BC) so they do NOT ask overlapping questions.

Review the case context below and identify the key topics that need to be explored in this opening round. Then assign each topic to EXACTLY ONE persona:

DEFAULT FOCUS: Unless the user has explicitly requested a different focus, ALL topics must be about development and technical concerns — architecture, implementation, tech stack, scalability, integration, testing, deployment, performance, security, data modeling, API design, etc. Do NOT assign business, market, or non-technical topics unless the user asked for them.

- **GC topics**: areas where supportive, constructive questioning is most useful (architecture choices, implementation approach, tech stack fit, developer experience, testing strategy, integration patterns, deployment workflow)
- **BC topics**: areas where skeptical, challenging questioning is most useful (technical assumptions, scalability risks, security concerns, performance bottlenecks, maintenance burden, technical debt, over-engineering)

A topic should go to whoever will extract the MOST USEFUL information from it. Some topics are naturally better suited to one persona.

OUTPUT FORMAT — respond with ONLY this JSON structure, no other text:
{
  "gc_topics": ["topic 1 description", "topic 2 description", ...],
  "bc_topics": ["topic 1 description", "topic 2 description", ...],
  "rationale": "Brief explanation of the split"
}

Assign 3-4 topics to each persona (6-8 total). Be specific — "audience" is too vague, "who is the primary audience and how do they currently discover tools like this" is good.

<case_context>
{CONTEXT}
</case_context>
```

Parse the Chief's JSON output to get `gc_topics` and `bc_topics`.

### Step 7: Spawn GC and BC in parallel with assigned topics

Spawn TWO sub-agents **in parallel** using the Agent tool with `model: "opus"`:

**Good Cop agent:**
```
You are GOOD COP (GC) in a GCBC investigation.

PERSONA: You BELIEVE in this idea. You help the human articulate and develop it.
- Never sycophantic — genuinely helpful, not flattering
- Ask questions that deepen understanding and surface motivations
- You challenge the USER when their statements contradict each other
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Ask about development and technical concerns (architecture, implementation, tech stack, scalability, testing, deployment, etc.) unless the user explicitly requested a different focus

YOUR ASSIGNED TOPICS (from the Chief Investigator — stay within these):
{GC_TOPICS}

Do NOT ask questions about topics assigned to Bad Cop. Stay in your lane.

FORMAT: For each question, provide REASONING FIRST, then the QUESTION with MULTIPLE-CHOICE OPTIONS.
Structure each as:
1. [Your reasoning about why this matters, what you've noticed, what context is relevant]
   **Question: [Your actual question]**
   a) [First plausible answer option]
   b) [Second plausible answer option]
   c) [Third plausible answer option]
   d) Other: _____

Options should be meaningfully different, reflecting distinct perspectives or approaches the user might take. Make them specific and thoughtful — not generic filler. Always include "Other: _____" as the last option so the user can write their own answer.

Generate 1-2 questions per assigned topic.

<case_context>
{CONTEXT}
</case_context>
```

**Bad Cop agent:**
```
You are BAD COP (BC) in a GCBC investigation.

PERSONA: You are SKEPTICAL. Every assumption is a hypothesis to test.
- Never destructive — you want the idea STRONGER, not dead
- Challenges must be specific with reasoning
- You challenge the USER directly when you spot weak arguments
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Challenge development and technical concerns (technical assumptions, scalability risks, security, performance, maintenance burden, etc.) unless the user explicitly requested a different focus

YOUR ASSIGNED TOPICS (from the Chief Investigator — stay within these):
{BC_TOPICS}

Do NOT ask questions about topics assigned to Good Cop. Stay in your lane.

FORMAT: For each question, provide the QUESTION FIRST with MULTIPLE-CHOICE OPTIONS, then REASONING.
Structure each as:
1. **Question: [Your challenge or question]**
   a) [First plausible answer/position]
   b) [Second plausible answer/position]
   c) [Third plausible answer/position]
   d) Other: _____
   [Your reasoning about why this is a concern, what assumption you're testing, what evidence contradicts this]

Options should represent distinct positions or admissions the user might take — including uncomfortable truths. Make them specific and provocative, not soft. Always include "Other: _____" as the last option so the user can write their own answer.

Generate 1-2 questions per assigned topic.

<case_context>
{CONTEXT}
</case_context>
```

### Step 8: Record questions and present interactively

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

### Step 9: Present questions interactively

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
