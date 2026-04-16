# /link-case — Link current case to another case

Create a bidirectional link between the active case and a target case.

## Arguments

`$ARGUMENTS` = target slug, optionally followed by a note.

## Process

### Step 1: Parse arguments

Split `$ARGUMENTS`: first token is the target slug, remainder is the note.

If empty:
```bash
python -m gcbc.cli list
```
Display all cases and usage:
```
Usage: /link-case <target-slug> [optional note]
Example: /link-case add-dark-mode Related theming work
```
Then stop.

### Step 2: Link

```bash
python -m gcbc.cli add-link --target-slug "[target]" --note "[note]"
```

On success:
```
Linked: [active-slug] <-> [target-slug]
Note: [note]

Both cases' links.md files have been updated.
```

On error (target not found, self-link), display the error.
