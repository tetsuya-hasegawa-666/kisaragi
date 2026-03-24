import type { DatasetRecord } from "./DatasetRecord";
import type { DatasetRepository, DatasetResultRecord } from "./DatasetRepository";

export class StaticDatasetRepository implements DatasetRepository {
  private datasetsById: Map<string, DatasetRecord>;
  private readonly results: DatasetResultRecord[] = [];
  private sourcePolicy: string;
  private readOnly: boolean;

  public constructor(
    datasets: DatasetRecord[],
    options?: { sourcePolicy?: string; readOnly?: boolean }
  ) {
    this.datasetsById = new Map(datasets.map((dataset) => [dataset.id, { ...dataset }]));
    this.sourcePolicy = options?.sourcePolicy ?? "Seed bootstrap + in-app update";
    this.readOnly = options?.readOnly ?? false;
  }

  public listDatasets(): DatasetRecord[] {
    return [...this.datasetsById.values()].map((dataset) => ({ ...dataset }));
  }

  public updateDataset(datasetId: string, status: string, recordCount: number): DatasetRecord {
    if (this.readOnly) {
      throw new Error("このデータソースは読み取り専用です。");
    }

    const current = this.datasetsById.get(datasetId);

    if (!current) {
      throw new Error(`Dataset '${datasetId}' was not found.`);
    }

    const updatedAt = new Date().toISOString();
    const updated = { ...current, status, recordCount, updatedAt };
    this.datasetsById.set(datasetId, updated);
    this.results.unshift({
      id: `result-${this.results.length + 1}`,
      datasetId,
      summary: `${updated.name} updated to ${status} (${recordCount} records)`,
      createdAt: updatedAt
    });
    return { ...updated };
  }

  public listResults(): DatasetResultRecord[] {
    return this.results.map((result) => ({ ...result }));
  }

  public getSourcePolicy(): string {
    return this.sourcePolicy;
  }

  public isReadOnly(): boolean {
    return this.readOnly;
  }

  public replaceDatasets(
    datasets: DatasetRecord[],
    options: { sourcePolicy: string; readOnly: boolean }
  ): void {
    this.datasetsById = new Map(datasets.map((dataset) => [dataset.id, { ...dataset }]));
    this.sourcePolicy = options.sourcePolicy;
    this.readOnly = options.readOnly;
  }
}
