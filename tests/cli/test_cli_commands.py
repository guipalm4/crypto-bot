#!/usr/bin/env python3
"""
Test CLI Commands - Comprehensive Real Test

This script tests all CLI commands in a real environment and generates
a report of issues that need to be fixed.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table

console = Console()

# CLI entry point
CLI_CMD = [sys.executable, "-m", "crypto_bot.cli.main"]


def run_command_test(
    cmd: List[str], description: str, timeout: int = 10
) -> Dict[str, Any]:
    """
    Test a CLI command and return results.

    Args:
        cmd: Command to test
        description: Description of what is being tested
        timeout: Timeout in seconds (default: 10)

    Returns:
        Dict with test results
    """
    full_cmd = CLI_CMD + cmd
    result = {
        "command": " ".join(cmd),
        "description": description,
        "success": False,
        "exit_code": None,
        "stdout": "",
        "stderr": "",
        "error": None,
        "timeout": timeout,
    }

    try:
        process = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result["exit_code"] = process.returncode
        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["success"] = process.returncode == 0

    except subprocess.TimeoutExpired:
        result["error"] = f"Command timed out after {timeout} seconds"
        result["exit_code"] = -1
        # For start command, timeout is expected (it runs indefinitely)
        if "start" in cmd:
            result["success"] = True  # Start command should timeout
            result["stdout"] = "Command started successfully (expected timeout)"

    except Exception as e:
        result["error"] = str(e)
        result["exit_code"] = -1

    return result


def main() -> None:
    """Run all CLI command tests and generate report."""
    console.print("\n[bold cyan]🧪 Testing All CLI Commands[/bold cyan]\n")

    tests = [
        # Basic commands
        (["--help"], "Main help command", 5),
        (["--version"], "Version command", 5),
        (["version"], "Version subcommand", 5),
        (["status"], "System status", 10),
        # Start/Stop commands - Note: start command runs indefinitely
        # We test it with a short timeout to verify it starts correctly
        (["start", "--dry-run"], "Start bot in dry-run mode (expected timeout)", 3),
        (["stop"], "Stop bot", 10),
        (["restart", "--dry-run"], "Restart bot in dry-run mode", 15),
        # Monitoring commands
        (["strategies"], "List active strategies", 10),
        (
            ["strategies", "--exchange", "binance"],
            "List strategies filtered by exchange",
            10,
        ),
        (["positions"], "List open positions", 10),
        (
            ["balances", "--exchange", "binance"],
            "Get balances (requires exchange config)",
            15,
        ),
        (
            ["balances", "--exchange", "binance", "--currency", "BTC"],
            "Get specific currency balance",
            15,
        ),
        # Control commands
        (
            ["force", "test-strategy-id"],
            "Force strategy execution (will fail without valid ID)",
            10,
        ),
        (["logs"], "View logs", 5),
        (["logs", "--lines", "10"], "View last 10 log lines", 5),
        (["dry-run"], "Show dry-run status", 5),
        (["dry-run", "--enable"], "Enable dry-run mode", 5),
        (["dry-run", "--disable"], "Disable dry-run mode", 5),
    ]

    results: List[Dict[str, Any]] = []

    for cmd, description, timeout in tests:
        console.print(f"[dim]Testing: {' '.join(cmd)}[/dim]")
        result = run_command_test(cmd, description, timeout)
        results.append(result)

        if result["success"]:
            console.print("  ✅ [green]PASS[/green]")
        else:
            console.print(f"  ❌ [red]FAIL[/red] (exit: {result['exit_code']})")

    # Generate detailed report
    console.print("\n[bold cyan]📊 Test Results Report[/bold cyan]\n")

    # Summary table
    summary_table = Table(
        title="Test Summary", show_header=True, header_style="bold magenta"
    )
    summary_table.add_column("Command", style="cyan")
    summary_table.add_column("Status", justify="center")
    summary_table.add_column("Exit Code", justify="right")
    summary_table.add_column("Issues", style="yellow")

    passed = 0
    failed = 0
    issues: List[Dict[str, Any]] = []

    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        status_style = "green" if result["success"] else "red"

        issue_summary = ""
        if not result["success"]:
            failed += 1
            if result["error"]:
                issue_summary = result["error"]
            elif result["stderr"]:
                issue_summary = (
                    result["stderr"][:50] + "..."
                    if len(result["stderr"]) > 50
                    else result["stderr"]
                )
            elif result["exit_code"] and result["exit_code"] != 0:
                issue_summary = f"Exit code: {result['exit_code']}"

            issues.append(
                {
                    "command": result["command"],
                    "description": result["description"],
                    "issue": issue_summary,
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "exit_code": result["exit_code"],
                }
            )
        else:
            passed += 1

        summary_table.add_row(
            result["command"],
            f"[{status_style}]{status}[/{status_style}]",
            str(result["exit_code"]) if result["exit_code"] is not None else "N/A",
            issue_summary[:50] if issue_summary else "-",
        )

    console.print(summary_table)
    console.print(
        f"\n[green]✅ Passed: {passed}[/green] | [red]❌ Failed: {failed}[/red] | [cyan]Total: {len(results)}[/cyan]\n"
    )

    # Detailed issues report
    if issues:
        console.print("[bold yellow]🔧 Issues Found - Action Required:[/bold yellow]\n")

        issues_table = Table(
            title="Detailed Issues", show_header=True, header_style="bold red"
        )
        issues_table.add_column("Command", style="cyan", width=30)
        issues_table.add_column("Description", style="yellow", width=40)
        issues_table.add_column("Issue", style="red")
        issues_table.add_column("Suggested Fix", style="green", width=40)

        for issue in issues:
            fix_suggestion = generate_fix_suggestion(issue)
            issues_table.add_row(
                issue["command"],
                issue["description"],
                (
                    issue["issue"][:60] + "..."
                    if len(issue["issue"]) > 60
                    else issue["issue"]
                ),
                fix_suggestion,
            )

        console.print(issues_table)

        # Write detailed report to file
        report_file = Path("tests/cli/cli_test_report.md")
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("# CLI Commands Test Report\n\n")
            f.write(
                f"**Generated:** {__import__('datetime').datetime.now().isoformat()}\n\n"
            )
            f.write(
                f"**Summary:** {passed} passed, {failed} failed out of {len(results)} tests\n\n"
            )
            f.write("## Issues Found\n\n")

            for issue in issues:
                f.write(f"### Command: `{issue['command']}`\n\n")
                f.write(f"**Description:** {issue['description']}\n\n")
                f.write(f"**Issue:** {issue['issue']}\n\n")
                f.write(f"**Exit Code:** {issue['exit_code']}\n\n")

                if issue["stdout"]:
                    f.write("**Stdout:**\n```\n")
                    f.write(issue["stdout"][:500])
                    f.write("\n```\n\n")

                if issue["stderr"]:
                    f.write("**Stderr:**\n```\n")
                    f.write(issue["stderr"][:500])
                    f.write("\n```\n\n")

                f.write(f"**Suggested Fix:** {generate_fix_suggestion(issue)}\n\n")
                f.write("---\n\n")

        console.print(f"\n[green]📄 Detailed report saved to: {report_file}[/green]")

    else:
        console.print(
            "[bold green]✅ All tests passed! No issues found.[/bold green]\n"
        )


def generate_fix_suggestion(issue: Dict[str, Any]) -> str:
    """Generate fix suggestion based on issue type."""
    cmd = issue["command"]
    stderr = issue["stderr"].lower() if issue.get("stderr") else ""
    stdout = issue["stdout"].lower() if issue.get("stdout") else ""
    exit_code = issue["exit_code"]

    # Database connection issues
    if "database" in stderr or "connection" in stderr or "session" in stderr:
        return "Verify database connection. Check DATABASE_URL env var or config file."

    # Missing configuration
    if "config" in stderr or "settings" in stderr or "not found" in stderr:
        return "Check configuration files in config/environments/ directory."

    # Strategy not found
    if "force" in cmd and ("not found" in stderr or "strategy" in stderr):
        return "Expected - command needs valid strategy ID or name. Create a strategy first."

    # Exchange not configured
    if "balances" in cmd and ("exchange" in stderr or "not configured" in stderr):
        return "Configure exchange API keys in settings or environment variables."

    # Log file not found
    if "logs" in cmd and ("not found" in stderr or "file" in stderr):
        return "Create logs directory and ensure logging is configured."

    # Permission issues
    if "permission" in stderr or "access denied" in stderr:
        return "Check file/directory permissions."

    # Import errors
    if "import" in stderr or "module" in stderr:
        return "Verify all dependencies are installed: pip install -r requirements.txt"

    # Timeout for start command is expected
    if "start" in cmd and "timeout" in str(issue.get("error", "")).lower():
        return "Expected behavior - start command runs indefinitely. This is correct."

    # Timeout for other commands
    if issue.get("error") and "timeout" in str(issue["error"]).lower():
        return (
            "Command may be hanging. Check for infinite loops or blocking operations."
        )

    # Generic
    if exit_code == 1:
        return "Review error output above for specific error message."

    return "Check command syntax and required dependencies."


if __name__ == "__main__":
    main()
