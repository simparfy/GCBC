# GCBC — Good Cop Bad Cop Framework

An AI-driven idea investigation framework. Two personas (Good Cop and Bad Cop) interrogate users through multiple rounds, gather evidence, debate each other, and produce final specs with go/no-go verdicts.

## Key Conventions

- All case data lives in `~/.gcbc/cases/{slug}/` — outside the project directory
- Each case directory contains: case.md, links.md, interrogation.md, debate.md, state.json, and optionally verdict.md
- The Python CLI is at `src/gcbc/cli.py` — call it with `python -m gcbc.cli <command>`
- Install: `pip install -e .` from repo root
- All skill files call the Python CLI for file I/O — never write case files directly
- One active case at a time
- Facts are global (stored in `~/.gcbc/facts.md`), shared across all cases
- Links are bidirectional — linking A to B also links B to A

## Model Routing

- **Opus**: Interrogation questions, debate turns, investigation, verdict generation
- **Sonnet**: File writing, formatting, case management operations

## Default Focus

- Interrogation questions should focus primarily on **development and technical topics** — architecture, implementation, tech stack, scalability, integration, testing, deployment, performance, security, etc.
- Business, market, or non-technical questions should only be asked if the user explicitly requests them or if a critical non-technical risk surfaces that demands attention.
- This applies to GC/BC question generation, investigation prompts, and direct conversations.

## Interrogation Rounds

- Each round has **two halves**: Good Cop asks questions first, then Bad Cop challenges the user's answers
- **GC half**: Good Cop explores topics constructively — architecture, tech stack, implementation, etc.
- **BC half**: Bad Cop reads the GC answers and counter-interrogates — probing weak spots, challenging assumptions, stress-testing decisions
- **Rounds loop automatically** — interrogation keeps going until both GC and BC are fully satisfied that nothing is unclear or assumed. The user does NOT need to run `/interrogate` repeatedly.
- No Chief Investigator — each persona picks their own topics freely
- Minimum 3 rounds before sufficiency can be signaled (both GC and BC must agree)
- Both GC and BC MUST output `SUFFICIENT_INFO: true` or `SUFFICIENT_INFO: false` every round — it is never omitted
- Questions are presented one at a time via AskUserQuestion — never dumped in bulk

## GC/BC Communication Styles

- **Good Cop**: Reasoning FIRST, then question (builds context before asking)
- **Bad Cop**: Question FIRST, then reasoning (challenges directly, explains after)
- Both challenge the USER directly — not just the idea abstractly

## Running the CLI

```bash
python -m gcbc.cli --help
python -m gcbc.cli status        # Check active case
python -m gcbc.cli list          # All cases
python -m gcbc.cli open --title "My Idea"
```

## Commands

| Command | Description |
|---|---|
| `/open-case <idea>` | Create case + run first interrogation round |
| `/interrogate [answers]` | Continue interrogation |
| `/gc <message>` | Talk to Good Cop directly |
| `/bc <message>` | Talk to Bad Cop directly |
| `/investigate [focus]` | Evidence gathering |
| `/fact <statement>` | Add global non-negotiable |
| `/case` | Case dashboard |
| `/debate` | Start GC/BC debate |
| `/verdict` | Generate go/no-go recommendation |
| `/close-case` | Archive case |
| `/reopen-case <slug>` | Reopen archived case |
| `/link-case <slug> [note]` | Bidirectional link |
| `/split-case <children>` | Split into child cases |
| `/merge-case <slug>` | Intelligent merge |
