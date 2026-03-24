import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { basename, extname, join, relative, resolve, sep } from "node:path";

import type { DocumentRecord } from "../src/document-workspace/model/DocumentRecord";

export interface SourceProfileManifest {
  profileId: string;
  label: string;
  projectRoot: string;
  documentRoots: string[];
  compareRoots?: string[];
}

export interface ProjectManifest {
  projectId: string;
  sourceProfiles: SourceProfileManifest[];
  ignoreGlobs: string[];
  readOnly: boolean;
}

export interface LiveSourceProfile {
  profileId: string;
  label: string;
  projectRoot: string;
  sourcePolicy: string;
  documents: DocumentRecord[];
}

export interface LiveProjectSnapshot {
  profiles: LiveSourceProfile[];
  readOnly: boolean;
  sourceSignature: string;
}

export interface RevealTarget {
  profileId: string;
  absolutePath: string;
  relativePath: string;
  kind: "file" | "directory";
}

export function loadLiveProjectSnapshot(manifestPath: string): LiveProjectSnapshot {
  const manifest = readManifest(manifestPath);
  const profiles = manifest.sourceProfiles.map((profile) => buildProfileSnapshot(profile, manifest.ignoreGlobs));

  return {
    profiles,
    readOnly: manifest.readOnly,
    sourceSignature: buildSourceSignature(profiles)
  };
}

export function resolveRevealTarget(
  manifestPath: string,
  profileId: string,
  relativePath: string
): RevealTarget {
  const manifest = readManifest(manifestPath);
  const profile = manifest.sourceProfiles.find((entry) => entry.profileId === profileId);

  if (!profile) {
    throw new Error(`Unknown source profile '${profileId}'.`);
  }

  const absolutePath = resolve(profile.projectRoot, relativePath);
  if (!isInsideRoot(profile.projectRoot, absolutePath)) {
    throw new Error("Reveal path is outside projectRoot.");
  }
  if (!existsSync(absolutePath)) {
    throw new Error("Reveal source was not found.");
  }

  const allowedRoots = profile.compareRoots ?? profile.documentRoots;
  const isAllowed = allowedRoots.some((configuredRoot) => {
    const absoluteRoot = resolve(profile.projectRoot, configuredRoot);
    return absolutePath === absoluteRoot || isInsideRoot(absoluteRoot, absolutePath);
  });
  if (!isAllowed) {
    throw new Error("Reveal path is outside configured roots.");
  }

  const stats = statSync(absolutePath);
  return {
    profileId,
    absolutePath,
    relativePath: toProjectRelativePath(profile.projectRoot, absolutePath),
    kind: stats.isDirectory() ? "directory" : "file"
  };
}

function buildProfileSnapshot(
  profile: SourceProfileManifest,
  ignoreGlobs: string[]
): LiveSourceProfile {
  const roots = profile.compareRoots ?? profile.documentRoots;
  const documents = collectEntries(profile.projectRoot, roots, ignoreGlobs)
    .filter((entry) => entry.kind === "directory" || isDisplayableFile(entry.absolutePath))
    .map((entry) => buildDocumentRecord(profile, entry.absolutePath, entry.kind))
    .sort((left, right) => left.path.localeCompare(right.path, "ja"));

  return {
    profileId: profile.profileId,
    label: profile.label,
    projectRoot: profile.projectRoot,
    sourcePolicy: "filesystem recursive read-only",
    documents
  };
}

function buildDocumentRecord(
  profile: SourceProfileManifest,
  absolutePath: string,
  kind: "file" | "directory"
): DocumentRecord {
  const body = kind === "file" ? readFileSync(absolutePath, "utf8") : "";
  const relativePath = toProjectRelativePath(profile.projectRoot, absolutePath);

  return {
    id: `${profile.profileId}:${relativePath}`,
    profileId: profile.profileId,
    profileLabel: profile.label,
    nodeKind: kind,
    title: kind === "file" ? resolveDocumentTitle(absolutePath, body) : basename(absolutePath),
    path: relativePath,
    body,
    tags: buildDocumentTags(relativePath, kind)
  };
}

function collectEntries(
  projectRoot: string,
  roots: string[],
  ignoreGlobs: string[]
): Array<{ absolutePath: string; kind: "file" | "directory" }> {
  const result: Array<{ absolutePath: string; kind: "file" | "directory" }> = [];

  for (const root of roots) {
    const absoluteRoot = resolve(projectRoot, root);
    if (!isInsideRoot(projectRoot, absoluteRoot)) {
      throw new Error(`Root '${root}' is outside projectRoot.`);
    }
    if (!existsSync(absoluteRoot)) {
      continue;
    }
    if (!statSync(absoluteRoot).isDirectory()) {
      continue;
    }
    walkDirectory(projectRoot, absoluteRoot, ignoreGlobs, result);
  }

  return result;
}

