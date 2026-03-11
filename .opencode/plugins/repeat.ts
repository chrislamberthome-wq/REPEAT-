/**
 * .opencode/plugins/repeat.ts
 *
 * OpenCode plugin for REPEAT governance commands.
 *
 * This plugin registers three commands that invoke deterministic Python
 * verifiers through thin shell wrappers. It MUST NOT interpret, rewrite,
 * or override verifier outputs. All governance outcomes (PASS/FAIL/ERROR)
 * are determined solely by the verifier scripts.
 *
 * OpenCode advisory contract:
 *   - May assist operators in drafting action JSON, explaining failures,
 *     and scaffolding remediation patches.
 *   - Must NOT emit, reinterpret, or override verifier PASS/FAIL/ERROR.
 *   - Must NOT write to receipts/council_ledger.jsonl directly.
 *   - Must treat infrastructure faults (non-zero exit from scripts) as ERROR
 *     without silent downgrade.
 *
 * Commands registered:
 *   repeat.verify_action <path>   — validate a council action JSON file
 *   repeat.verify_receipt <path>  — validate a seat_fill receipt JSON file
 *   repeat.replay_ledger [path]   — replay council ledger, emit final state
 */

import { spawnSync } from "child_process";
import * as path from "path";

interface CommandResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

/**
 * Execute a shell script with a file path argument.
 * Uses spawnSync with an explicit array of arguments to prevent
 * shell interpolation of user-supplied paths.
 */
function runScript(script: string, args: string[]): CommandResult {
  const result = spawnSync("bash", [script, ...args], {
    encoding: "utf-8",
    stdio: ["ignore", "pipe", "pipe"],
  });

  const exitCode =
    result.status !== null && result.status !== undefined
      ? result.status
      : 2; // treat spawn failure as ERROR

  return {
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
    exitCode,
  };
}

/**
 * Format a verifier result for operator display.
 * Preserves raw output; appends remediation hint only on FAIL/ERROR.
 */
function formatResult(res: CommandResult, commandName: string): string {
  const lines: string[] = [];

  if (res.stdout.trim()) {
    lines.push(res.stdout.trim());
  }

  if (res.stderr.trim()) {
    lines.push(res.stderr.trim());
  }

  if (res.exitCode === 0) {
    return lines.join("\n");
  }

  // Advisory note: OpenCode may suggest remediation but must not alter
  // authoritative outcomes. The note is clearly labelled as advisory.
  const level = res.exitCode === 2 ? "ERROR" : "FAIL";
  lines.push(
    `\n[ADVISORY] ${commandName} exited with ${level} (exit code ${res.exitCode}).` +
      "\nReview the verifier output above. OpenCode can help draft a corrected " +
      "action or receipt, but the verifier result is authoritative and cannot " +
      "be overridden by this plugin."
  );

  return lines.join("\n");
}

export function activate(context: { registerCommand: Function }): void {
  /**
   * repeat.verify_action <path>
   *
   * Validates a council action JSON file using repeat_verifier.py.
   * Emits deterministic PASS/FAIL/ERROR output unchanged.
   */
  context.registerCommand(
    "repeat.verify_action",
    async (actionPath: string): Promise<string> => {
      if (!actionPath) {
        return "ERROR: repeat.verify_action requires a file path argument.";
      }
      const scriptPath = path.join("tools", "repeat_verify_action.sh");
      const res = runScript(scriptPath, [actionPath]);
      return formatResult(res, "repeat.verify_action");
    }
  );

  /**
   * repeat.verify_receipt <path>
   *
   * Validates a seat_fill receipt JSON file using repeat_verifier.py.
   * Emits deterministic PASS/FAIL/ERROR output unchanged.
   */
  context.registerCommand(
    "repeat.verify_receipt",
    async (receiptPath: string): Promise<string> => {
      if (!receiptPath) {
        return "ERROR: repeat.verify_receipt requires a file path argument.";
      }
      const scriptPath = path.join("tools", "repeat_verify_receipt.sh");
      const res = runScript(scriptPath, [receiptPath]);
      return formatResult(res, "repeat.verify_receipt");
    }
  );

  /**
   * repeat.replay_ledger [path]
   *
   * Replays the council ledger via replay_ledger_engine.py.
   * Emits final council state as JSON on PASS.
   * Defaults to receipts/council_ledger.jsonl if no path is provided.
   */
  context.registerCommand(
    "repeat.replay_ledger",
    async (ledgerPath?: string): Promise<string> => {
      const scriptPath = path.join("tools", "repeat_replay_ledger.sh");
      const args = ledgerPath ? [ledgerPath] : [];
      const res = runScript(scriptPath, args);
      return formatResult(res, "repeat.replay_ledger");
    }
  );
}
