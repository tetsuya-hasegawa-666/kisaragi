import { describe, expect, it } from "vitest";

import { DocumentWorkspaceController } from "../../../../--products/prj-kisaragi_0001/src/document-workspace/controller/DocumentWorkspaceController";
import type { DocumentRecord } from "../../../../--products/prj-kisaragi_0001/src/document-workspace/model/DocumentRecord";
import type { DocumentRepository } from "../../../../--products/prj-kisaragi_0001/src/document-workspace/model/DocumentRepository";

class StubDocumentRepository implements DocumentRepository {
  public constructor(private readonly documents: DocumentRecord[]) {}

  public listDocuments(): DocumentRecord[] {
    return this.documents;
  }

  public saveDocument(documentId: string, body: string): DocumentRecord {
    const found = this.documents.find((document) => document.id === documentId);
    if (!found) {
      throw new Error("not found");
    }
    found.body = body;
    return found;
  }

  public getSourcePolicy(): string {
    return "filesystem recursive read-only";
  }

  public isReadOnly(): boolean {
    return true;
  }
}

describe("DocumentWorkspaceController", () => {
  it("returns available profiles and defaults to codev-view", () => {
    const controller = new DocumentWorkspaceController(
      new StubDocumentRepository([
        createDocument("db-a", "codev-db", "codev-db basis", "--docs/--artifact/prj-kisaragi_0001/north_star.md"),
        createDocument("view-a", "codev-view", "codev-view basis", "prj-kisaragi_0001/README.md")
      ])
    );

    const state = controller.createSelectionState();

    expect(state.availableProfiles.map((profile) => profile.profileId)).toEqual([
      "codev-view",
      "codev-db"
    ]);
    expect(state.activeProfileId).toBe("codev-view");
  });

  it("prefers prj-view then db-view when launcher profiles are present", () => {
    const controller = new DocumentWorkspaceController(
      new StubDocumentRepository([
        createDocument("db-a", "db-view", "db-view", "--devs/--plans/plan.md"),
        createDocument("tree-a", "prj-view", "prj-view", "prj-kisaragi_0001/--plans/plan.md")
      ])
    );

    const state = controller.createSelectionState();

    expect(state.availableProfiles.map((profile) => profile.profileId)).toEqual(["prj-view", "db-view"]);
    expect(state.activeProfileId).toBe("prj-view");
  });

  it("builds a nested tree for the active profile only", () => {
    const controller = new DocumentWorkspaceController(
      new StubDocumentRepository([
        createDocument("db-a", "codev-db", "codev-db basis", "--docs/--artifact/prj-kisaragi_0001/north_star.md"),
        createDocument("db-b", "codev-db", "codev-db basis", "--docs/--operations/prj-kisaragi_0001/change_protocol.md"),
        createDocument("view-a", "codev-view", "codev-view basis", "prj-kisaragi_0001/README.md")
      ])
    );

    const state = controller.createSelectionState("codev-db");

    expect(state.tree[0]?.label).toBe("--docs");
    expect(state.tree[0]?.children[0]?.label).toBe("--artifact");
    expect(state.tree[0]?.children[0]?.children[0]?.label).toBe("prj-kisaragi_0001");
  });

  it("expands ancestor directories for the selected path", () => {
    const controller = new DocumentWorkspaceController(
      new StubDocumentRepository([
        createDocument("tree-a", "prj-view", "prj-view", "kisaragi/kisaragi-tree/prj-kisaragi_0001/--plans/plan.md")
      ])
    );

    const state = controller.createSelectionState(
      "prj-view",
      [],
      "kisaragi/kisaragi-tree/prj-kisaragi_0001/--plans/plan.md"
    );

    expect(state.expandedPaths).toEqual([
      "kisaragi",
      "kisaragi/kisaragi-tree",
      "kisaragi/kisaragi-tree/prj-kisaragi_0001",
      "kisaragi/kisaragi-tree/prj-kisaragi_0001/--plans"
    ]);
  });

  it("does not force-expand the selected directory itself", () => {
    const controller = new DocumentWorkspaceController(
      new StubDocumentRepository([
        createDirectory("tree-root", "prj-view", "prj-view", "kisaragi"),
        createDirectory("tree-child", "prj-view", "prj-view", "kisaragi/kisaragi-tree"),
        createDirectory("tree-leaf", "prj-view", "prj-view", "kisaragi/kisaragi-tree/prj-kisaragi_0001")
      ])
    );

    const state = controller.createSelectionState("prj-view", [], "kisaragi/kisaragi-tree");

    expect(state.expandedPaths).toEqual(["kisaragi"]);
  });
});

function createDocument(
  id: string,
  profileId: string,
  profileLabel: string,
  path: string
): DocumentRecord {
  return {
    id,
    profileId,
    profileLabel,
    nodeKind: "file",
    title: path.split("/").pop() ?? path,
    path,
    body: path,
    tags: ["md"]
  };
}

function createDirectory(
  id: string,
  profileId: string,
  profileLabel: string,
  path: string
): DocumentRecord {
  return {
    id,
    profileId,
    profileLabel,
    nodeKind: "directory",
    title: path.split("/").pop() ?? path,
    path,
    body: "",
    tags: ["directory"]
  };
}
