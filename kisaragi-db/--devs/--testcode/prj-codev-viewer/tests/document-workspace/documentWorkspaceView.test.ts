import { describe, expect, it } from "vitest";

import type { DocumentWorkspaceState } from "../../../../--products/prj-codev-viewer/src/document-workspace/controller/DocumentWorkspaceController";
import {
  DocumentWorkspaceView,
  type DashboardWorkspaceViewState
} from "../../../../--products/prj-codev-viewer/src/document-workspace/view/DocumentWorkspaceView";

const state: DocumentWorkspaceState = {
  availableProfiles: [
    { profileId: "codev-db", profileLabel: "codev-db basis" },
    { profileId: "codev-view", profileLabel: "codev-view basis" }
  ],
  searchQuery: "",
  expandDepth: 3,
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
              id: "file:--docs/--artifact/prj-codev-viewer/north_star.md",
              label: "north_star.md",
              path: "--docs/--artifact/prj-codev-viewer/north_star.md",
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
  });

  it("keeps prj-codev-viewer visible in the sticky trail when present in the tree", () => {
    const container = document.createElement("section");
    const view = new DocumentWorkspaceView(container);

    view.render({
      left: {
        ...state,
        tree: [
          {
            id: "dir:prj-codev-viewer",
            label: "prj-codev-viewer",
            path: "prj-codev-viewer",
            kind: "directory",
            children: [
              {
                id: "file:prj-codev-viewer/README.md",
                label: "README.md",
                path: "prj-codev-viewer/README.md",
                kind: "file",
                children: []
              }
            ]
          }
        ]
      },
      right: state
    });

    expect(container.querySelector("[data-pane='left'] [data-role='selection-trail-shell']")?.textContent).toContain(
      "prj-codev-viewer"
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
          id: "file:--docs/--artifact/prj-codev-viewer/story_release_map.md",
          title: "story_release_map.md",
          path: "--docs/--artifact/prj-codev-viewer/story_release_map.md",
          body: "# Story Release Map\nbody"
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
            id: "file:--docs/--artifact/prj-codev-viewer/story_release_map.md",
            label: "story_release_map.md",
            path: "--docs/--artifact/prj-codev-viewer/story_release_map.md",
            kind: "file",
            children: []
          }
        ]
      },
      right: state
    });

    expect(container.querySelector("[data-role='detail-strip']")).not.toBeNull();
    expect(container.querySelector("[data-role='document-reading-body']")?.textContent).toContain("Story Release Map");
    expect(container.querySelector("[data-role='back-to-search']")).not.toBeNull();
  });

  it("renders plain text for non-markdown files", () => {
    const container = document.createElement("section");
    const view = new DocumentWorkspaceView(container);

    view.render({
      left: {
        ...state,
        selectedDocument: {
          id: "file:--docs/--artifact/prj-codev-viewer/.env",
          title: ".env",
          path: "--docs/--artifact/prj-codev-viewer/.env",
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
            id: "file:--docs/--artifact/prj-codev-viewer/.env",
            label: ".env",
            path: "--docs/--artifact/prj-codev-viewer/.env",
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
