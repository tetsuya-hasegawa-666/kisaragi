import type { DatasetRecord } from "./DatasetRecord";
import type { DatasetRepository, DatasetResultRecord } from "./DatasetRepository";

export class UnlockableDatasetRepository implements DatasetRepository {
  private draftDatasetsById: Map<string, DatasetRecord> | null = null;
  private draftResults: DatasetResultRecord[] | null = null;

  public constructor(private readonly baseRepository: DatasetRepository) {}

  public listDatasets(): DatasetRecord[] {
    if (!this.draftDatasetsById) {
      return this.baseRepository.listDatasets();
    }

    return [...this.draftDatasetsById.values()].map((dataset) => ({ ...dataset }));
  }

  public updateDataset(datasetId: string, status: string, recordCount: number): DatasetRecord {
    if (!this.draftDatasetsById) {
      return this.baseRepository.updateDataset(datasetId, status, recordCount);
    }

    const current = this.draftDatasetsById.get(datasetId);

    if (!current) {
      throw new Error(`Dataset '${datasetId}' was not found.`);
    }

    const updatedAt = new Date().toISOString();
    const updated = { ...current, status, recordCount, updatedAt };
    this.draftDatasetsById.set(datasetId, updated);
    this.draftResults?.unshift({
      id: `draft-result-${(this.draftResults?.length ?? 0) + 1}`,
      datasetId,
      summary: `${updated.name} moved to ${status} (${recordCount} records) in local draft`,
      createdAt: updatedAt
    });
    return { ...updated };
  }

  public listResults(): DatasetResultRecord[] {
    if (!this.draftResults) {
      return this.baseRepository.listResults();
    }

    return this.draftResults.map((result) => ({ ...result }));
  }

  public getSourcePolicy(): string {
    if (!this.draftDatasetsById) {
      return this.baseRepository.getSourcePolicy();
    }

    return `${this.baseRepository.getSourcePolicy()} -> local draft unlock`;
  }

  public isReadOnly(): boolean {
    return this.draftDatasetsById ? false : this.baseRepository.isReadOnly();
  }

  public isLocalDraftUnlocked(): boolean {
    return this.draftDatasetsById !== null;
  }

  public unlockLocalDraft(): void {
    if (this.draftDatasetsById || !this.baseRepository.isReadOnly()) {
      return;
    }

    this.draftDatasetsById = new Map(
      this.baseRepository.listDatasets().map((dataset) => [dataset.id, { ...dataset }])
    );
    this.draftResults = this.baseRepository.listResults().map((result) => ({ ...result }));
  }
}
