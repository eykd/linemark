#!/usr/bin/env python3
"""Pre-tool-use hook to block dangerous git flags.

This hook validates git commands and blocks flags that bypass safety checks:
- --no-verify: Skips pre-commit and commit-msg hooks
- --no-gpg-sign: Skips GPG signing
- --force/-f: Force push flags
- --force-with-lease: Force push with lease
"""

import json
import re
import sys


def read_stdin() -> str:
    """Read JSON input from stdin.

    Returns:
        Complete stdin content as a string.

    """
    return sys.stdin.read()


def main() -> None:
    """Main hook logic: validates git commands and blocks dangerous flags."""
    try:
        # Read and parse hook input
        hook_input = read_stdin()
        input_data = json.loads(hook_input)

        # Extract bash command from tool input
        bash_command = input_data.get('tool_input', {}).get('command', '')

        # Check for prohibited git flags
        prohibited_pattern = re.compile(
            r'git.*(--no-verify|--no-gpg-sign)|'
            r'git\s+push.*(--force([^-]|$)|-f\s|--force-with-lease)'
        )

        if prohibited_pattern.search(bash_command):
            error_msg = """BLOCKED: Hook bypass or force flags detected.

Prohibited flags: --no-verify, --no-gpg-sign, --force, -f, --force-with-lease

Instead of bypassing safety checks:
- If pre-commit hook fails: Fix the linting/formatting/type errors it found
- If commit-msg fails: Write a proper conventional commit message
- If pre-push fails: Fix the issues preventing push
- If force push needed: This usually indicates a workflow problem

Fix the root problem rather than bypassing the safety mechanism.
Only use these flags when explicitly requested by the user.
"""
            sys.stderr.write(error_msg)
            sys.exit(2)  # Exit 2 = blocking error

        sys.exit(0)  # Allow the command

    except Exception as e:
        sys.stderr.write(f'Hook error: {e}\n')
        sys.exit(1)


if __name__ == '__main__':
    main()
