import * as readline from 'readline';

/**
 * Hook input structure from Claude Code.
 */
interface HookInput {
  tool_input?: {
    command?: string;
  };
}

/**
 * Reads JSON input from stdin and returns it as a string.
 *
 * @returns Promise resolving to the complete stdin content.
 */
async function readStdin(): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false,
  });

  let input = '';
  for await (const line of rl) {
    input += line + '\n';
  }
  return input;
}

/**
 * Main hook logic: validates git commands and blocks dangerous flags.
 *
 * @returns Promise that resolves when hook completes.
 */
async function main(): Promise<void> {
  try {
    const hookInput = await readStdin();
    const inputData = JSON.parse(hookInput) as HookInput;

    const bashCommand =
      (typeof inputData.tool_input?.command === 'string' ? inputData.tool_input.command : null) ??
      '';

    // Check for prohibited git flags
    const prohibitedPattern =
      /git.*(--no-verify|--no-gpg-sign)|git\s+push.*(--force([^-]|$)|-f\s|--force-with-lease)/;

    if (prohibitedPattern.test(bashCommand)) {
      const errorMsg = `BLOCKED: Hook bypass or force flags detected.

Prohibited flags: --no-verify, --no-gpg-sign, --force, -f, --force-with-lease

Instead of bypassing safety checks:
- If pre-commit hook fails: Fix the linting/formatting/type errors it found
- If commit-msg fails: Write a proper conventional commit message
- If pre-push fails: Fix the issues preventing push
- If force push needed: This usually indicates a workflow problem

Fix the root problem rather than bypassing the safety mechanism.
Only use these flags when explicitly requested by the user.
`;

      process.stderr.write(errorMsg);
      process.exit(2); // Exit 2 = blocking error
    }

    process.exit(0); // Allow the command
  } catch (error) {
    process.stderr.write(`Hook error: ${error instanceof Error ? error.message : String(error)}`);
    process.exit(1);
  }
}

main().catch(console.error);
