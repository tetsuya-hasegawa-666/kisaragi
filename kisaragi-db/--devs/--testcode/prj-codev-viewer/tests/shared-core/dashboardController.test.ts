import { describe, expect, it } from "vitest";

import { StaticDocumentRepository } from "../../../../--products/prj-codev-viewer/src/document-workspace/model/StaticDocumentRepository";
import { DashboardController } from "../../../../--products/prj-codev-viewer/src/shared-core/controller/DashboardController";

describe("DashboardController", () => {
  it("renders two independent panes and can switch the left pane profile", () => {
    const container = document.createElement("div");
    const controller = new DashboardController(
      container,
      new StaticDocumentRepository(
        [
          {
            id: "db-a",
            profileId: "codev-db",
            profileLabel: "codev-db basis",
            nodeKind: "file",
            title: "north_star.md",
            path: "--docs/--artifact/prj-codev-viewer/north_star.md",
            body: "db",
            tags: ["md"]
          },
          {
            id: "view-a",
            profileId: "codev-view",
            profileLabel: "codev-view basis",
            nodeKind: "file",
            title: "README.md",
            path: "prj-codev-viewer/README.md",
            body: "view",
            tags: ["md"]
          }
        ],
        { sourcePolicy: "filesystem recursive read-only", readOnly: true }
      )
    );

    controller.start();

    let leftPane = container.querySelector("[data-pane='left']") as HTMLElement;
    let rightPane = container.querySelector("[data-pane='right']") as HTMLElement;

    expect(leftPane.textContent).toContain("README.md");
    expect(leftPane.textContent).not.toContain("--docs");
    expect(rightPane.textContent).toContain("README.md");
    expect(container.querySelectorAll("[data-role='tree-toggle']").length).toBeGreaterThan(0);

    (
      leftPane.querySelector("[data-role='profile-tab'][data-profile-id='codev-db']") as HTMLButtonElement
    ).click();

    leftPane = container.querySelector("[data-pane='left']") as HTMLElement;
    rightPane = container.querySelector("[data-pane='right']") as HTMLElement;

    expect(leftPane.textContent).toContain("--docs");
    expect(leftPane.textContent).not.toContain("README.md");
    expect(rightPane.textContent).toContain("README.md");
  });
});
