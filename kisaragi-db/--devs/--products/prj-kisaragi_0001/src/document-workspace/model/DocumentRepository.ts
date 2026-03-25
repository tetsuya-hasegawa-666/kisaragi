import type { DocumentRecord } from "./DocumentRecord";

export interface DocumentRepository {
  listDocuments(): DocumentRecord[];
  saveDocument(documentId: string, body: string): DocumentRecord;
  getSourcePolicy(): string;
  isReadOnly(): boolean;
}
