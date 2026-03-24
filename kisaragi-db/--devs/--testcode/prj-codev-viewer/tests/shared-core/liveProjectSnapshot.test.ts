// @vitest-environment node

import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import {
  loadLiveProjectSnapshot,
  resolveRevealTarget
} from "../../../../--products/prj-codev-viewer/tools/liveProjectSnapshot";

const tempRoots: string[] = [];

afterEach(() => {
  for (const root of tempRoots.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

describe("liveProjectSnapshot", () => {
  it("reads documents from multiple source profiles", () => {
    const { manifestPath } = createProjectFixture();

    const snapshot = loadLiveProjectSnapshot(manifestPath);

    expect(snapshot.profiles.map((profile) => profile.profileId)).toEqual(["codev-db", "codev-view"]);
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain(
      "--docs/--artifact/prj-codev-viewer"
    );
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain(
      "--docs/--artifact/prj-codev-viewer/north_star.md"
    );
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("prj-codev-viewer");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain(
      "prj-codev-viewer/README.md"
    );
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain(
      "prj-codev-viewer/.env"
    );
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain(
      "prj-codev-viewer/index.ts"
    );
  });

  it("adds profile metadata to collected documents", () => {
    const { manifestPath } = createProjectFixture();

    const snapshot = loadLiveProjectSnapshot(manifestPath);
    const document = snapshot.profiles[0]?.documents[0];

    expect(document?.profileId).toBe("codev-db");
    expect(document?.profileLabel).toBe("codev-db basis");
    expect(snapshot.profiles[0]?.documents.some((entry) => entry.nodeKind === "directory")).toBe(true);
    expect(snapshot.profiles[0]?.documents.find((entry) => entry.path.endsWith("north_star.md"))?.title).toBe("North Star");
  });

  it("resolves reveal target inside configured roots", () => {
    const { manifestPath } = createProjectFixture();

    const target = resolveRevealTarget(
      manifestPath,
      "codev-view",
      "prj-codev-viewer/README.md"
    );

    expect(target.kind).toBe("file");
    expect(target.relativePath).toBe("prj-codev-viewer/README.md");
  });

  it("rejects reveal target outside configured roots", () => {
    const { manifestPath } = createProjectFixture();

    expect(() =>
      resolveRevealTarget(manifestPath, "codev-view", "outside/secret.md")
    ).toThrow("outside configured roots");
  });
});

function createProjectFixture(): { manifestPath: string } {
  const root = mkdtempSync(join(tmpdir(), "codev-viewer-live-read-"));
  tempRoots.push(root);

  mkdirSync(join(root, "codev-db", "--docs", "--artifact", "prj-codev-viewer"), { recursive: true });
  mkdirSync(join(root, "codev-db", "--process", "--state", "prj-codev-viewer"), { recursive: true });
  mkdirSync(join(root, "codev-view", "prj-codev-viewer"), { recursive: true });
  mkdirSync(join(root, "codev-view", "prj-isensorium"), { recursive: true });
  mkdirSync(join(root, "codev-view", "outside"), { recursive: true });

  writeFileSync(
    join(root, "codev-db", "--docs", "--artifact", "prj-codev-viewer", "north_star.md"),
    "# North Star\nBody\n",
    "utf8"
  );
  writeFileSync(
    join(root, "codev-db", "--process", "--state", "prj-codev-viewer", "current_state.md"),
    "# Current State\nBody\n",
    "utf8"
  );
  writeFileSync(join(root, "codev-view", "prj-codev-viewer", "README.md"), "# View\nBody\n", "utf8");
  writeFileSync(join(root, "codev-view", "prj-codev-viewer", ".env"), "API_KEY=test\n", "utf8");
  writeFileSync(join(root, "codev-view", "prj-codev-viewer", "index.ts"), "export const x = 1;\n", "utf8");
  writeFileSync(
    join(root, "codev-view", "prj-isensorium", "README.md"),
    "# Sensorium\nBody\n",
    "utf8"
  );
  writeFileSync(join(root, "codev-view", "outside", "secret.md"), "# Secret\n", "utf8");

  const manifestPath = join(root, "project-manifest.json");
  writeFileSync(
    manifestPath,
    JSON.stringify(
      {
        projectId: "prj-codev-viewer",
        sourceProfiles: [
          {
            profileId: "codev-db",
            label: "codev-db basis",
            projectRoot: join(root, "codev-db"),
            documentRoots: ["--docs", "--process"],
            compareRoots: ["--docs/--artifact", "--process/--state"]
          },
          {
            profileId: "codev-view",
            label: "codev-view basis",
            projectRoot: join(root, "codev-view"),
            documentRoots: ["."],
            compareRoots: ["prj-codev-viewer", "prj-isensorium"]
          }
        ],
        ignoreGlobs: ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/build/**"],
        readOnly: true
      },
      null,
      2
    ),
    "utf8"
  );

  return { manifestPath };
}
