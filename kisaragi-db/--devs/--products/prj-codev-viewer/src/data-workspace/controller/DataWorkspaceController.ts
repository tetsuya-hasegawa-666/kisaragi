import type { DatasetRecord } from "../model/DatasetRecord";
import type { DatasetRepository, DatasetResultRecord } from "../model/DatasetRepository";

export interface DatasetStatusSummary {
  status: string;
  datasetCount: number;
  recordCount: number;
}

export interface DatasetDirectoryGroup {
  topDirectory: string;
  datasets: DatasetRecord[];
}

export interface DataConsultationResponse {
  summary: string;
  evidence: string[];
  nextAction: string;
}

export interface DataConsultationState {
  selectedDatasetIds: string[];
  focusPrompt: string;
  lastResponse: DataConsultationResponse | null;
  selectedDatasetId?: string;
}

export interface DataWorkspaceIssue {
  severity: "info" | "warning" | "error";
  title: string;
  message: string;
}

export interface DataWorkspaceState {
  datasets: DatasetRecord[];
  results: DatasetResultRecord[];
  selectedDatasets: DatasetRecord[];
  selectedDataset: DatasetRecord | null;
  directoryGroups: DatasetDirectoryGroup[];
  sourcePolicy: string;
  isReadOnly: boolean;
  consultation: DataConsultationState;
  issue: DataWorkspaceIssue | null;
  summary: {
    totalDatasets: number;
    totalRecords: number;
    byStatus: DatasetStatusSummary[];
  };
}

export class DataWorkspaceController {
  public constructor(private readonly repository: DatasetRepository) {}

  public createState(
    consultationState?: Partial<DataConsultationState>
  ): DataWorkspaceState {
    const datasets = this.repository
      .listDatasets()
      .sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
    const selectedDatasetIds =
      consultationState?.selectedDatasetIds?.filter((datasetId) =>
        datasets.some((dataset) => dataset.id === datasetId)
      ) ?? (datasets[0] ? [datasets[0].id] : []);
    const selectedDataset =
      datasets.find((dataset) => dataset.id === consultationState?.selectedDatasetId) ??
      datasets.find((dataset) => selectedDatasetIds.includes(dataset.id)) ??
      datasets[0] ??
      null;

    const byStatusMap = new Map<string, DatasetStatusSummary>();
    let totalRecords = 0;

    for (const dataset of datasets) {
      totalRecords += dataset.recordCount;
      const current = byStatusMap.get(dataset.status) ?? {
        status: dataset.status,
        datasetCount: 0,
        recordCount: 0
      };
      current.datasetCount += 1;
      current.recordCount += dataset.recordCount;
      byStatusMap.set(dataset.status, current);
    }

    return {
      datasets,
      results: this.repository
        .listResults()
        .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
        .slice(0, 5),
      selectedDatasets: datasets.filter((dataset) => selectedDatasetIds.includes(dataset.id)),
      selectedDataset,
      directoryGroups: this.groupByTopDirectory(datasets),
      sourcePolicy: this.repository.getSourcePolicy(),
      isReadOnly: this.repository.isReadOnly(),
      consultation: {
        selectedDatasetIds,
        selectedDatasetId: selectedDataset?.id,
        focusPrompt: consultationState?.focusPrompt ?? "",
        lastResponse: consultationState?.lastResponse ?? null
      },
      issue: this.resolveIssue(datasets, selectedDataset),
      summary: {
        totalDatasets: datasets.length,
        totalRecords,
        byStatus: [...byStatusMap.values()].sort((left, right) =>
          left.status.localeCompare(right.status, "ja")
        )
      }
    };
  }

  public selectDataset(
    datasetId: string,
    consultationState?: Partial<DataConsultationState>
  ): DataWorkspaceState {
    const state = this.createState(consultationState);
    return this.createState({
      ...state.consultation,
      selectedDatasetId: datasetId
    });
  }

  public updateDataset(datasetId: string, status: string, recordCount: number): DataWorkspaceState {
    this.repository.updateDataset(datasetId, status, recordCount);
    return this.createState({ selectedDatasetId: datasetId, selectedDatasetIds: [datasetId] });
  }

