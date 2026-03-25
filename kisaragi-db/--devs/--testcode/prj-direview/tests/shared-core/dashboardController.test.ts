import { beforeEach, describe, expect, it } from "vitest";

import { StaticDocumentRepository } from "../../../../--products/prj-direview/src/document-workspace/model/StaticDocumentRepository";
import { DashboardController } from "../../../../--products/prj-direview/src/shared-core/controller/DashboardController";

describe("DashboardController", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it("restores the active profile from sessionStorage after reload", () => {
    const repository = new StaticDocumentRepository(
      [
        {
          id: "db-a",
          profileId: "db-view",
          profileLabel: "db-view",
          nodeKind: "file",
          title: "plan.md",
          path: "--devs/--plans/plan.md",
          body: "db",
          tags: ["md"]
        },
        {
          id: "tree-a",
          profileId: "prj-view",
          profileLabel: "prj-view",
          nodeKind: "file",
          title: "tree.md",
          path: "prj-direview/tree.md",
          body: "tree",
          tags: ["md"]
        }
      ],
      { sourcePolicy: "filesystem recursive read-only", readOnly: true }
    );

    const firstContainer = document.createElement("div");
    const firstController = new DashboardController(firstContainer, repository);
    firstController.start();
    (
      firstContainer.querySelector(
        "[data-pane='left'] [data-role='profile-tab'][data-profile-id='db-view']"
      ) as HTMLButtonElement
    ).click();

    const secondContainer = document.createElement("div");
    const secondController = new DashboardController(secondContainer, repository);
    secondController.start();

    expect((secondContainer.querySelector("[data-pane='left']") as HTMLElement).textContent).toContain("--devs");
    expect((secondContainer.querySelector("[data-pane='left']") as HTMLElement).textContent).not.toContain("tree.md");
  });

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
            path: "--docs/--artifact/prj-direview/north_star.md",
            body: "db",
            tags: ["md"]
          },
          {
            id: "view-a",
            profileId: "codev-view",
            profileLabel: "codev-view basis",
            nodeKind: "file",
            title: "README.md",
            path: "prj-direview/README.md",
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

    (leftPane.querySelector("[data-role='expand-depth-input']") as HTMLInputElement).value = "2";
    (leftPane.querySelector("[data-role='expand-depth-input']") as HTMLInputElement).dispatchEvent(
      new Event("input", { bubbles: true })
    );
    (rightPane.querySelector("[data-role='expand-depth-input']") as HTMLInputElement).value = "2";
    (rightPane.querySelector("[data-role='expand-depth-input']") as HTMLInputElement).dispatchEvent(
      new Event("input", { bubbles: true })
    );
    (leftPane.querySelector("[data-role='expand-all']") as HTMLButtonElement).click();
    (rightPane.querySelector("[data-role='expand-all']") as HTMLButtonElement).click();

    leftPane = container.querySelector("[data-pane='left']") as HTMLElement;
    rightPane = container.querySelector("[data-pane='right']") as HTMLElement;

    expect(leftPane.textContent).toContain("prj-direview");
    expect(leftPane.textContent).not.toContain("--docs");
    expect(rightPane.textContent).toContain("prj-direview");
    expect(container.querySelectorAll("[data-role='tree-toggle']").length).toBeGreaterThan(0);

    (
      leftPane.querySelector("[data-role='profile-tab'][data-profile-id='codev-db']") as HTMLButtonElement
    ).click();

    leftPane = container.querySelector("[data-pane='left']") as HTMLElement;
    rightPane = container.querySelector("[data-pane='right']") as HTMLElement;

    expect(leftPane.textContent).toContain("--docs");
    expect(leftPane.textContent).not.toContain("prj-direview/README.md");
    expect(rightPane.textContent).toContain("prj-direview");
  });

  it("treats collapse-all as depth 1", () => {
    const container = document.createElement("div");
    const controller = new DashboardController(
      container,
      new StaticDocumentRepository(
        [
          {
            id: "tree-dir",
            profileId: "prj-view",
            profileLabel: "prj-view",
            nodeKind: "directory",
            title: "prj-direview",
            path: "prj-direview",
            body: "",
            tags: ["directory"]
          },
          {
            id: "tree-child-dir",
            profileId: "prj-view",
            profileLabel: "prj-view",
            nodeKind: "directory",
            title: "--plans",
            path: "prj-direview/--plans",
            body: "",
            tags: ["directory"]
          },
          {
            id: "tree-file",
            profileId: "prj-view",
            profileLabel: "prj-view",
            nodeKind: "file",
            title: "plan.md",
            path: "prj-direview/--plans/plan.md",
            body: "plan",
            tags: ["md"]
          }
        ],
        { sourcePolicy: "filesystem recursive read-only", readOnly: true }
      )
    );

    controller.start();

    const leftPane = container.querySelector("[data-pane='left']") as HTMLElement;
    (leftPane.querySelector("[data-role='collapse-all']") as HTMLButtonElement).click();

    expect(leftPane.textContent).toContain("prj-direview");
    expect(leftPane.textContent).not.toContain("--plans");
    expect(leftPane.textContent).not.toContain("plan.md");
    expect(
      (leftPane.querySelector("[data-role='expand-depth-input']") as HTMLInputElement).value
    ).toBe("1");
  });
});
