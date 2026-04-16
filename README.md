# GCBC — Good Cop Bad Cop

An AI-driven idea investigation framework for Claude Code. Two AI personas — Good Cop (supportive) and Bad Cop (skeptical) — interrogate you through multiple rounds, gather evidence, debate each other, and produce final specs with go/no-go verdicts.

## Install

**One-liner (bash):**
```bash
curl -fsSL https://raw.githubusercontent.com/simparfy/GCBC/main/install.sh | bash
```

**PowerShell (Windows):**
```powershell
irm https://raw.githubusercontent.com/simparfy/GCBC/main/install.ps1 | iex
```

**Manual:**
```bash
git clone https://github.com/simparfy/GCBC.git ~/.gcbc
pip install -e ~/.gcbc
```

## Upgrade

```bash
gcbc upgrade
```

## Uninstall

```bash
gcbc uninstall
```

## Quick Start

```
/open-case Add offline sync support to the mobile app
```

Good Cop and Bad Cop will immediately start interrogating you with 5+ deep questions each. Answer them, then:

```
/interrogate Here are my answers: ...
```

Continue for as many rounds as needed. When ready:

```
/debate
```

GC and BC debate in 3-5 turns. If they agree, a verdict is written. Then:

```
/verdict
```

Get a final GO / NO-GO / CONDITIONAL recommendation.

## Commands

| Command | Description |
|---|---|
| `/open-case <idea>` | Create a case and start interrogation |
| `/interrogate [answers]` | Continue with answers, get next questions |
| `/gc <message>` | Talk directly to Good Cop |
| `/bc <message>` | Talk directly to Bad Cop |
| `/investigate [focus]` | GC/BC search web + codebase for evidence |
| `/fact <statement>` | Add a global non-negotiable |
| `/case` | Show case dashboard |
| `/debate` | Start GC/BC background debate |
| `/verdict` | Generate GO / NO-GO / CONDITIONAL |
| `/close-case` | Archive current case |
| `/reopen-case <slug>` | Reopen an archived case |
| `/link-case <slug> [note]` | Link two cases (bidirectional) |
| `/split-case <child1, child2>` | Split case into children |
| `/merge-case <slug>` | Merge case into active case |

## How It Works

1. **Open a case** with your idea
2. **Interrogation**: GC asks supportive questions (reasoning first), BC asks challenging questions (question first). 5+ deep questions per agent per round.
3. **Investigation** (optional): GC searches for supporting evidence, BC for contradicting evidence
4. **Debate**: When ready, GC and BC debate in 5 sequential turns. They can suggest splitting or reopening cases.
5. **Verdict**: After consensus, a structured spec is written. `/verdict` adds a GO/NO-GO recommendation.

## Key Design Choices

- **Asymmetric styles**: GC builds context then asks. BC questions then explains.
- **Both challenge YOU**: Not just the idea — your statements and contradictions too.
- **Facts are global**: Non-negotiables apply across all cases.
- **Links are bidirectional**: Linking A to B links B to A.
- **Verdict is living**: Updated as new rounds and debates occur, with a changelog.
- **Agents can suggest splits/reopens**: During debate, GC/BC proactively manage the case landscape.

## License

AGPL-3.0
