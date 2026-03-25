import type { DatasetRecord } from "./DatasetRecord";
import type { DatasetRepository, DatasetResultRecord } from "./DatasetRepository";

const DATASET_STORAGE_KEY = "direview.datasets";
const RESULT_STORAGE_KEY = "direview.datasetResults";

export class BrowserDatasetRepository implements DatasetRepository {
  public constructor(private readonly seedDatasets: DatasetRecord[]) {}

  public listDatasets(): DatasetRecord[] {
    return this.readDatasets();
  }

  public updateDataset(datasetId: string, status: string, recordCount: number): DatasetRecord {
    const datasets = this.readDatasets();
    const index = datasets.findIndex((dataset) => dataset.id === datasetId);

    if (index < 0) {
      throw new Error(`データセット '${datasetId}' が見つかりません。`);
    }

    const updatedAt = new Date().toISOString();
    const updated = { ...datasets[index], status, recordCount, updatedAt };
    datasets[index] = updated;
    this.writeDatasets(datasets);

    const results = this.readResults();
    results.unshift({
      id: `result-${results.length + 1}`,
      datasetId,
      summary: `${updated.name} を${this.getStatusLabel(status)}に更新し、${recordCount} 件を保存しました。`,
      createdAt: updatedAt
    });
    this.writeResults(results);
    return updated;
  }

  public listResults(): DatasetResultRecord[] {
    return this.readResults();
  }

  public getSourcePolicy(): string {
    return "seed 読み込み + localStorage 更新";
  }

  public isReadOnly(): boolean {
    return false;
  }

  private readDatasets(): DatasetRecord[] {
    const raw = globalThis.localStorage?.getItem(DATASET_STORAGE_KEY);

    if (!raw) {
      this.writeDatasets(this.seedDatasets.map((dataset) => ({ ...dataset })));
      return this.readDatasets();
    }

    return JSON.parse(raw) as DatasetRecord[];
  }

  private writeDatasets(datasets: DatasetRecord[]): void {
    globalThis.localStorage?.setItem(DATASET_STORAGE_KEY, JSON.stringify(datasets));
  }

  private readResults(): DatasetResultRecord[] {
    const raw = globalThis.localStorage?.getItem(RESULT_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as DatasetResultRecord[]) : [];
  }

  private writeResults(results: DatasetResultRecord[]): void {
    globalThis.localStorage?.setItem(RESULT_STORAGE_KEY, JSON.stringify(results));
  }

  private getStatusLabel(status: string): string {
    switch (status) {
      case "draft":
        return "下書き";
      case "ready":
        return "準備完了";
      case "review":
        return "レビュー中";
      case "live":
        return "ライブ";
      default:
        return status;
    }
  }
}
