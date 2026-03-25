import { describe, expect, it } from "vitest";

import type { DataWorkspaceState } from "../../../../--products/prj-direview/src/data-workspace/controller/DataWorkspaceController";
import { DataWorkspaceView } from "../../../../--products/prj-direview/src/data-workspace/view/DataWorkspaceView";

const state: DataWorkspaceState = {
  datasets: [
    {
      id: "dataset-2",
      name: "session-20260317-01",
      category: "session",
      recordCount: 5,
      status: "ready",
      updatedAt: "2026-03-14T09:30:00Z",
      path: "--process/--testlogs/prj-isensorium/session-20260317-01",
      topDirectory: "prj-isensorium",
      recordingMode: "pocket_recording",
      requestedRoute: "frozen_camerax_arcore",
      activeRoute: "frozen_camerax_arcore",
      files: [
        {
          name: "session_manifest.json",
          relativePath: "--process/--testlogs/prj-isensorium/session-20260317-01/session_manifest.json",
          sizeBytes: 512,
          present: true
        }
      ],
      download: {
        kind: "directory",
        relativePath: "--process/--testlogs/prj-isensorium/session-20260317-01",
        fileName: "session-20260317-01.zip"
      },
      previewText: "sessionId: session-20260317-01"
    },
    {
      id: "dataset-1",
      name: "summary",
      category: "json",
      recordCount: 12,
      status: "draft",
      updatedAt: "2026-03-14T08:30:00Z",
      path: "exports/summary.json",
      topDirectory: "exports"
    }
  ],
  results: [
    {
      id: "result-1",
      datasetId: "dataset-2",
      summary: "session-20260317-01 updated to ready (5 records)",
      createdAt: "2026-03-14T09:30:00Z"
    }
  ],
  selectedDatasets: [
    {
      id: "dataset-2",
      name: "session-20260317-01",
      category: "session",
      recordCount: 5,
      status: "ready",
      updatedAt: "2026-03-14T09:30:00Z"
    }
  ],
  selectedDataset: {
    id: "dataset-2",
    name: "session-20260317-01",
    category: "session",
    recordCount: 5,
    status: "ready",
    updatedAt: "2026-03-14T09:30:00Z",
    path: "--process/--testlogs/prj-isensorium/session-20260317-01",
    topDirectory: "prj-isensorium",
    recordingMode: "pocket_recording",
    requestedRoute: "frozen_camerax_arcore",
    activeRoute: "frozen_camerax_arcore",
    files: [
      {
        name: "session_manifest.json",
        relativePath: "--process/--testlogs/prj-isensorium/session-20260317-01/session_manifest.json",
        sizeBytes: 512,
        present: true
      }
    ],
    download: {
      kind: "directory",
      relativePath: "--process/--testlogs/prj-isensorium/session-20260317-01",
      fileName: "session-20260317-01.zip"
    },
    previewText: "sessionId: session-20260317-01"
  },
  directoryGroups: [
    {
      topDirectory: "exports",
      datasets: [
        {
          id: "dataset-1",
          name: "summary",
          category: "json",
          recordCount: 12,
          status: "draft",
          updatedAt: "2026-03-14T08:30:00Z",
          path: "exports/summary.json",
          topDirectory: "exports"
        }
      ]
    },
    {
      topDirectory: "prj-isensorium",
      datasets: [
        {
          id: "dataset-2",
          name: "session-20260317-01",
          category: "session",
          recordCount: 5,
          status: "ready",
          updatedAt: "2026-03-14T09:30:00Z",
          path: "--process/--testlogs/prj-isensorium/session-20260317-01",
          topDirectory: "prj-isensorium",
          recordingMode: "pocket_recording",
          requestedRoute: "frozen_camerax_arcore",
          activeRoute: "frozen_camerax_arcore",
          files: [
            {
              name: "session_manifest.json",
              relativePath: "--process/--testlogs/prj-isensorium/session-20260317-01/session_manifest.json",
              sizeBytes: 512,
              present: true
            }
          ],
          download: {
            kind: "directory",
            relativePath: "--process/--testlogs/prj-isensorium/session-20260317-01",
            fileName: "session-20260317-01.zip"
          },
          previewText: "sessionId: session-20260317-01"
        }
      ]
    }
  ],
  sourcePolicy: "filesystem recursive read-only",
  isReadOnly: true,
  consultation: {
    selectedDatasetIds: ["dataset-2"],
    selectedDatasetId: "dataset-2",
    focusPrompt: "anomaly check",
    lastResponse: {
      summary: "1 item fixed as consultation bundle.",
      evidence: ["session-20260317-01 (ready, 5 files)"],
      nextAction: "focus: anomaly check"
    }
  },
  issue: null,
  summary: {
    totalDatasets: 2,
    totalRecords: 17,
    byStatus: [
      { status: "draft", datasetCount: 1, recordCount: 12 },
      { status: "ready", datasetCount: 1, recordCount: 5 }
    ]
  }
};

describe("DataWorkspaceView", () => {
  it("renders archive explorer, preview, and download action", () => {
    const container = document.createElement("section");
    const view = new DataWorkspaceView(container);

    view.render(state);

    expect(container.querySelector("[data-role='total-datasets']")?.textContent).toContain("2");
    expect(container.querySelectorAll("[data-role='dataset-row']")).toHaveLength(2);
    expect(
      container.querySelector("[data-role='chart-bar'][data-status='draft']")?.getAttribute("style")
    ).toContain("100%");
    expect(container.querySelector("[data-role='selected-dataset-title']")?.textContent).toContain(
      "session-20260317-01"
    );
    expect(container.querySelector("[data-role='download-dataset']")?.getAttribute("href")).toContain(
      "/api/dashboard/download?path="
    );
    expect(container.querySelector("[data-role='data-consultation-response']")?.textContent).toContain(
      "Summary"
    );
  });

  it("renders local draft unlock guidance for read-only live data", () => {
    const container = document.createElement("section");
    const view = new DataWorkspaceView(container);

    view.render(state);

    expect(container.textContent).toContain("Read-only");
    expect(container.querySelector("[data-role='dataset-status']")).toBeNull();
    expect(container.querySelector("[data-role='save-dataset']")).toBeNull();
    expect(container.querySelector("[data-role='unlock-data-editing']")).not.toBeNull();
    expect(container.querySelector("[data-role='unlock-data-guidance']")?.textContent).toContain(
      "local draft"
    );
  });
});
