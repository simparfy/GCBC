"""GCBC CLI — Typer-based command interface for case management."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import typer

from . import __version__, GITHUB_REPO, GITHUB_URL
from . import case as cm

app = typer.Typer(add_completion=False, no_args_is_help=True)


def _out(data: dict) -> None:
    """Print JSON to stdout."""
    typer.echo(json.dumps(data, indent=2))


def _err(msg: str, code: int = 1) -> None:
    """Print error to stderr and exit."""
    typer.echo(json.dumps({"error": msg}), err=True)
    raise typer.Exit(code)


def _cases_dir() -> Path:
    return cm._cases_dir()


def _require_active() -> tuple[Path, dict]:
    """Get active case or exit with error."""
    cd = _cases_dir()
    active = cm.find_active_case(cd)
    if active is None:
        _err("No open case found. Start one with /open-case <idea>.")
    meta = cm.load_case_meta(active)
    return active, meta


@app.command("open")
def cmd_open(
    title: str = typer.Option(..., help="Case title"),
    description: str = typer.Option("", help="Case description"),
) -> None:
    """Create a new case."""
    cd = _cases_dir()

    # Check for existing active case
    active = cm.find_active_case(cd)
    if active is not None:
        meta = cm.load_case_meta(active)
        _err(f"Case already open: [{meta.get('slug')}] {meta.get('title')}")

    slug, path = cm.create_case(cd, title, description)
    _out({"slug": slug, "path": str(path), "status": "open"})


@app.command("close")
def cmd_close() -> None:
    """Close the active case."""
    active, meta = _require_active()
    cm.close_case(active)
    _out({"slug": meta["slug"], "status": "closed"})


@app.command("reopen")
def cmd_reopen(
    slug: str = typer.Option(..., help="Case slug to reopen"),
) -> None:
    """Reopen a closed case."""
    cd = _cases_dir()

    # Check for existing active case
    active = cm.find_active_case(cd)
    if active is not None:
        ameta = cm.load_case_meta(active)
        _err(f"Close current case [{ameta.get('slug')}] first.")

    try:
        path = cm.reopen_case(cd, slug)
        state = cm._load_internal_state(slug)
        _out({"slug": slug, "status": "open", "round_count": state.get("round_count", 0)})
    except cm.CaseNotFoundError as e:
        _err(str(e))
    except cm.CaseAlreadyOpenError as e:
        _err(str(e))


@app.command("status")
def cmd_status() -> None:
    """Show active case status."""
    cd = _cases_dir()
    active = cm.find_active_case(cd)
    if active is None:
        _out({"active": False})
        return
    meta = cm.load_case_meta(active)
    slug = meta.get("slug", active.name)
    state = cm._load_internal_state(slug)
    _out({
        "active": True,
        "slug": slug,
        "title": meta.get("title", ""),
        "status": meta.get("status", ""),
        "round_count": state.get("round_count", 0),
        "debate_attempts": state.get("debate_attempts", 0),
        "phase": state.get("phase", "gc"),
        "gc_rounds": state.get("gc_rounds", 0),
        "bc_rounds": state.get("bc_rounds", 0),
        "created": meta.get("created", ""),
        "updated": meta.get("updated", ""),
        "parent": meta.get("parent"),
        "children": meta.get("children", []),
        "merged_from": meta.get("merged_from", []),
        "path": str(active),
    })


@app.command("list")
def cmd_list() -> None:
    """List all cases."""
    cd = _cases_dir()
    cases = cm.list_all_cases(cd)
    _out({"cases": cases, "count": len(cases)})


@app.command("increment-round")
def cmd_increment_round() -> None:
    """Increment the round counter for the active case."""
    active, _ = _require_active()
    new_round = cm.increment_round(active)
    _out({"round": new_round})


@app.command("increment-debate")
def cmd_increment_debate() -> None:
    """Increment the debate attempts counter for the active case."""
    active, _ = _require_active()
    new_count = cm.increment_debate_attempts(active)
    _out({"debate_attempts": new_count})


@app.command("set-phase")
def cmd_set_phase(
    phase: str = typer.Option(..., help="Phase to set: gc, bc, or done"),
) -> None:
    """Set the interrogation phase for the active case."""
    active, _ = _require_active()
    try:
        new_phase = cm.set_phase(active, phase)
        _out({"phase": new_phase})
    except cm.CaseError as e:
        _err(str(e))


@app.command("append-transcript")
def cmd_append_transcript(
    content: str = typer.Option(..., help="Content to append"),
) -> None:
    """Append content to interrogation.md."""
    active, _ = _require_active()
    cm.append_to_transcript(active, content)
    _out({"appended": True})


@app.command("append-debate")
def cmd_append_debate(
    content: str = typer.Option(..., help="Content to append"),
) -> None:
    """Append content to debate.md."""
    active, _ = _require_active()
    cm.append_to_debate(active, content)
    _out({"appended": True})


@app.command("add-fact")
def cmd_add_fact(
    statement: str = typer.Option(..., help="Fact statement"),
) -> None:
    """Add a fact to the global facts.md."""
    root = cm._project_root()
    added, reason = cm.append_fact(root, statement)
    _out({"added": added, "reason": reason})


@app.command("add-link")
def cmd_add_link(
    target_slug: str = typer.Option(..., help="Target case slug"),
    note: str = typer.Option("", help="Optional note about the link"),
) -> None:
    """Link the active case to another case (bidirectional)."""
    cd = _cases_dir()
    active, _ = _require_active()
    try:
        cm.append_link(cd, active, target_slug, note)
        _out({"linked": True, "target": target_slug})
    except cm.CaseNotFoundError as e:
        _err(str(e))
    except cm.CaseError as e:
        _err(str(e))


@app.command("write-verdict")
def cmd_write_verdict(
    content: str = typer.Option(..., help="Verdict content"),
) -> None:
    """Write or update verdict.md for the active case."""
    active, _ = _require_active()
    cm.write_verdict(active, content)
    _out({"written": True})


@app.command("context")
def cmd_context() -> None:
    """Dump full case context for the active case."""
    active, _ = _require_active()
    context = cm.read_full_case_context(active)
    # Output raw text, not JSON, for agent consumption
    typer.echo(context)


@app.command("save-questions")
def cmd_save_questions() -> None:
    """Save questions JSON from stdin for interactive answering."""
    import sys
    active, meta = _require_active()
    data = sys.stdin.read()
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        _err(f"Invalid JSON: {e}")
    slug = meta.get("slug", active.name)
    internal = cm._case_dir(slug)
    qfile = internal / "questions.json"
    qfile.write_text(data, encoding="utf-8")
    count = len(parsed.get("questions", []))
    _out({"saved": True, "path": str(qfile), "question_count": count})


@app.command("ask")
def cmd_ask() -> None:
    """Run interactive questionnaire for the active case."""
    active, meta = _require_active()
    try:
        from .interactive import run_questionnaire
        answers = run_questionnaire(active)
        if not answers:
            raise typer.Exit(1)
    except FileNotFoundError as e:
        _err(str(e))
    except KeyboardInterrupt:
        typer.echo("\nCancelled.")
        raise typer.Exit(1)


@app.command("read-answers")
def cmd_read_answers() -> None:
    """Read and consume saved interactive answers. Deletes answers.json after reading."""
    active, meta = _require_active()
    slug = meta.get("slug", active.name)
    afile = cm._case_dir(slug) / "answers.json"
    if not afile.exists():
        _out({"has_answers": False})
        return
    data = json.loads(afile.read_text(encoding="utf-8"))
    from .interactive import format_answers_for_transcript
    formatted = format_answers_for_transcript(data["answers"])
    afile.unlink()
    _out({"has_answers": True, "formatted": formatted})


@app.command("slug")
def cmd_slug(
    title: str = typer.Option(..., help="Title to slugify"),
) -> None:
    """Preview slug generation for a title."""
    _out({"slug": cm.slugify_title(title)})


@app.command("split")
def cmd_split(
    children: str = typer.Option(..., help="Comma-separated child names"),
) -> None:
    """Split the active case into child cases."""
    cd = _cases_dir()
    active, _ = _require_active()
    child_names = [c.strip() for c in children.split(",") if c.strip()]
    if len(child_names) < 2:
        _err("Need at least 2 child names to split.")
    results = cm.split_case(cd, active, child_names)
    _out({
        "split": True,
        "children": [{"slug": s, "path": str(p)} for s, p in results],
    })


@app.command("merge")
def cmd_merge(
    source_slug: str = typer.Option(..., help="Source case slug to merge in"),
) -> None:
    """Merge a source case into the active case (metadata only)."""
    cd = _cases_dir()
    active, _ = _require_active()
    try:
        source_path = cm.merge_case(cd, active, source_slug)
        _out({"merged": True, "source": source_slug, "source_path": str(source_path)})
    except cm.CaseNotFoundError as e:
        _err(str(e))


@app.command("get-case")
def cmd_get_case(
    slug: str = typer.Option(..., help="Case slug to read"),
) -> None:
    """Read a specific case's full context (for merge operations)."""
    cd = _cases_dir()
    case_path = cd / slug
    if not case_path.exists():
        _err(f"Case '{slug}' not found")
    context = cm.read_full_case_context(case_path)
    typer.echo(context)


