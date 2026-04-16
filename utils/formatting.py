# utils/formatting.py
# Console output helpers. Keep prints consistent across modules.
# Avoids pulling in Rich just for basic formatting — Rich is only used
# in experiment/reporter.py where it's worth it.

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"


def color_score(score: float) -> str:
    """Return a colored string for a 0-1 score."""
    s = f"{score:.2f}"
    if score >= 0.75:
        return f"{GREEN}{s}{RESET}"
    elif score >= 0.4:
        return f"{YELLOW}{s}{RESET}"
    else:
        return f"{RED}{s}{RESET}"


def print_banner(title: str, width: int = 55):
    """Print a simple section banner."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_result_row(result: dict):
    """
    Print a one-line summary for a single evaluated result.
    Format: [UNSAFE/safe ] [category            ] safety=0.xx composite=0.xx
    """
    safety = result.get("safety_eval", {}).get("safety_score", 0)
    composite = result.get("alignment_eval", {}).get("composite_alignment", 0)
    is_unsafe = result.get("safety_eval", {}).get("is_unsafe", False)
    cat = result.get("category", "unknown")
    error = result.get("error")

    if error:
        status = f"{DIM}[error ]{RESET}"
    elif is_unsafe:
        status = f"{RED}[UNSAFE]{RESET}"
    else:
        status = f"{GREEN}[safe  ]{RESET}"

    print(
        f"  {status} [{cat:<22}] "
        f"safety={color_score(safety)} composite={color_score(composite)}"
    )


def format_pct(value: float) -> str:
    """Format a percentage with color coding."""
    s = f"{value:.1f}%"
    if value < 10:
        return f"{GREEN}{s}{RESET}"
    elif value < 30:
        return f"{YELLOW}{s}{RESET}"
    else:
        return f"{RED}{s}{RESET}"


def hr(width: int = 55, char: str = "-"):
    """Print a horizontal rule."""
    print(char * width)
