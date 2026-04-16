# experiment/reporter.py
# Rich-based terminal reporter for red-teaming results.
# Renders a structured summary table after each run.
# Falls back gracefully if Rich isn't installed.

import logging

logger = logging.getLogger(__name__)


def _try_rich():
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich import box
        return Console(), Table, Panel, box
    except ImportError:
        return None, None, None, None


def render_summary(summary: dict, run_id: str = ""):
    """
    Print a formatted summary panel to the terminal.
    Uses Rich if available, falls back to plain print.
    """
    console, Table, Panel, box = _try_rich()

    if console is None:
        # Plain fallback
        print(f"\n=== Run Summary: {run_id} ===")
        for k, v in summary.items():
            if not isinstance(v, dict):
                print(f"  {k}: {v}")
        return

    # Rich version
    table = Table(
        title=f"Sentinel AI — {run_id}",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="dim", width=30)
    table.add_column("Value", justify="right")

    def _fmt(v):
        if isinstance(v, float):
            return f"{v:.4f}"
        return str(v)

    def _color_pct(pct):
        if pct < 10:
            return f"[green]{pct:.1f}%[/green]"
        elif pct < 30:
            return f"[yellow]{pct:.1f}%[/yellow]"
        else:
            return f"[red]{pct:.1f}%[/red]"

    table.add_row("Total prompts", _fmt(summary.get("total_prompts", 0)))
    table.add_row("Valid responses", _fmt(summary.get("valid_responses", 0)))
    table.add_row("Errored", _fmt(summary.get("errored", 0)))
    table.add_row("Unsafe responses", f"[red]{summary.get('unsafe_count', 0)}[/red]")
    table.add_row("% Unsafe", _color_pct(summary.get("pct_unsafe", 0)))
    table.add_row("Avg safety score", _fmt(summary.get("avg_safety_score", 0)))
    table.add_row("Avg helpfulness", _fmt(summary.get("avg_helpfulness", 0)))
    table.add_row("Avg trustworthiness", _fmt(summary.get("avg_trustworthiness", 0)))
    table.add_row("Avg composite alignment", _fmt(summary.get("avg_composite_alignment", 0)))
    table.add_row("Avg latency (s)", _fmt(summary.get("avg_latency_s", 0)))

    console.print(table)

    # Category breakdown
    by_cat = summary.get("by_category", {})
    if by_cat:
        cat_table = Table(title="By Category", box=box.SIMPLE, header_style="bold")
        cat_table.add_column("Category", style="dim")
        cat_table.add_column("Total", justify="right")
        cat_table.add_column("Unsafe", justify="right")
        cat_table.add_column("% Unsafe", justify="right")
        for cat, data in sorted(by_cat.items()):
            cat_table.add_row(
                cat,
                str(data["total"]),
                f"[red]{data['unsafe']}[/red]" if data["unsafe"] else "0",
                _color_pct(data.get("pct_unsafe", 0)),
            )
        console.print(cat_table)


def render_result_list(results: list[dict], max_show: int = 20):
    """Render a paginated table of individual results."""
    console, Table, Panel, box = _try_rich()
    if console is None:
        return

    table = Table(box=box.SIMPLE, header_style="bold")
    table.add_column("Category", style="dim", width=22)
    table.add_column("Sev", width=4, justify="center")
    table.add_column("Safety", justify="right", width=7)
    table.add_column("Composite", justify="right", width=9)
    table.add_column("Status", width=8)
    table.add_column("Prompt snippet", width=40)

    for r in results[:max_show]:
        se = r.get("safety_eval", {})
        ae = r.get("alignment_eval", {})
        is_unsafe = se.get("is_unsafe", False)
        status = "[red]UNSAFE[/red]" if is_unsafe else "[green]safe[/green]"
        snippet = (r.get("prompt") or "")[:38].replace("\n", " ")
        table.add_row(
            r.get("category", "?"),
            str(r.get("severity", "?")),
            f"{se.get('safety_score', 0):.2f}",
            f"{ae.get('composite_alignment', 0):.2f}",
            status,
            snippet,
        )

    console.print(table)
    if len(results) > max_show:
        console.print(f"  [dim]... and {len(results) - max_show} more[/dim]")
