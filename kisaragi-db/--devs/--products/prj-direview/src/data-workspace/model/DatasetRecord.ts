export interface DatasetFileRecord {
  name: string;
  relativePath: string;
  sizeBytes: number;
  present: boolean;
}

export interface DatasetDownloadRecord {
  kind: "file" | "directory";
  relativePath: string;
  fileName: string;
}

export interface DatasetRecord {
  id: string;
  name: string;
  category: string;
  recordCount: number;
  status: string;
  updatedAt: string;
  path?: string;
  topDirectory?: string;
  sessionId?: string;
  recordingMode?: string;
  requestedRoute?: string;
  activeRoute?: string;
  startedAt?: string;
  finalizedAt?: string;
  statusMessage?: string;
  files?: DatasetFileRecord[];
  previewText?: string;
  download?: DatasetDownloadRecord;
}