def _get_install_dir() -> Path:
    """Get the directory where gcbc is installed (the repo root)."""
    return Path(__file__).resolve().parent.parent.parent


def _latest_version_from_github() -> str | None:
    """Fetch the latest version tag from GitHub. Returns None on failure."""
    import urllib.request
    import urllib.error

    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            tag = data.get("tag_name", "")
            return tag.lstrip("v")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError):
        return None


@app.command("version")
def cmd_version(
    check: bool = typer.Option(False, "--check", help="Check for updates on GitHub"),
) -> None:
    """Show GCBC version."""
    result: dict = {"version": __version__}
    install_dir = _get_install_dir()
    result["install_dir"] = str(install_dir)

    if check:
        latest = _latest_version_from_github()
        if latest is None:
            result["latest"] = None
            result["update_available"] = None
            result["check_error"] = "Could not reach GitHub"
        else:
            result["latest"] = latest
            result["update_available"] = latest != __version__

    _out(result)


@app.command("upgrade")
def cmd_upgrade() -> None:
    """Upgrade GCBC to the latest version."""
    install_dir = _get_install_dir()
    git_dir = install_dir / ".git"

    if not git_dir.is_dir():
        _err(f"Not a git repository: {install_dir}. Re-clone from {GITHUB_URL}")

    typer.echo(f"Upgrading GCBC in {install_dir} ...")

    # Fetch latest
    res = subprocess.run(
        ["git", "fetch", "--tags", "origin"],
        cwd=install_dir, capture_output=True, text=True,
    )
    if res.returncode != 0:
        _err(f"git fetch failed: {res.stderr.strip()}")

    # Pull latest main
    res = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=install_dir, capture_output=True, text=True,
    )
    if res.returncode != 0:
        _err(f"git pull failed: {res.stderr.strip()}")

    typer.echo(res.stdout.strip())

    # Reinstall package
    res = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(install_dir), "--quiet"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        _err(f"pip install failed: {res.stderr.strip()}")

    # Re-read version from the updated package
    # (the current process still has the old version in memory)
    res = subprocess.run(
        [sys.executable, "-c", "from gcbc import __version__; print(__version__)"],
        capture_output=True, text=True,
    )
    new_version = res.stdout.strip() if res.returncode == 0 else "unknown"

    _out({
        "upgraded": True,
        "previous_version": __version__,
        "current_version": new_version,
    })


@app.command("uninstall")
def cmd_uninstall() -> None:
    """Uninstall GCBC."""
    install_dir = _get_install_dir()

    typer.echo("Uninstalling GCBC ...")
    res = subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "gcbc", "-y"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        _err(f"pip uninstall failed: {res.stderr.strip()}")

    data_dir = cm._data_dir()
    _out({
        "uninstalled": True,
        "note": f"The gcbc CLI has been removed. "
                f"Case data remains in {data_dir}. "
                f"To fully remove, delete {install_dir} and {data_dir}",
    })


if __name__ == "__main__":
    app()
