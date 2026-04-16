# utils/formatting.py — console output helpers
# sab modules mein prints consistent rakhne ke liye
# Rich pull karne ki zaroorat nahi basic formatting ke liye — woh sirf experiment/reporter.py mein use hota hai

RESET  = "\033[0m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
DIM    = "\033[2m"


def color_score(score: float) -> str:
    # 0-1 score ko colored string mein convert karo terminal output ke liye
    s = f"{score:.2f}"
    if score >= 0.75:
        return f"{GREEN}{s}{RESET}"
    elif score >= 0.4:
        return f"{YELLOW}{s}{RESET}"
    else:
        return f"{RED}{s}{RESET}"


def print_banner(title: str, width: int = 55):
    # simple section banner print karo
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_result_row(result: dict):
    # ek evaluated result ka one-line summary print karo
    # Format: [UNSAFE/safe ] [category            ] safety=0.xx composite=0.xx
    safety    = result.get("safety_eval",    {}).get("safety_score", 0)
    composite = result.get("alignment_eval", {}).get("composite_alignment", 0)
    is_unsafe = result.get("safety_eval",    {}).get("is_unsafe", False)
    cat       = result.get("category", "unknown")
    error     = result.get("error")

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
    # percentage ko color-coded string mein format karo
    s = f"{value:.1f}%"
    if value < 10:
        return f"{GREEN}{s}{RESET}"
    elif value < 30:
        return f"{YELLOW}{s}{RESET}"
    else:
        return f"{RED}{s}{RESET}"


def hr(width: int = 55, char: str = "-"):
    # horizontal rule print karo — section separators ke liye
    print(char * width)
