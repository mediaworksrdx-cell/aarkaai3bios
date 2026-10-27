import { safeExec } from './safe_exec.ts';

export interface AllowedBinarySpec {
  binary: string;
  allowedSubcommands?: RegExp;
  blockedFlags?: RegExp;
}

export class AllowlistExecutionHarness {
  private static readonly ALLOWED_BINARIES: Map<string, AllowedBinarySpec> = new Map([
    [
      'npx',
      {
        binary: 'npx',
        allowedSubcommands: /^(tsc|vitest|eslint|prettier|tsx)$/
      }
    ],
    [
      'node',
      {
        binary: 'node',
        allowedSubcommands: /^(\-v|\-\-version|\-\-test|.+\.(mjs|js|ts))$/
      }
    ],
    [
      'git',
      {
        binary: 'git',
        allowedSubcommands: /^(status|diff|log|add|commit|rev-parse|branch)$/
      }
    ],
    [
      'cargo',
      {
        binary: 'cargo',
        allowedSubcommands: /^(check|test|build|bench|--version)$/
      }
    ]
  ]);

  public static async execute(
    binary: string,
    args: string[],
    cwd: string = process.cwd()
  ) {
    const spec = this.ALLOWED_BINARIES.get(binary);
    if (!spec) {
      throw new Error(`SECURITY ALERT: Binary '${binary}' is not on the execution allowlist.`);
    }

    if (args.length > 0 && spec.allowedSubcommands) {
      const primaryArg = args[0];
      if (!spec.allowedSubcommands.test(primaryArg)) {
        throw new Error(
          `SECURITY ALERT: Subcommand '${primaryArg}' is rejected for binary '${binary}'.`
        );
      }
    }

    const crawlingRegex = /^(-R|--recursive|\/s)$/i;
    for (const arg of args) {
      if (crawlingRegex.test(arg)) {
        throw new Error(`RULE 8 VIOLATION: Recursive discovery argument '${arg}' is prohibited.`);
      }
      if (/[\;&\|`\$\<\>]/.test(arg)) {
        throw new Error(`SECURITY ALERT: Shell metacharacter detected in argument: '${arg}'`);
      }
    }

    return await safeExec(binary, args, { cwd });
  }

  public static isBinaryAllowed(binary: string): boolean {
    return this.ALLOWED_BINARIES.has(binary);
  }
}
