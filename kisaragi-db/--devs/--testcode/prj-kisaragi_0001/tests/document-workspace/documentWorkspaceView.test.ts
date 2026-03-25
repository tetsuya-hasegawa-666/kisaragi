import { describe, expect, it } from "vitest";

import type { DocumentWorkspaceState } from "../../../../--products/prj-kisaragi_0001/src/document-workspace/controller/DocumentWorkspaceController";
import {
  DocumentWorkspaceView,
  type DashboardWorkspaceViewState
} from "../../../../--products/prj-kisaragi_0001/src/document-workspace/view/DocumentWorkspaceView";

const state: DocumentWorkspaceState = {
  availableProfiles: [
    { profileId: "codev-db", profileLabel: "codev-db basis" },
    { profileId: "codev-view", profileLabel: "codev-view basis" }
  ],
  searchQuery: "",
  expandDepth: 1,
  matchedPaths: [],
  selectedTrail: [],
  isStoryReleaseMapMode: false,
  activeProfileId: "codev-db",
  expandedPaths: ["--docs", "--docs/--artifact"],
  tree: [
    {
      id: "dir:--docs",
      label: "--docs",
      path: "--docs",
      kind: "directory",
      children: [
        {
          id: "dir:--docs/--artifact",
          label: "--artifact",
          path: "--docs/--artifact",
          kind: "directory",
          children: [
            {
              id: "file:--docs/--artifact/prj-kisaragi_0001/north_star.md",
              label: "north_star.md",
              path: "--docs/--artifact/prj-kisaragi_0001/north_star.md",
              kind: "file",
              children: []
            }
          ]
        }
      ]
    }
  ]
};

describe("DocumentWorkspaceView", () => {
  it("renders profile tabs and a compact expandable tree", () => {
    const container = document.createElement("section");
    const view = new DocumentWorkspaceView(container);

    const dashboardState: DashboardWorkspaceViewState = {
      left: state,
      right: state
    };

    view.render(dashboardState);

    expect(container.querySelector("[data-role='selection-stage']")).not.toBeNull();
    expect(container.querySelectorAll("[data-role='profile-tab']")).toHaveLength(4);
    expect(container.querySelectorAll("[data-role='tree-group']")).toHaveLength(4);
    expect(container.querySelectorAll("[data-role='tree-toggle']")).toHaveLength(4);
    expect(container.querySelectorAll("[data-role='selection-pane']")).toHaveLength(2);
    expect(container.querySelectorAll("[data-role='selection-trail-shell']")).toHaveLength(2);
    expect(container.querySelector("[data-pane='left'] [data-role='selection-trail-shell']")?.textContent?.trim()).toBe("");
  });

  it("renders the selected directory path in the sticky trail", () => {
    const container = document.createElement("section");
    const view = new DocumentWorkspaceView(container);

    view.render({
      left: {
        ...state,
        selectedTrail: [
          {
            id: "dir:prj-kisaragi_0001",
            label: "prj-kisaragi_0001",
            path: "prj-kisaragi_0001",
            kind: "directory",
            children: []
          },
          {
            id: "dir:prj-kisaragi_0001/--plans",
            label: "--plans",
            path: "prj-kisaragi_0001/--plans",
            kind: "directory",
            children: []
          }
        ]
      },
      right: state
    });

    expect(container.querySelector("[data-pane='left'] [data-role='selection-trail-shell']")?.textContent).toContain(
      "prj-kisaragi_0001"
    );
    expect(container.querySelector("[data-pane='left'] [data-role='selection-trail-shell']")?.textContent).toContain(
      "--plans"
    );
  });

  it("renders a reading layout when a markdown file is selected", () => {
    const container = document.createElement("section");
    const view = new DocumentWorkspaceView(container);

    view.render({
      left: {
        ...state,
        isStoryReleaseMapMode: true,
        selectedDocument: {
          id: "file:--docs/--artifact/prj-kisaragi_0001/story_release_map.md",
          title: "story_release_map.md",
          path: "--docs/--artifact/prj-kisaragi_0001/story_release_map.md",
          body: "# Story Release Map\n\n- first item\n- second item\n\n```ts\nconst value = 1;\n```"
        },
        selectedTrail: [
          {
            id: "dir:--docs",
            label: "--docs",
            path: "--docs",
            kind: "directory",
            children: []
          },
          {
            id: "dir:--docs/--artifact",
            label: "--artifact",
            path: "--docs/--artifact",
            kind: "directory",
            children: []
          },
          {
            id: "file:--docs/--artifact/prj-kisaragi_0001/story_release_map.md",
            label: "story_release_map.md",
            path: "--docs/--artifact/prj-kisaragi_0001/story_release_map.md",
            kind: "file",
            children: []
          }
        ]
      },
      right: state
    });

    expect(container.querySelector("[data-role='detail-strip']")).not.toBeNull();
    expect(container.querySelector(".markdown-body h1")?.textContent).toContain("Story Release Map");
    expect(container.querySelectorAll(".markdown-body li")).toHaveLength(2);
    expect(container.querySelector(".markdown-body pre code")?.textContent).toContain("const value = 1;");
    expect(container.querySelector("[data-role='back-to-search']")).not.toBeNull();
  });

  it("renders plain text for non-markdown files", () => {
    const container = document.createElement("section");
    const view = new DocumentWorkspaceView(container);

    view.render({
      left: {
        ...state,
        selectedDocument: {
          id: "file:--docs/--artifact/prj-kisaragi_0001/.env",
          title: ".env",
          path: "--docs/--artifact/prj-kisaragi_0001/.env",
          body: "API_KEY=test\nMODE=dev"
        },
        selectedTrail: [
          {
            id: "dir:--docs",
            label: "--docs",
            path: "--docs",
            kind: "directory",
            children: []
          },
          {
            id: "file:--docs/--artifact/prj-kisaragi_0001/.env",
            label: ".env",
            path: "--docs/--artifact/prj-kisaragi_0001/.env",
            kind: "file",
            children: []
          }
        ]
      },
      right: state
    });

    expect(container.querySelector(".plain-text-pre")?.textContent).toContain("API_KEY=test");
  });
});