  public toggleDatasetSelection(
    datasetId: string,
    consultationState?: Partial<DataConsultationState>
  ): DataWorkspaceState {
    const state = this.createState(consultationState);
    const nextSelectedDatasetIds = state.consultation.selectedDatasetIds.includes(datasetId)
      ? state.consultation.selectedDatasetIds.filter((selectedId) => selectedId !== datasetId)
      : [...state.consultation.selectedDatasetIds, datasetId];

    return this.createState({
      ...state.consultation,
      selectedDatasetId: state.consultation.selectedDatasetId ?? datasetId,
      selectedDatasetIds: nextSelectedDatasetIds,
      lastResponse: null
    });
  }

  public updateConsultationFocus(
    focusPrompt: string,
    consultationState?: Partial<DataConsultationState>
  ): DataWorkspaceState {
    const state = this.createState(consultationState);
    return this.createState({
      ...state.consultation,
      focusPrompt
    });
  }

  public consultDatasets(
    consultationState?: Partial<DataConsultationState>
  ): DataWorkspaceState {
    const state = this.createState(consultationState);
    const selectedDatasets = state.selectedDatasets;
    const focusPrompt = state.consultation.focusPrompt.trim();
    const hasSelection = selectedDatasets.length > 0;

    return this.createState({
      ...state.consultation,
      lastResponse: {
        summary: hasSelection
          ? `${selectedDatasets.length} 件のアーカイブ候補を consultation bundle として固定しました。`
          : "consultation 対象のアーカイブを 1 件以上選択してください。",
        evidence: selectedDatasets.map(
          (dataset) =>
            `${dataset.name} (${this.getStatusLabel(dataset.status)}, ${dataset.recordCount} files)`
        ),
        nextAction: hasSelection
          ? focusPrompt.length > 0
            ? `focus: ${focusPrompt}`
            : "確認したい観点を focus に書くと、archive viewer の要約が安定します。"
          : "archive explorer で対象を選び直してください。"
      }
    });
  }

  private groupByTopDirectory(datasets: DatasetRecord[]): DatasetDirectoryGroup[] {
    const groups = new Map<string, DatasetRecord[]>();
    for (const dataset of datasets) {
      const topDirectory = dataset.topDirectory ?? this.resolveTopDirectory(dataset.path);
      const current = groups.get(topDirectory) ?? [];
      current.push(dataset);
      groups.set(topDirectory, current);
    }
    return [...groups.entries()]
      .map(([topDirectory, groupedDatasets]) => ({
        topDirectory,
        datasets: groupedDatasets.sort((left, right) => left.name.localeCompare(right.name, "ja"))
      }))
      .sort((left, right) => left.topDirectory.localeCompare(right.topDirectory, "ja"));
  }

  private resolveIssue(
    datasets: DatasetRecord[],
    selectedDataset: DatasetRecord | null
  ): DataWorkspaceIssue | null {
    if (datasets.length === 0) {
      return {
        severity: "warning",
        title: "アーカイブが見つかりません",
        message: "session archive または export metadata がまだ読めていません。Refresh で再確認してください。"
      };
    }
    if (!selectedDataset) {
      return {
        severity: "info",
        title: "プレビュー対象を選択してください",
        message: "左側の archive explorer から 1 件選ぶと、metadata と download 操作を確認できます。"
      };
    }
    const missingFiles = selectedDataset.files?.filter((file) => !file.present) ?? [];
    if (missingFiles.length > 0) {
      return {
        severity: "warning",
        title: "一部ファイルが見つかりません",
        message: `${missingFiles.length} 件の source file が不足しています。download 前に source path を確認してください。`
      };
    }
    if (!selectedDataset.download) {
      return {
        severity: "error",
        title: "ダウンロード元が不明です",
        message: "download contract が未設定です。viewer contract と source path を確認してください。"
      };
    }
    return null;
  }

  private resolveTopDirectory(path?: string): string {
    if (!path || path.length === 0) {
      return "root";
    }
    return path.split("/")[0] ?? "root";
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
        return "live";
      default:
        return status;
    }
  }
}
