import type { DocumentRecord } from "../model/DocumentRecord";
import type { DocumentRepository } from "../model/DocumentRepository";

export interface SourceProfileOption {
  profileId: string;
  profileLabel: string;
}

export interface DocumentTreeNode {
  id: string;
  label: string;
  path: string;
  kind: "directory" | "file";
  children: DocumentTreeNode[];
}

export interface SelectedDocumentSummary {
  id: string;
  title: string;
  path: string;
  body: string;
}

export interface DocumentWorkspaceState {
  availableProfiles: SourceProfileOption[];
  activeProfileId: string;
  tree: DocumentTreeNode[];
  expandedPaths: string[];
  expandDepth: number;
  selectedPath?: string;
  searchQuery?: string;
  matchedPaths?: string[];
  selectedDocument?: SelectedDocumentSummary;
  selectedTrail: DocumentTreeNode[];
  isStoryReleaseMapMode: boolean;
}

export class DocumentWorkspaceController {
  public constructor(private readonly repository: DocumentRepository) {}

  public createSelectionState(
    activeProfileId?: string,
    expandedPaths: string[] = [],
    selectedPath?: string,
    searchQuery = "",
    expandDepth = 3
  ): DocumentWorkspaceState {
    const documents = this.repository.listDocuments().sort((left, right) =>
      left.path.localeCompare(right.path, "ja")
    );
    const availableProfiles = this.listProfiles(documents);
    const resolvedProfileId =
      activeProfileId && availableProfiles.some((profile) => profile.profileId === activeProfileId)
        ? activeProfileId
        : availableProfiles[0]?.profileId ?? "";
    const profileDocuments = documents.filter((document) => document.profileId === resolvedProfileId);
    const tree = this.buildTree(profileDocuments);

    const normalizedQuery = searchQuery.trim().toLocaleLowerCase("ja");
    const matchedPaths = normalizedQuery.length
      ? this.collectMatchedPaths(tree, normalizedQuery)
      : [];
    const effectiveExpandedPaths = normalizedQuery.length
      ? this.collectSearchExpandedPaths(tree, normalizedQuery)
      : expandedPaths;

    const selectedDocumentRecord = profileDocuments.find(
      (document) => document.nodeKind === "file" && document.path === selectedPath
    );
    const selectedTrail = selectedPath ? this.findTrail(tree, selectedPath) : [];
    const isStoryReleaseMapMode = selectedPath?.toLocaleLowerCase("ja").endsWith("story_release_map.md") ?? false;

    return {
      availableProfiles,
      activeProfileId: resolvedProfileId,
      tree,
      expandedPaths: effectiveExpandedPaths,
      expandDepth,
      selectedPath,
      searchQuery,
      matchedPaths,
      selectedDocument: selectedDocumentRecord
        ? {
            id: selectedDocumentRecord.id,
            title: selectedDocumentRecord.title,
            path: selectedDocumentRecord.path,
            body: selectedDocumentRecord.body
          }
        : undefined,
      selectedTrail,
      isStoryReleaseMapMode
    };
  }

  private collectMatchedPaths(nodes: DocumentTreeNode[], query: string): string[] {
    const matches: string[] = [];
    for (const node of nodes) {
      if (node.label.toLocaleLowerCase("ja").includes(query)) {
        matches.push(node.path);
      }
      matches.push(...this.collectMatchedPaths(node.children, query));
    }
    return matches;
  }

  private collectSearchExpandedPaths(nodes: DocumentTreeNode[], query: string): string[] {
    const expanded = new Set<string>();
    const visit = (node: DocumentTreeNode): boolean => {
      const selfMatches = node.label.toLocaleLowerCase("ja").includes(query);
      let descendantMatches = false;
      for (const child of node.children) {
        descendantMatches = visit(child) || descendantMatches;
      }
      if (node.kind === "directory" && (selfMatches || descendantMatches)) {
        expanded.add(node.path);
      }
      return selfMatches || descendantMatches;
    };
    for (const node of nodes) {
      visit(node);
    }
    return [...expanded];
  }

  private findTrail(nodes: DocumentTreeNode[], selectedPath: string): DocumentTreeNode[] {
    for (const node of nodes) {
      if (node.path === selectedPath) {
        return [node];
      }
      const childTrail = this.findTrail(node.children, selectedPath);
      if (childTrail.length > 0) {
        return [node, ...childTrail];
      }
    }
    return [];
  }

  private listProfiles(documents: DocumentRecord[]): SourceProfileOption[] {
    const profiles = new Map<string, string>();
    for (const document of documents) {
      profiles.set(document.profileId, document.profileLabel);
    }

    return [...profiles.entries()]
      .map(([profileId, profileLabel]) => ({ profileId, profileLabel }))
      .sort((left, right) => {
        if (left.profileId === "codev-view" && right.profileId !== "codev-view") {
          return -1;
        }
        if (right.profileId === "codev-view" && left.profileId !== "codev-view") {
          return 1;
        }
        return left.profileLabel.localeCompare(right.profileLabel, "ja");
      });
  }

  private buildTree(documents: DocumentRecord[]): DocumentTreeNode[] {
    const rootNodes: DocumentTreeNode[] = [];

    for (const document of documents) {
      const segments = document.path.split("/");
      let currentLevel = rootNodes;
      let currentPath = "";

      segments.forEach((segment, index) => {
        currentPath = currentPath.length === 0 ? segment : `${currentPath}/${segment}`;
        const isFile = index === segments.length - 1 && document.nodeKind === "file";
        let node = currentLevel.find((entry) => entry.path === currentPath);

        if (!node) {
          node = {
            id: `${isFile ? "file" : "dir"}:${currentPath}`,
            label: segment,
            path: currentPath,
            kind: isFile ? "file" : "directory",
            children: []
          };
          currentLevel.push(node);
        }

        currentLevel = node.children;
      });
    }

    return this.sortNodes(rootNodes);
  }

  private sortNodes(nodes: DocumentTreeNode[]): DocumentTreeNode[] {
    return [...nodes]
      .sort((left, right) => {
        if (left.kind !== right.kind) {
          return left.kind === "directory" ? -1 : 1;
        }
        return left.label.localeCompare(right.label, "ja");
      })
      .map((node) => ({
        ...node,
        children: this.sortNodes(node.children)
      }));
  }
}
