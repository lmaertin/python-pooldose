"""Example usage of new CLI features for JSON extraction and output saving."""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and print the results."""
    print(f"\n{'=' * 60}")
    print(f"Example: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('=' * 60)
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        print("✓ Success")
        if result.stdout:
            print(result.stdout[:500])  # Print first 500 chars
    else:
        print("✗ Failed")
        if result.stderr:
            print(result.stderr[:500])


def main():
    """Demonstrate new CLI features."""
    print("=" * 60)
    print("Python PoolDose - New CLI Features Examples")
    print("=" * 60)

    # Example 1: Show help
    run_command(
        [sys.executable, "-m", "pooldose", "--help"],
        "Show help with new options"
    )

    # Example 2: Extract JSON (will fail without real device)
    print("\n" + "=" * 60)
    print("Note: The following commands require a real device")
    print("Replace '192.168.1.100' with your device IP")
    print("=" * 60)

    examples = [
        "# Extract JSON from device (default file: instantvalues.json)",
        "python -m pooldose --host 192.168.1.100 --extract-json",
        "",
        "# Extract JSON to custom file",
        "python -m pooldose --host 192.168.1.100 --extract-json -o mydata.json",
        "",
        "# Extract with HTTPS",
        "python -m pooldose --host 192.168.1.100 --ssl --extract-json",
        "",
        "# Save analysis output to file",
        "python -m pooldose --host 192.168.1.100 --analyze -o analysis.json",
        "",
        "# Save normal connection output to file",
        "python -m pooldose --host 192.168.1.100 -o output.json",
        "",
        "# Save mock mode output to file",
        "python -m pooldose --mock data.json -o results.json",
    ]

    for line in examples:
        print(line)

    print("\n" + "=" * 60)
    print("For more information, see README.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
