// @vitest-environment node

import { mkdtempSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, describe, expect, it } from "vitest";

import {
  loadLiveProjectSnapshot,
  resolveRevealTarget
} from "../../../../--products/prj-direview/tools/liveProjectSnapshot";
import { resolveManifestPath } from "../../../../--products/prj-direview/tools/resolveManifestPath";

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
      "--docs/--artifact/prj-direview"
    );
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain(
      "--docs/--artifact/prj-direview/north_star.md"
    );
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("prj-direview");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain(
      "prj-direview/README.md"
    );
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain(
      "prj-direview/.env"
    );
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain(
      "prj-direview/index.ts"
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

  it("reads documents from launcher-generated db-view and prj-view profiles", () => {
    const { manifestPath } = createWorkspaceRootFixture();

    const snapshot = loadLiveProjectSnapshot(manifestPath);

    expect(snapshot.profiles.map((profile) => profile.profileId)).toEqual(["db-view", "prj-view"]);
    expect(snapshot.profiles[0]?.projectRoot.endsWith(rootName(manifestPath))).toBe(false);
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi");
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-db");
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-db/--devs/--plans");
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-tree");
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-ruling");
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi/AGENTS.md");
    expect(snapshot.profiles[0]?.documents.map((document) => document.path)).toContain("kisaragi/.gitignore");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("kisaragi");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-tree");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-tree/prj-direview");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("kisaragi/kisaragi-skills");
    expect(snapshot.profiles[1]?.documents.map((document) => document.path)).toContain("kisaragi/AGENTS.md");
  });

  it("resolves reveal target inside configured roots", () => {
    const { manifestPath } = createProjectFixture();

    const target = resolveRevealTarget(
      manifestPath,
      "codev-view",
      "prj-direview/README.md"
    );

    expect(target.kind).toBe("file");
    expect(target.relativePath).toBe("prj-direview/README.md");
  });

  it("rejects reveal target outside configured roots", () => {
    const { manifestPath } = createProjectFixture();

    expect(() =>
      resolveRevealTarget(manifestPath, "codev-view", "outside/secret.md")
    ).toThrow("outside configured roots");
  });

  it("prefers environment manifest path when provided", () => {
    const resolved = resolveManifestPath("C:/workspace/prj-direview", {
      CODEV_VIEWER_MANIFEST_PATH: "C:/runtime/active-project-manifest.json"
    });

    expect(resolved).toBe(join("C:/runtime", "active-project-manifest.json"));
  });

  it("falls back to the project config manifest path", () => {
    const resolved = resolveManifestPath("C:/workspace/prj-direview", {});

    expect(resolved).toBe(join("C:/workspace/prj-direview", "config", "project-manifest.json"));
  });
});

function createProjectFixture(): { manifestPath: string } {
  const root = mkdtempSync(join(tmpdir(), "direview-live-read-"));
  tempRoots.push(root);

  mkdirSync(join(root, "codev-db", "--docs", "--artifact", "prj-direview"), { recursive: true });
  mkdirSync(join(root, "codev-db", "--process", "--state", "prj-direview"), { recursive: true });
  mkdirSync(join(root, "codev-view", "prj-direview"), { recursive: true });
  mkdirSync(join(root, "codev-view", "prj-isensorium"), { recursive: true });
  mkdirSync(join(root, "codev-view", "outside"), { recursive: true });

  writeFileSync(
    join(root, "codev-db", "--docs", "--artifact", "prj-direview", "north_star.md"),
    "# North Star\nBody\n",
    "utf8"
  );
  writeFileSync(
    join(root, "codev-db", "--process", "--state", "prj-direview", "current_state.md"),
    "# Current State\nBody\n",
    "utf8"
  );
  writeFileSync(join(root, "codev-view", "prj-direview", "README.md"), "# View\nBody\n", "utf8");
  writeFileSync(join(root, "codev-view", "prj-direview", ".env"), "API_KEY=test\n", "utf8");
  writeFileSync(join(root, "codev-view", "prj-direview", "index.ts"), "export const x = 1;\n", "utf8");
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
        projectId: "prj-direview",
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
            compareRoots: ["prj-direview", "prj-isensorium"]
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

function createWorkspaceRootFixture(): { manifestPath: string } {
  const root = mkdtempSync(join(tmpdir(), "direview-workspace-root-"));
  tempRoots.push(root);

  const workspaceRoot = join(root, "kisaragi");
  mkdirSync(join(workspaceRoot, "kisaragi-db", "--devs", "--plans"), { recursive: true });
  mkdirSync(join(workspaceRoot, "kisaragi-ruling"), { recursive: true });
  mkdirSync(join(workspaceRoot, "kisaragi-skills"), { recursive: true });
  mkdirSync(join(workspaceRoot, "kisaragi-tree"), { recursive: true });
  mkdirSync(join(workspaceRoot, "kisaragi-tree", "prj-direview"), { recursive: true });

  writeFileSync(join(workspaceRoot, "AGENTS.md"), "# Root\n", "utf8");
  writeFileSync(join(workspaceRoot, ".gitignore"), "node_modules/\n", "utf8");
  writeFileSync(join(workspaceRoot, "kisaragi-db", "agents.md"), "# DB\n", "utf8");
  writeFileSync(join(workspaceRoot, "kisaragi-db", "--devs", "--plans", "plan.md"), "# Plan\n", "utf8");
  writeFileSync(join(workspaceRoot, "kisaragi-ruling", "agents.md"), "# Ruling\n", "utf8");
  writeFileSync(join(workspaceRoot, "kisaragi-skills", "agents.md"), "# Skills\n", "utf8");
  writeFileSync(join(workspaceRoot, "kisaragi-tree", "agents.md"), "# Tree Agents\n", "utf8");
  writeFileSync(join(workspaceRoot, "kisaragi-tree", "tree-sync.ps1"), "Write-Host sync\n", "utf8");

  const manifestPath = join(root, "active-project-manifest.json");
  writeFileSync(
    manifestPath,
    JSON.stringify(
      {
        projectId: "prj-direview",
        sourceProfiles: [
          {
            profileId: "db-view",
            label: "db-view",
            projectRoot: root,
            documentRoots: ["kisaragi"],
            compareRoots: ["kisaragi"]
          },
          {
            profileId: "prj-view",
            label: "prj-view",
            projectRoot: root,
            documentRoots: ["kisaragi"],
            compareRoots: ["kisaragi"]
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

function rootName(value: string): string {
  return value.split(/[\\/]/).filter(Boolean).at(-1) ?? value;
}
