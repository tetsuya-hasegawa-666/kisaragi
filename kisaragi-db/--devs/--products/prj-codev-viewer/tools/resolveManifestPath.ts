import { resolve } from "node:path";

export function resolveManifestPath(projectDir: string, environment: NodeJS.ProcessEnv): string {
  const explicitPath = environment.CODEV_VIEWER_MANIFEST_PATH?.trim();

  if (explicitPath) {
    return resolve(explicitPath);
  }

  return resolve(projectDir, "config", "project-manifest.json");
}
