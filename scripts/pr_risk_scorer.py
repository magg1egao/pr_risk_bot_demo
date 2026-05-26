import json
import os
import subprocess
from pathlib import Path


RISKY_PATH_KEYWORDS = [
    "auth",
    "payment",
    "security",
    "permission",
    "config",
    "deploy",
    "database",
    "migration",
]


TEST_PATH_KEYWORDS = [
    "test",
    "tests",
    "spec",
]


def run_command(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_changed_files() -> list[str]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if event_path and Path(event_path).exists():
        with open(event_path, "r", encoding="utf-8") as file:
            event = json.load(file)

        base_sha = event["pull_request"]["base"]["sha"]
        head_sha = event["pull_request"]["head"]["sha"]

        output = run_command(["git", "diff", "--name-only", base_sha, head_sha])
        return [line for line in output.splitlines() if line.strip()]

    output = run_command(["git", "diff", "--name-only", "HEAD~1", "HEAD"])
    return [line for line in output.splitlines() if line.strip()]


def get_diff_stat() -> tuple[int, int]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")

    if event_path and Path(event_path).exists():
        with open(event_path, "r", encoding="utf-8") as file:
            event = json.load(file)

        base_sha = event["pull_request"]["base"]["sha"]
        head_sha = event["pull_request"]["head"]["sha"]

        output = run_command(["git", "diff", "--numstat", base_sha, head_sha])
    else:
        output = run_command(["git", "diff", "--numstat", "HEAD~1", "HEAD"])

    additions = 0
    deletions = 0

    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue

        added, deleted, _ = parts

        if added.isdigit():
            additions += int(added)
        if deleted.isdigit():
            deletions += int(deleted)

    return additions, deletions


def is_test_file(path: str) -> bool:
    lower_path = path.lower()
    return any(keyword in lower_path for keyword in TEST_PATH_KEYWORDS)


def is_risky_file(path: str) -> bool:
    lower_path = path.lower()
    return any(keyword in lower_path for keyword in RISKY_PATH_KEYWORDS)


def calculate_risk_score(
    changed_files: list[str],
    additions: int,
    deletions: int,
) -> tuple[int, list[str]]:
    score = 0
    signals = []

    total_lines_changed = additions + deletions
    test_files_changed = [path for path in changed_files if is_test_file(path)]
    risky_files_changed = [path for path in changed_files if is_risky_file(path)]

    if len(changed_files) >= 5:
        score += 20
        signals.append(f"Large file spread: {len(changed_files)} files changed.")

    if total_lines_changed >= 300:
        score += 25
        signals.append(f"Large change size: {total_lines_changed} lines modified.")
    elif total_lines_changed >= 100:
        score += 15
        signals.append(f"Moderate change size: {total_lines_changed} lines modified.")

    if not test_files_changed:
        score += 25
        signals.append("No test files were changed.")

    if risky_files_changed:
        score += 25
        risky_list = ", ".join(f"`{path}`" for path in risky_files_changed[:5])
        signals.append(f"Risk-sensitive files changed: {risky_list}.")

    score = min(score, 100)

    if not signals:
        signals.append("No major risk signals detected.")

    return score, signals


def get_risk_level(score: int) -> str:
    if score >= 70:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def build_comment() -> str:
    changed_files = get_changed_files()
    additions, deletions = get_diff_stat()

    score, signals = calculate_risk_score(
        changed_files=changed_files,
        additions=additions,
        deletions=deletions,
    )

    risk_level = get_risk_level(score)

    files_display = "\n".join(f"- `{path}`" for path in changed_files[:15])
    if len(changed_files) > 15:
        files_display += f"\n- ...and {len(changed_files) - 15} more"

    signals_display = "\n".join(f"- {signal}" for signal in signals)

    return f"""## PR Quality Signal: {risk_level}

**Risk score:** {score}/100

### Summary

- Files changed: **{len(changed_files)}**
- Lines added: **{additions}**
- Lines deleted: **{deletions}**

### Signals

{signals_display}

### Changed files

{files_display if files_display else "- No changed files detected."}

### Suggested reviewer action

Use this as an advisory signal, not a merge blocker. If risk is medium or high, consider checking whether the PR has enough tests and whether the changed files are historically sensitive areas.
"""


def main() -> None:
    print(build_comment())


if __name__ == "__main__":
    main()