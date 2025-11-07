#!/usr/bin/env python3
"""
Manual Aerich migration format fix script.
Run this script once to fix old-format migration files.
"""


import os
import subprocess
import sys


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {description}:")
        print(e.stderr)
        return False


def main():
    """Main function to fix Aerich migrations."""
    print("Attempting to fix Aerich migration format...")

    # Change to project directory
    os.chdir("/app")

    # Check if aerich is installed
    if not run_command(
        "command -v aerich", "Checking if aerich is available"
    ):
        print("Installing aerich...")
        if not run_command("pip install aerich", "Installing aerich"):
            print("Failed to install aerich")
            return False

    # Try the fix-migrations command
    print("\nAttempting to fix migration formats...")
    success = run_command(
        "aerich fix-migrations", "Running aerich fix-migrations"
    )

    if not success:
        print("fix-migrations failed, trying alternative approach...")

        # Check what version we have and try other approaches
        result = subprocess.run(
            ["aerich", "--version"], capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Aerich version: {result.stdout.strip()}")
        else:
            print("Could not determine Aerich version")

        # Try to run aerich upgrade which might fix the issue
        print("\nTrying aerich upgrade...")
        success = run_command("aerich upgrade", "Running aerich upgrade")

    if success:
        print("\nMigration format fixing completed successfully!")
        return True
    else:
        print("\nMigration format fixing failed. Please check logs above.")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
