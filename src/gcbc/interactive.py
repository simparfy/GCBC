"""Interactive questionnaire for GCBC interrogation rounds.

Presents questions one at a time with arrow-key navigation,
single/multi select, and custom text input.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

OTHER_OPTION = "\u270f  Type my own answer"
MULTI_OPTION = "\u229e  Select multiple"


@dataclass
class Question:
    id: int
    persona: str  # "GC" or "BC"
    reasoning: str
    question: str
    options: list[str]
    multi_select: bool = False


def _get_internal_dir(case_path: Path) -> Path:
    """Get the ~/.gcbc/cases/{slug}/ directory for AI-internal files."""
    from . import case as cm
    meta = cm.load_case_meta(case_path)
    slug = meta.get("slug", case_path.name)
    return cm._internal_case_dir(slug)


def load_questions(case_path: Path) -> tuple[int, list[Question]]:
    """Load questions from questions.json in ~/.gcbc/."""
    qfile = _get_internal_dir(case_path) / "questions.json"
    if not qfile.exists():
        raise FileNotFoundError("No questions found. Run an interrogation first.")
    data = json.loads(qfile.read_text(encoding="utf-8"))
    questions = [Question(**q) for q in data["questions"]]
    round_num = data.get("round", 0)
    return round_num, questions


def save_questions(case_path: Path, questions: list[Question], round_num: int) -> Path:
    """Save questions to questions.json in ~/.gcbc/."""
    internal = _get_internal_dir(case_path)
    qfile = internal / "questions.json"
    data = {
        "round": round_num,
        "questions": [asdict(q) for q in questions],
    }
    qfile.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return qfile


def _show_question_header(q: Question, current: int, total: int) -> None:
    """Display the question context/reasoning in a rich panel."""
    persona_color = "green" if q.persona == "GC" else "red"
    persona_label = "Good Cop" if q.persona == "GC" else "Bad Cop"

    title = Text()
    title.append(f" {current}/{total} ", style="bold")
    title.append(f"[{persona_label}]", style=f"bold {persona_color}")

    body = ""
    if q.reasoning:
        body += f"[dim italic]{q.reasoning}[/dim italic]\n\n"
    body += f"[bold]{q.question}[/bold]"

    console.print()
    console.print(Panel(
        body,
        title=title,
        border_style=persona_color,
        padding=(1, 2),
    ))


def run_questionnaire(case_path: Path) -> list[dict]:
    """Run the interactive questionnaire and return answers."""
    import questionary
    from questionary import Style

    style = Style([
        ("qmark", "fg:cyan bold"),
        ("question", "bold"),
        ("answer", "fg:green bold"),
        ("pointer", "fg:cyan bold"),
        ("highlighted", "fg:cyan bold"),
        ("selected", "fg:green"),
        ("instruction", "fg:white dim"),
    ])

    round_num, questions = load_questions(case_path)
    total = len(questions)
    answers: list[dict] = []

    console.print()
    console.print(Panel(
        "[bold]Answer each question using \u2191\u2193 arrows.[/bold]\n"
        "Press [bold]Enter[/bold] to select.\n"
        "Choose [cyan]\u270f  Type my own answer[/cyan] for a custom response.\n"
        "Choose [cyan]\u229e  Select multiple[/cyan] to pick more than one.\n"
        "Press [bold]Ctrl+C[/bold] to cancel.",
        title="[bold cyan] GCBC Interactive Interrogation [/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    for idx, q in enumerate(questions, 1):
        _show_question_header(q, idx, total)

        if q.multi_select:
            answer = _ask_multi(q, style)
        else:
            answer = _ask_single(q, style)

        if answer is None:
            console.print("\n[yellow]Interrogation cancelled.[/yellow]")
            return []

        answers.append(answer)
        short = _format_short_answer(answer)
        console.print(f"  [green]\u2713[/green] {short}")

    # Save answers
    _save_answers(case_path, answers, round_num)

    console.print()
    console.print(Panel(
        "[bold green]All questions answered![/bold green]\n\n"
        "Run [bold cyan]/interrogate[/bold cyan] to continue the investigation.",
        border_style="green",
        padding=(1, 2),
    ))

    return answers


def _ask_single(q: Question, style: object) -> dict | None:
    """Single-select question with option to switch to multi."""
    import questionary

    choices = list(q.options) + [MULTI_OPTION, OTHER_OPTION]

    choice = questionary.select(
        "",
        choices=choices,
        style=style,
        instruction="(\u2191\u2193 navigate, Enter select)",
        qmark="",
    ).ask()

    if choice is None:
        return None

    if choice == MULTI_OPTION:
        return _ask_multi(q, style)

    if choice == OTHER_OPTION:
        custom = questionary.text(
            "Your answer:",
            style=style,
        ).ask()
        if custom is None:
            return None
        return {
            "id": q.id,
            "persona": q.persona,
            "question": q.question,
            "selected": [custom],
            "custom": True,
        }

    return {
        "id": q.id,
        "persona": q.persona,
        "question": q.question,
        "selected": [choice],
        "custom": False,
    }


def _ask_multi(q: Question, style: object) -> dict | None:
    """Multi-select question with checkboxes."""
    import questionary

    choices = list(q.options) + [OTHER_OPTION]

    selected = questionary.checkbox(
        "Select all that apply:",
        choices=choices,
        style=style,
        instruction="(\u2191\u2193 navigate, Space toggle, Enter confirm)",
        qmark="",
    ).ask()

    if selected is None:
        return None

    custom_text = None
    if OTHER_OPTION in selected:
        selected.remove(OTHER_OPTION)
        custom_text = questionary.text(
            "Your answer:",
            style=style,
        ).ask()
        if custom_text:
            selected.append(custom_text)

    return {
        "id": q.id,
        "persona": q.persona,
        "question": q.question,
        "selected": selected,
        "custom": bool(custom_text),
    }


def _format_short_answer(answer: dict) -> str:
    """Format answer for the confirmation line shown after selection."""
    selected = answer["selected"]
    if not selected:
        return "(no selection)"
    if len(selected) == 1:
        text = selected[0]
    else:
        text = " | ".join(selected)
    if len(text) > 80:
        text = text[:77] + "..."
    return text


def _save_answers(case_path: Path, answers: list[dict], round_num: int) -> None:
    """Save answers as JSON and append formatted text to transcript."""
    internal = _get_internal_dir(case_path)

    # Save structured JSON
    afile = internal / "answers.json"
    afile.write_text(json.dumps({
        "round": round_num,
        "answers": answers,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    # Append formatted answers to interrogation transcript
    from . import case as cm
    formatted = format_answers_for_transcript(answers)
    cm.append_to_transcript(case_path, f"### User Response\n\n{formatted}")


def format_answers_for_transcript(answers: list[dict]) -> str:
    """Format answers as markdown for the interrogation transcript."""
    lines = []
    for a in answers:
        selected = a["selected"]
        if not selected:
            answer_text = "(skipped)"
        elif len(selected) == 1:
            answer_text = selected[0]
        else:
            answer_text = " | ".join(selected)
        lines.append(f"{a['id']}. **[{a['persona']}]** {a['question']}\n   -> {answer_text}")
    return "\n\n".join(lines)
