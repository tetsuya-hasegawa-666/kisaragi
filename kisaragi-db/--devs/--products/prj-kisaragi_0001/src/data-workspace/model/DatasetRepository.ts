import type { DatasetRecord } from "./DatasetRecord";

export interface DatasetResultRecord {
  id: string;
  datasetId: string;
  summary: string;
  createdAt: string;
}

export interface DatasetRepository {
  listDatasets(): DatasetRecord[];
  updateDataset(datasetId: string, status: string, recordCount: number): DatasetRecord;
  listResults(): DatasetResultRecord[];
  getSourcePolicy(): string;
  isReadOnly(): boolean;
}
