"""
Run the full test suite (lightweight) for this repository.

Usage:
    python test/run_full_tests.py

This script will invoke `pytest` to run the created tests.
"""
import subprocess
import sys


def main():
    cmd = [sys.executable, "-m", "pytest", "-q", "test/backend_tests.py", "test/frontend_simulation.py", "test/db_tests.py"]
    print("Running tests:", " ".join(cmd))
    proc = subprocess.run(cmd)
    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()
