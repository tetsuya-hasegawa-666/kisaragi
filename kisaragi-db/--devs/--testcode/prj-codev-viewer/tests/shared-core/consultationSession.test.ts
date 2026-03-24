import { describe, expect, it } from "vitest";

import {
  createConsultationSession,
  type ConsultationBundleItem
} from "../../../../--products/prj-codev-viewer/src/shared-core/model/ConsultationSession";

describe("createConsultationSession", () => {
  it("builds the document consultation contract from the selected bundle", () => {
    const bundle: ConsultationBundleItem[] = [
      {
        id: "doc-1",
        kind: "document",
        label: "North Star",
        path: "docs/artifact/north_star.md"
      }
    ];

    const session = createConsultationSession({
      workspaceId: "document",
      sourcePolicy: "filesystem recursive read-only",
      bundle
    });

    expect(session.storyId).toBe("document-consultation");
    expect(session.bundle).toEqual(bundle);
    expect(session.responseFields.map((field) => field.key)).toEqual([
      "summary",
      "evidence",
      "next_action"
    ]);
    expect(session.approvalState).toBe("consultation-only");
    expect(session.behaviorLeaves).toContain("document-bundle-fixed");
  });

  it("keeps code consultation behind the phase gate", () => {
    const session = createConsultationSession({
      workspaceId: "code",
      sourcePolicy: "filesystem recursive read-only",
      bundle: [
        {
          id: "code-1",
          kind: "code",
          label: "Document Controller",
          path: "src/document-workspace/controller/DocumentWorkspaceController.ts"
        }
      ]
    });

    expect(session.storyId).toBe("code-consultation");
    expect(session.approvalState).toBe("phase-gated-read-only");
    expect(session.behaviorLeaves).toContain("code-phase-gate-visible");
  });
});
