import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

import { defineConfig } from "vitest/config";

import { loadLiveProjectSnapshot, resolveRevealTarget } from "./tools/liveProjectSnapshot";
import { resolveManifestPath } from "./tools/resolveManifestPath";

const projectDir = resolve(fileURLToPath(new URL(".", import.meta.url)));
const manifestPath = resolveManifestPath(projectDir, process.env);

export default defineConfig({
  server: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    fs: {
      allow: [projectDir, resolve(projectDir, "../../--testcode/prj-codev-viewer")]
    }
  },
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true
  },
  plugins: [
    {
      name: "codev-viewer-live-project-state",
      configureServer(server) {
        server.middlewares.use("/api/dashboard/live-state", (_request, response) => {
          if (!existsSync(manifestPath)) {
            response.statusCode = 404;
            response.setHeader("Content-Type", "application/json");
            response.end(JSON.stringify({ message: "project manifest was not found" }));
            return;
          }

          try {
            const snapshot = loadLiveProjectSnapshot(manifestPath);
            response.statusCode = 200;
            response.setHeader("Content-Type", "application/json");
            response.end(JSON.stringify(snapshot));
          } catch (error) {
            response.statusCode = 500;
            response.setHeader("Content-Type", "application/json");
            response.end(
              JSON.stringify({
                message: error instanceof Error ? error.message : "live project snapshot failed"
              })
            );
          }
        });

        server.middlewares.use("/api/dashboard/reveal", (request, response) => {
          if (!existsSync(manifestPath)) {
            response.statusCode = 404;
            response.setHeader("Content-Type", "application/json");
            response.end(JSON.stringify({ message: "project manifest was not found" }));
            return;
          }

          try {
            const requestUrl = new URL(request.url ?? "", "http://localhost");
            const profileId = requestUrl.searchParams.get("profile");
            const relativePath = requestUrl.searchParams.get("path");

            if (!profileId || !relativePath) {
              response.statusCode = 400;
              response.setHeader("Content-Type", "application/json");
              response.end(JSON.stringify({ message: "profile and path are required" }));
              return;
            }

            const target = resolveRevealTarget(manifestPath, profileId, relativePath);
            revealInExplorer(target.absolutePath, target.kind);
            response.statusCode = 200;
            response.setHeader("Content-Type", "application/json");
            response.end(JSON.stringify({ ok: true }));
          } catch (error) {
            response.statusCode = 500;
            response.setHeader("Content-Type", "application/json");
            response.end(
              JSON.stringify({
                message: error instanceof Error ? error.message : "reveal failed"
              })
            );
          }
        });
      }
    }
  ],
  test: {
    dir: resolve(projectDir, "../../--testcode/prj-codev-viewer/tests"),
    environment: "jsdom",
    include: ["**/*.test.ts"],
    coverage: {
      reporter: ["text", "html"]
    }
  }
});

function revealInExplorer(absolutePath: string, kind: "file" | "directory"): void {
  const command =
    kind === "file"
      ? ["-NoProfile", "-Command", `explorer.exe /select,"${absolutePath}"`]
      : ["-NoProfile", "-Command", `explorer.exe "${absolutePath}"`];
  const result = spawnSync("powershell", command, { stdio: "pipe" });

  if (result.status !== 0) {
    throw new Error(result.stderr.toString("utf8").trim() || "Explorer reveal failed");
  }
}
