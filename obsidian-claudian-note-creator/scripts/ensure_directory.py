#!/usr/bin/env python3
"""
Script to ensure the target directory exists.
This script checks if 'fleeting notes/from-claudian' directory exists,
and creates it if it doesn't.
"""

import os
import sys

def ensure_directory(vault_path):
    """Ensure the target directory exists in the Obsidian vault."""
    target_dir = os.path.join(vault_path, "fleeting notes", "from-claudian")

    if not os.path.exists(target_dir):
        print(f"Creating directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
        return True
    else:
        print(f"Directory already exists: {target_dir}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python ensure_directory.py <vault_path>")
        sys.exit(1)

    vault_path = sys.argv[1]
    ensure_directory(vault_path)

if __name__ == "__main__":
    main()