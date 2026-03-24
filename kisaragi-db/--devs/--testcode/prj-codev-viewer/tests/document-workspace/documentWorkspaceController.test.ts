import { describe, expect, it } from "vitest";

import { DocumentWorkspaceController } from "../../../../--products/prj-codev-viewer/src/document-workspace/controller/DocumentWorkspaceController";
import type { DocumentRecord } from "../../../../--products/prj-codev-viewer/src/document-workspace/model/DocumentRecord";
import type { DocumentRepository } from "../../../../--products/prj-codev-viewer/src/document-workspace/model/DocumentRepository";

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
        createDocument("db-a", "codev-db", "codev-db basis", "--docs/--artifact/prj-codev-viewer/north_star.md"),
        createDocument("view-a", "codev-view", "codev-view basis", "prj-codev-viewer/README.md")
      ])
    );

    const state = controller.createSelectionState();

    expect(state.availableProfiles.map((profile) => profile.profileId)).toEqual([
      "codev-view",
      "codev-db"
    ]);
    expect(state.activeProfileId).toBe("codev-view");
  });

  it("builds a nested tree for the active profile only", () => {
    const controller = new DocumentWorkspaceController(
      new StubDocumentRepository([
        createDocument("db-a", "codev-db", "codev-db basis", "--docs/--artifact/prj-codev-viewer/north_star.md"),
        createDocument("db-b", "codev-db", "codev-db basis", "--docs/--operations/prj-codev-viewer/change_protocol.md"),
        createDocument("view-a", "codev-view", "codev-view basis", "prj-codev-viewer/README.md")
      ])
    );

    const state = controller.createSelectionState("codev-db");

    expect(state.tree[0]?.label).toBe("--docs");
    expect(state.tree[0]?.children[0]?.label).toBe("--artifact");
    expect(state.tree[0]?.children[0]?.children[0]?.label).toBe("prj-codev-viewer");
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
