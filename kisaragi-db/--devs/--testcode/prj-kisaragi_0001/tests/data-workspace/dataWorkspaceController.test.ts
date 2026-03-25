import { describe, expect, it } from "vitest";

import { DataWorkspaceController } from "../../../../--products/prj-kisaragi_0001/src/data-workspace/controller/DataWorkspaceController";
import type { DatasetRecord } from "../../../../--products/prj-kisaragi_0001/src/data-workspace/model/DatasetRecord";
import type { DatasetRepository, DatasetResultRecord } from "../../../../--products/prj-kisaragi_0001/src/data-workspace/model/DatasetRepository";

class StubDatasetRepository implements DatasetRepository {
  private readonly results: DatasetResultRecord[] = [];

  public constructor(
    private readonly datasets: DatasetRecord[],
    private readonly readOnly = false
  ) {}

  public listDatasets(): DatasetRecord[] {
    return this.datasets;
  }

  public updateDataset(datasetId: string, status: string, recordCount: number): DatasetRecord {
    const index = this.datasets.findIndex((dataset) => dataset.id === datasetId);
    const updated = {
      ...this.datasets[index],
      status,
      recordCount,
      updatedAt: "2026-03-14T10:00:00Z"
    };
    this.datasets[index] = updated;
    this.results.unshift({
      id: `result-${this.results.length + 1}`,
      datasetId,
      summary: `${updated.name} updated to ${status} (${recordCount} records)`,
      createdAt: "2026-03-14T10:00:00Z"
    });
    return updated;
  }

  public listResults(): DatasetResultRecord[] {
    return this.results;
  }

  public getSourcePolicy(): string {
    return this.readOnly ? "filesystem recursive read-only" : "Seed bootstrap + in-app update";
  }

  public isReadOnly(): boolean {
    return this.readOnly;
  }
}

describe("DataWorkspaceController", () => {
  it("returns datasets sorted by updatedAt descending and groups them by top directory", () => {
    const controller = new DataWorkspaceController(
      new StubDatasetRepository([
        {
          id: "dataset-1",
          name: "session-1",
          category: "session",
          recordCount: 12,
          status: "ready",
          updatedAt: "2026-03-14T08:30:00Z",
          path: "--process/--testlogs/prj-isensorium/session-1",
          topDirectory: "prj-isensorium"
        },
        {
          id: "dataset-2",
          name: "summary",
          category: "json",
          recordCount: 5,
          status: "draft",
          updatedAt: "2026-03-14T09:30:00Z",
          path: "exports/summary.json",
          topDirectory: "exports"
        }
      ])
    );

    const state = controller.createState();

    expect(state.datasets.map((dataset) => dataset.id)).toEqual(["dataset-2", "dataset-1"]);
    expect(state.summary.totalDatasets).toBe(2);
    expect(state.summary.totalRecords).toBe(17);
    expect(state.directoryGroups.map((group) => group.topDirectory)).toEqual([
      "exports",
      "prj-isensorium"
    ]);
    expect(state.selectedDataset?.id).toBe("dataset-2");
  });

  it("reports a warning when selected archive is missing a source file", () => {
    const controller = new DataWorkspaceController(
      new StubDatasetRepository([
        {
          id: "dataset-1",
          name: "session-1",
          category: "session",
          recordCount: 2,
          status: "ready",
          updatedAt: "2026-03-14T08:30:00Z",
          files: [
            { name: "session_manifest.json", relativePath: "tmp/session-1/session_manifest.json", sizeBytes: 120, present: true },
            { name: "video.mp4", relativePath: "tmp/session-1/video.mp4", sizeBytes: 0, present: false }
          ],
          download: {
            kind: "directory",
            relativePath: "tmp/session-1",
            fileName: "session-1.zip"
          }
        }
      ])
    );

    const state = controller.createState();

    expect(state.issue?.severity).toBe("warning");
    expect(state.issue?.message).toContain("source file");
  });

  it("keeps a multi-dataset consultation bundle and returns a consultation response", () => {
    const controller = new DataWorkspaceController(
      new StubDatasetRepository([
        {
          id: "dataset-1",
          name: "session-1",
          category: "session",
          recordCount: 12,
          status: "ready",
          updatedAt: "2026-03-14T08:30:00Z"
        },
        {
          id: "dataset-2",
          name: "summary",
          category: "json",
          recordCount: 5,
          status: "draft",
          updatedAt: "2026-03-14T09:30:00Z"
        }
      ])
    );

    const selected = controller.toggleDatasetSelection("dataset-1", {
      selectedDatasetIds: ["dataset-2"],
      selectedDatasetId: "dataset-2"
    });
    const consulted = controller.consultDatasets({
      ...selected.consultation,
      focusPrompt: "anomaly check"
    });

    expect(selected.consultation.selectedDatasetIds).toEqual(["dataset-2", "dataset-1"]);
    expect(consulted.selectedDatasets).toHaveLength(2);
    expect(consulted.consultation.lastResponse?.summary).toContain("2 ");
    expect(consulted.consultation.lastResponse?.nextAction).toContain("anomaly check");
  });
});
