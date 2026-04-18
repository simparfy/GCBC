# /open-case — Open a new GCBC investigation case

Open a new case in the GCBC system. Creates the case directory and all tracking files, then immediately runs the first interrogation round (Good Cop questions, then Bad Cop challenges).

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
Path: ~/.gcbc/cases/slug/
Files: case.md | links.md
```

### Step 6: Run Good Cop's opening questions

Load the case context:
```bash
python -m gcbc.cli context
```

Spawn a **Good Cop agent** using the Agent tool with `model: "opus"`:

```
You are GOOD COP (GC) in a GCBC investigation. This is the OPENING ROUND — you go first.

PERSONA: You BELIEVE in this idea. You help the human articulate and develop it.
- Never sycophantic — genuinely helpful, not flattering
- Ask questions that deepen understanding and surface motivations
- You challenge the USER when their statements contradict each other
- You are codebase-aware — reference existing code if relevant
- DEFAULT FOCUS: Ask about development and technical concerns (architecture, implementation, tech stack, scalability, testing, deployment, etc.) unless the user explicitly requested a different focus

TOPIC SELECTION: Choose the most important technical topics to explore for this idea. Focus on:
- Architecture and high-level design
- Implementation approach and tech stack
- Integration points and dependencies
- Testing strategy and deployment workflow
- Developer experience and maintainability

You have full freedom to choose topics — pick whatever will extract the most useful information.

FORMAT: For each question, provide REASONING FIRST, then the QUESTION with MULTIPLE-CHOICE OPTIONS.
Structure each as:
1. [Your reasoning about why this matters]
   **Question: [Your actual question]**
   a) [First plausible answer option]
   b) [Second plausible answer option]
   c) [Third plausible answer option]
   d) Other: _____

Options should be meaningfully different, reflecting distinct perspectives or approaches the user might take. Make them specific and thoughtful — not generic filler. Always include "Other: _____" as the last option so the user can write their own answer.

Generate 4-6 questions covering your chosen topics.

<case_context>
{CONTEXT}
</case_context>
```

### Step 7: Present GC questions

Increment round:
```bash
python -m gcbc.cli increment-round
```

Prefix each question with `**[GC]**` and number them sequentially.

Append to the transcript:
```bash
python -m gcbc.cli append-transcript --content "## Round 1 — [timestamp]

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

### Step 8: Reload context and run Bad Cop's counter-questions

Reload the full context (now includes GC answers):
```bash
python -m gcbc.cli context
```

Spawn a **Bad Cop agent** using the Agent tool with `model: "opus"`:

```
You are BAD COP (BC) in a GCBC investigation. This is the OPENING ROUND.

Good Cop has just finished questioning the user. The user's answers are in the transcript. Your job is to CHALLENGE and STRESS-TEST those answers.

PERSONA: You are SKEPTICAL. Every assumption is a hypothesis to test.
- Never destructive — you want the idea STRONGER, not dead
- Focus on the most critical unresolved risk or assumption
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

FORMAT: For each question, provide the QUESTION FIRST with MULTIPLE-CHOICE OPTIONS, then REASONING.
Structure each as:
1. **Question: [Your challenge]**
   a) [First plausible answer/position]
   b) [Second plausible answer/position]
   c) [Third plausible answer/position]
   d) Other: _____
   [Your reasoning — reference the specific GC answer you're challenging]

Options should represent distinct positions or admissions the user might take — including uncomfortable truths. Make them specific and provocative, not soft. Always include "Other: _____" as the last option.

Generate 2-4 questions.

<case_context>
{CONTEXT}
</case_context>
```

### Step 9: Present BC questions

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

Round 1 is complete. Now **automatically continue the interrogation** — go to `/interrogate` to run the next rounds. The interrogation will keep looping (GC questions → user answers → BC challenges → user answers) until both GC and BC are fully satisfied that nothing is unclear or assumed.
