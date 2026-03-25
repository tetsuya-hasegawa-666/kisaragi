import { describe, expect, it } from "vitest";

import { CodeWorkspaceController } from "../../../../--products/prj-direview/src/code-workspace/controller/CodeWorkspaceController";
import { StaticCodeTargetRepository } from "../../../../--products/prj-direview/src/code-workspace/model/StaticCodeTargetRepository";

describe("CodeWorkspaceController", () => {
  it("returns read-only targets and a policy note", () => {
    const controller = new CodeWorkspaceController(
      new StaticCodeTargetRepository(
        [
          {
            id: "document-controller",
            title: "DocumentWorkspaceController.ts",
            path: "src/document-workspace/controller/DocumentWorkspaceController.ts",
            description: "ts / 80 lines",
            kind: "ts",
            updatedAt: "2026-03-14T10:00:00Z"
          }
        ],
        "filesystem recursive read-only"
      )
    );

    const state = controller.createState();

    expect(state.targets).toHaveLength(1);
    expect(state.policyNote.length).toBeGreaterThan(0);
    expect(state.sourcePolicy).toContain("filesystem");
    expect(state.selectedTargets).toHaveLength(1);
  });

  it("keeps selected code targets and returns a phase-gated consultation response", () => {
    const controller = new CodeWorkspaceController(
      new StaticCodeTargetRepository(
        [
          {
            id: "document-controller",
            title: "DocumentWorkspaceController.ts",
            path: "src/document-workspace/controller/DocumentWorkspaceController.ts",
            description: "ts / 80 lines",
            kind: "ts",
            updatedAt: "2026-03-14T10:00:00Z"
          },
          {
            id: "data-controller",
            title: "DataWorkspaceController.ts",
            path: "src/data-workspace/controller/DataWorkspaceController.ts",
            description: "ts / 90 lines",
            kind: "ts",
            updatedAt: "2026-03-14T10:05:00Z"
          }
        ],
        "filesystem recursive read-only"
      )
    );

    const selected = controller.toggleTargetSelection("data-controller");
    const consulted = controller.consultTargets({
      ...selected.consultation,
      focusPrompt: "phase gate check"
    });

    expect(selected.selectedTargets).toHaveLength(2);
    expect(consulted.consultation.lastResponse?.summary).toContain("2 ");
    expect(consulted.consultation.lastResponse?.nextAction).toContain("phase gate check");
  });
});
