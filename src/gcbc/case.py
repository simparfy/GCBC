"""Core case management logic for GCBC."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml
from slugify import slugify

from . import templates


class CaseError(Exception):
    pass


class CaseNotFoundError(CaseError):
    pass


class CaseAlreadyOpenError(CaseError):
    pass


class NoCaseOpenError(CaseError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify_title(title: str) -> str:
    """Convert title to filesystem-safe slug. Expects a pre-summarized 2-5 word title."""
    return slugify(title, max_length=40)


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse YAML frontmatter from a markdown file.

    Returns (meta_dict, body_text).
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2]
    return meta, body


def _write_frontmatter(path: Path, meta: dict, body: str) -> None:
    """Write YAML frontmatter + body back to a markdown file."""
    fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{fm}---{body}", encoding="utf-8")


def _data_dir() -> Path:
    """Return {project}/.gcbc/ — the root for all GCBC data within the project."""
    return _project_root() / ".gcbc"


def _cases_dir(project_root: Path | None = None) -> Path:
    """Resolve cases directory. All cases live in {project}/.gcbc/cases/."""
    import os
    env = os.environ.get("GCBC_CASES_DIR")
    if env:
        return Path(env)
    if project_root:
        return project_root / ".gcbc" / "cases"
    return _data_dir() / "cases"


def _case_dir(slug: str) -> Path:
    """Return {project}/.gcbc/cases/{slug}/, creating it if needed."""
    d = _cases_dir() / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def _project_root() -> Path:
    """Find project root by looking for pyproject.toml or .git."""
    p = Path.cwd()
    for parent in [p, *p.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return p


def _load_internal_state(slug: str) -> dict:
    """Load internal state from .gcbc/cases/{slug}/state.json."""
    defaults = {
        "round_count": 0,
        "debate_attempts": 0,
        "phase": "gc",
        "gc_rounds": 0,
        "bc_rounds": 0,
    }
    state_file = _case_dir(slug) / "state.json"
    if state_file.exists():
        stored = json.loads(state_file.read_text(encoding="utf-8"))
        return {**defaults, **stored}
    return defaults


def _save_internal_state(slug: str, state: dict) -> None:
    """Save internal state to .gcbc/cases/{slug}/state.json."""
    state_file = _case_dir(slug) / "state.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def find_active_case(cases_dir: Path) -> Path | None:
    """Find the first case with status=open. Returns case directory path."""
    if not cases_dir.exists():
        return None
    for d in sorted(cases_dir.iterdir()):
        if not d.is_dir():
            continue
        case_file = d / "case.md"
        if not case_file.exists():
            continue
        meta, _ = _parse_frontmatter(case_file)
        if meta.get("status") == "open":
            return d
    return None


def list_all_cases(cases_dir: Path) -> list[dict]:
    """List all cases with their metadata."""
    results = []
    if not cases_dir.exists():
        return results
    for d in sorted(cases_dir.iterdir()):
        if not d.is_dir():
            continue
        case_file = d / "case.md"
        if not case_file.exists():
            continue
        meta, _ = _parse_frontmatter(case_file)
        slug = meta.get("slug", d.name)
        state = _load_internal_state(slug)
        results.append({
            "slug": slug,
            "title": meta.get("title", ""),
            "status": meta.get("status", "unknown"),
            "created": meta.get("created", ""),
            "updated": meta.get("updated", ""),
            "round_count": state.get("round_count", 0),
            "debate_attempts": state.get("debate_attempts", 0),
            "parent": meta.get("parent"),
            "children": meta.get("children", []),
        })
    return results


def load_case_meta(case_path: Path) -> dict:
    """Load case.md frontmatter."""
    meta, _ = _parse_frontmatter(case_path / "case.md")
    return meta


def save_case_meta(case_path: Path, meta: dict) -> None:
    """Update case.md frontmatter, preserving body."""
    case_file = case_path / "case.md"
    _, body = _parse_frontmatter(case_file)
    meta["updated"] = _now()
    _write_frontmatter(case_file, meta, body)


def create_case(cases_dir: Path, title: str, description: str = "") -> tuple[str, Path]:
    """Create a new case directory with all template files.

    Returns (slug, case_path).
    """
    base_slug = slugify_title(title)
    if not base_slug:
        base_slug = "untitled"

    # Handle slug collision
    slug = base_slug
    for i in range(2, 100):
        case_path = cases_dir / slug
        if not case_path.exists():
            break
        slug = f"{base_slug}-{i}"
    else:
        raise CaseError(f"Too many slug collisions for '{base_slug}'")

    case_path = cases_dir / slug
    case_path.mkdir(parents=True, exist_ok=True)

    ts = _now()

    if not description:
        description = title

    # All case files live in {project}/cases/{slug}/
    (case_path / "case.md").write_text(
        templates.case_md(slug, title, description, ts), encoding="utf-8"
    )
    (case_path / "links.md").write_text(
        templates.links_md(title), encoding="utf-8"
    )
    (case_path / "interrogation.md").write_text(
        templates.interrogation_md(title), encoding="utf-8"
    )
    (case_path / "debate.md").write_text(
        templates.debate_md(title), encoding="utf-8"
    )

    return slug, case_path


def close_case(case_path: Path) -> None:
    """Set case status to closed."""
    meta = load_case_meta(case_path)
    if meta.get("status") != "open":
        raise CaseError(f"Case is not open (status: {meta.get('status')})")
    meta["status"] = "closed"
    save_case_meta(case_path, meta)


def reopen_case(cases_dir: Path, slug: str) -> Path:
    """Reopen a closed case."""
    case_path = cases_dir / slug
    if not case_path.exists():
        raise CaseNotFoundError(f"Case '{slug}' not found")

    meta = load_case_meta(case_path)
    if meta.get("status") == "open":
        raise CaseAlreadyOpenError(f"Case '{slug}' is already open")
    if meta.get("status") not in ("closed", "split", "merged"):
        raise CaseError(f"Cannot reopen case with status: {meta.get('status')}")

    meta["status"] = "open"
    save_case_meta(case_path, meta)
    return case_path


def increment_round(case_path: Path) -> int:
    """Increment round_count in internal state. Returns new count."""
    meta = load_case_meta(case_path)
    slug = meta.get("slug", case_path.name)
    state = _load_internal_state(slug)
    state["round_count"] = state.get("round_count", 0) + 1
    _save_internal_state(slug, state)
    return state["round_count"]


def increment_debate_attempts(case_path: Path) -> int:
    """Increment debate_attempts in internal state. Returns new count."""
    meta = load_case_meta(case_path)
    slug = meta.get("slug", case_path.name)
    state = _load_internal_state(slug)
    state["debate_attempts"] = state.get("debate_attempts", 0) + 1
    _save_internal_state(slug, state)
    return state["debate_attempts"]


def set_phase(case_path: Path, phase: str) -> str:
    """Set the interrogation phase. Valid values: 'gc', 'bc', 'done'. Returns the new phase."""
    if phase not in ("gc", "bc", "done"):
        raise CaseError(f"Invalid phase: {phase}. Must be 'gc', 'bc', or 'done'.")
    meta = load_case_meta(case_path)
    slug = meta.get("slug", case_path.name)
    state = _load_internal_state(slug)
    state["phase"] = phase
    _save_internal_state(slug, state)
    return phase


def append_to_transcript(case_path: Path, content: str) -> None:
    """Append content to interrogation.md."""
    slug = load_case_meta(case_path).get("slug", case_path.name)
    f = _case_dir(slug) / "interrogation.md"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"\n{content}\n")


def append_to_debate(case_path: Path, content: str) -> None:
    """Append content to debate.md."""
    slug = load_case_meta(case_path).get("slug", case_path.name)
    f = _case_dir(slug) / "debate.md"
    with f.open("a", encoding="utf-8") as fh:
        fh.write(f"\n{content}\n")


def append_fact(project_root: Path, statement: str) -> tuple[bool, str]:
    """Append a fact to the global facts.md in {project}/.gcbc/. Returns (added, reason)."""
    data_dir = _data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    facts_file = data_dir / "facts.md"

    if not facts_file.exists():
        facts_file.write_text(templates.facts_md(), encoding="utf-8")

    existing = facts_file.read_text(encoding="utf-8")

    # Dedupe check: normalize for comparison
    normalized = statement.strip().lower()
    for line in existing.splitlines():
        line_stripped = line.strip().lstrip("- ").strip().lower()
        if line_stripped == normalized:
            return False, "duplicate"

    ts = _now()
    with facts_file.open("a", encoding="utf-8") as fh:
        fh.write(f"\n- {statement.strip()}  <!-- {ts} -->\n")

    return True, "ok"


def append_link(cases_dir: Path, source_path: Path, target_slug: str, note: str = "") -> None:
    """Add bidirectional link between source case and target case."""
    target_path = cases_dir / target_slug
    if not target_path.exists():
        raise CaseNotFoundError(f"Target case '{target_slug}' not found")

    source_meta = load_case_meta(source_path)
    source_slug = source_meta.get("slug", source_path.name)

    if target_slug == source_slug:
        raise CaseError("Cannot link a case to itself")

    note_text = f" — {note}" if note else ""

    # Add link to source
    source_links = source_path / "links.md"
    with source_links.open("a", encoding="utf-8") as fh:
        fh.write(f"\n- [{target_slug}]{note_text}\n")

    # Add reverse link to target
    target_links = target_path / "links.md"
    with target_links.open("a", encoding="utf-8") as fh:
        fh.write(f"\n- [{source_slug}]{note_text}\n")


def write_verdict(case_path: Path, content: str) -> None:
    """Create or update verdict.md with changelog entry."""
    verdict_file = case_path / "verdict.md"
    ts = _now()

    if verdict_file.exists():
        existing = verdict_file.read_text(encoding="utf-8")
        # Append changelog entry
        changelog_entry = f"- [{ts}] Updated verdict\n"
        if "## Changelog" in existing:
            existing += changelog_entry
        else:
            existing += f"\n## Changelog\n\n{changelog_entry}"
        # Replace content above changelog
        verdict_file.write_text(content, encoding="utf-8")
    else:
        verdict_file.write_text(content, encoding="utf-8")


def read_full_case_context(case_path: Path) -> str:
    """Read all case files into a single tagged context string."""
    parts = []

    # All case files live in {project}/.gcbc/cases/{slug}/
    for filename in ["case.md", "links.md", "verdict.md", "interrogation.md", "debate.md"]:
        f = case_path / filename
        if f.exists():
            content = f.read_text(encoding="utf-8")
            parts.append(f'<file name="{filename}">\n{content}\n</file>')

    # Include global facts from {project}/.gcbc/facts.md
    facts_file = _data_dir() / "facts.md"
    if facts_file.exists():
        content = facts_file.read_text(encoding="utf-8")
        parts.append(f'<file name="facts.md" scope="global">\n{content}\n</file>')

    return "\n\n".join(parts)


def split_case(cases_dir: Path, parent_path: Path, child_names: list[str]) -> list[tuple[str, Path]]:
    """Split a case into child cases. Returns list of (slug, path) for children."""
    parent_meta = load_case_meta(parent_path)
    parent_slug = parent_meta.get("slug", parent_path.name)
    parent_title = parent_meta.get("title", "")

    children = []
    child_slugs = []

    for name in child_names:
        child_slug = f"{parent_slug}--{slugify_title(name)}"
        child_title = f"{parent_title} — {name.strip()}"
        child_slug_result, child_path = create_case(
            cases_dir, child_title, f"Split from [{parent_slug}]: {name.strip()}"
        )
        # Override slug to use parent--child format
        child_meta = load_case_meta(child_path)
        child_meta["parent"] = parent_slug
        save_case_meta(child_path, child_meta)

        # Link child back to parent
        child_links = child_path / "links.md"
        with child_links.open("a", encoding="utf-8") as fh:
            fh.write(f"\n- [{parent_slug}] — parent case\n")

        children.append((child_slug_result, child_path))
        child_slugs.append(child_slug_result)

    # Update parent
    parent_meta["status"] = "split"
    parent_meta["children"] = child_slugs
    save_case_meta(parent_path, parent_meta)

    # Link parent to children
    parent_links = parent_path / "links.md"
    with parent_links.open("a", encoding="utf-8") as fh:
        for cs in child_slugs:
            fh.write(f"\n- [{cs}] — child case\n")

    return children


def merge_case(cases_dir: Path, active_path: Path, source_slug: str) -> Path:
    """Mark source case as merged into active case. Returns source path.

    Note: The actual content rewriting is done by GC/BC agents in the skill file.
    This function handles the metadata/status updates only.
    """
    source_path = cases_dir / source_slug
    if not source_path.exists():
        raise CaseNotFoundError(f"Source case '{source_slug}' not found")

    active_meta = load_case_meta(active_path)
    source_meta = load_case_meta(source_path)
    active_slug = active_meta.get("slug", active_path.name)

    # Update source
    source_meta["status"] = "merged"
    source_meta["merged_into"] = active_slug
    save_case_meta(source_path, source_meta)

    # Update active
    merged_from = active_meta.get("merged_from", []) or []
    merged_from.append(source_slug)
    active_meta["merged_from"] = merged_from
    save_case_meta(active_path, active_meta)

    return source_path
