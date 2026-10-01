import { spawn } from "node:child_process";
import { constants } from "node:os";

/** Update the documented global npm installation, leaving project sync explicit. */
export function update(): Promise<number> {
  console.log("Updating Agent Manifesto Kit: npm install --global agent-manifesto-kit@latest");
  // Windows npm is a .cmd shim. All shell arguments are fixed literals, never user input.
  const child = spawn("npm", ["install", "--global", "agent-manifesto-kit@latest"], {
    stdio: "inherit",
    shell: process.platform === "win32",
  });

  return new Promise((resolve) => {
    let launchFailed = false;
    child.once("error", (error) => {
      launchFailed = true;
      console.error(`update: could not start npm: ${error.message}`);
      console.error("Make sure Node.js and npm are installed and npm is available on PATH.");
      resolve(1);
    });
    child.once("close", (code, signal) => {
      if (launchFailed) return;
      if (signal) {
        console.error(`update: npm was interrupted by ${signal}.`);
        resolve(128 + (constants.signals[signal] ?? 1));
      } else if (code !== 0) {
        console.error(`update: npm failed (exit code ${code ?? "unknown"}). See its output above.`);
        resolve(code ?? 1);
      } else {
        console.log('Update completed. Run "agentkit --version" to check the installed version.');
        resolve(0);
      }
    });
  });
}
