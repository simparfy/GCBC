"""Markdown templates for GCBC case files."""


def case_md(slug: str, title: str, description: str, timestamp: str) -> str:
    return f"""---
status: open
title: "{title}"
slug: "{slug}"
created: "{timestamp}"
updated: "{timestamp}"
parent: null
children: []
merged_from: []
---

# Case: {title}

## Description

{description}
"""


def interrogation_md(title: str) -> str:
    return f"""# Interrogation Transcript — {title}

This file contains the full record of all interrogation rounds.

---
"""


def links_md(title: str) -> str:
    return f"""# Case Links — {title}

Related cases linked with `/link-case`.

---
"""


def debate_md(title: str) -> str:
    return f"""# GC/BC Debate Transcript — {title}

This file records the background debate between Good Cop and Bad Cop.

---
"""


def verdict_md(title: str, problem: str, solution: str, facts: str,
               open_questions: str, links: str, timestamp: str,
               debate_turns: int, round_count: int) -> str:
    return f"""# Verdict — {title}

## Problem

{problem}

## Solution

{solution}

## Non-Negotiables

{facts}

## Open Questions

{open_questions}

## Links

{links}

## Changelog

- [{timestamp}] Initial verdict written after {round_count} rounds, {debate_turns} debate turns
"""


def facts_md() -> str:
    return """# Facts (Non-Negotiables)

These are constraints added with `/fact`. They are treated as hard requirements
across ALL cases and will appear in every verdict's Non-Negotiables section.

---
"""