function walkDirectory(
  projectRoot: string,
  currentPath: string,
  ignoreGlobs: string[],
  result: Array<{ absolutePath: string; kind: "file" | "directory" }>
): void {
  const relativePath = toProjectRelativePath(projectRoot, currentPath);
  if (relativePath && shouldIgnore(ignoreGlobs, relativePath)) {
    return;
  }

  if (relativePath) {
    result.push({ absolutePath: currentPath, kind: "directory" });
  }

  for (const entry of readdirSync(currentPath, { withFileTypes: true })) {
    const absolutePath = join(currentPath, entry.name);
    const entryRelativePath = toProjectRelativePath(projectRoot, absolutePath);
    if (shouldIgnore(ignoreGlobs, entryRelativePath)) {
      continue;
    }
    const isDirectoryLike =
      entry.isDirectory() || (entry.isSymbolicLink() && existsSync(absolutePath) && statSync(absolutePath).isDirectory());
    if (isDirectoryLike) {
      walkDirectory(projectRoot, absolutePath, ignoreGlobs, result);
      continue;
    }
    if (entry.isFile()) {
      result.push({ absolutePath, kind: "file" });
    }
  }
}

function readManifest(manifestPath: string): ProjectManifest {
  return JSON.parse(readFileSync(manifestPath, "utf8")) as ProjectManifest;
}

function resolveDocumentTitle(filePath: string, body: string): string {
  const heading = body
    .split(/\r?\n/)
    .map((line) => line.trim())
    .find((line) => line.startsWith("# "));

  return heading ? heading.replace(/^#\s+/, "") : basename(filePath, extname(filePath));
}

function isDisplayableFile(filePath: string): boolean {
  const normalizedPath = filePath.toLowerCase();
  const fileName = basename(normalizedPath);
  const extension = extname(normalizedPath);

  const allowedExtensions = new Set([
    ".md",
    ".txt",
    ".json",
    ".jsonc",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
    ".html",
    ".css",
    ".scss",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".py",
    ".rb",
    ".php",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".psm1",
    ".bat",
    ".cmd",
    ".sql",
    ".graphql",
    ".gql",
    ".csv",
    ".tsv",
    ".log"
  ]);
  const allowedNames = new Set([
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".gitignore",
    ".gitattributes",
    ".editorconfig",
    "dockerfile",
    "makefile",
    "readme",
    "license",
    "agents.md"
  ]);

  return allowedExtensions.has(extension) || allowedNames.has(fileName);
}

function buildDocumentTags(projectRelativePath: string, kind: "file" | "directory"): string[] {
  const segments = projectRelativePath.split("/");
  const tags = new Set<string>();

  if (segments[0]) {
    tags.add(segments[0]);
  }

  const extension = extname(projectRelativePath).replace(".", "");
  if (extension) {
    tags.add(extension);
  }
  tags.add(kind);

  return [...tags];
}

function shouldIgnore(ignoreGlobs: string[], relativePath: string): boolean {
  const normalized = relativePath.replaceAll("\\", "/");
  const segments = normalized.split("/");

  return ignoreGlobs.some((pattern) => {
    const token = pattern.replaceAll("**/", "").replaceAll("/**", "").replaceAll("*", "");
    if (token.length === 0) {
      return false;
    }
    const normalizedToken = token.replaceAll("\\", "/").replace(/^\/+|\/+$/g, "");
    return segments.includes(normalizedToken);
  });
}

function toProjectRelativePath(projectRoot: string, absolutePath: string): string {
  return relative(projectRoot, absolutePath).split(sep).join("/");
}

function isInsideRoot(projectRoot: string, absolutePath: string): boolean {
  const relativePath = relative(projectRoot, absolutePath);
  return relativePath === "" || (!relativePath.startsWith("..") && !relativePath.includes(`..${sep}`));
}

function buildSourceSignature(profiles: LiveSourceProfile[]): string {
  return profiles
    .map(
      (profile) =>
        `${profile.profileId}:${profile.documents
          .map((document) => `${document.path}:${document.body.length}`)
          .join("|")}`
    )
    .join("::");
}
