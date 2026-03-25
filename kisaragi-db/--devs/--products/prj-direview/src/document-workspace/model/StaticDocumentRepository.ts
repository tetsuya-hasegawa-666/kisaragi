import type { DocumentRecord } from "./DocumentRecord";
import type { DocumentRepository } from "./DocumentRepository";

export class StaticDocumentRepository implements DocumentRepository {
  private documentsById: Map<string, DocumentRecord>;
  private sourcePolicy: string;
  private readOnly: boolean;

  public constructor(
    documents: DocumentRecord[],
    options?: { sourcePolicy?: string; readOnly?: boolean }
  ) {
    this.documentsById = new Map(documents.map((document) => [document.id, { ...document }]));
    this.sourcePolicy = options?.sourcePolicy ?? "Seed bootstrap + in-app save";
    this.readOnly = options?.readOnly ?? false;
  }

  public listDocuments(): DocumentRecord[] {
    return [...this.documentsById.values()].map((document) => ({ ...document, tags: [...document.tags] }));
  }

  public saveDocument(documentId: string, body: string): DocumentRecord {
    if (this.readOnly) {
      throw new Error("この文書ソースは読み取り専用です。");
    }

    const current = this.documentsById.get(documentId);

    if (!current) {
      throw new Error(`Document '${documentId}' was not found.`);
    }

    const updated = { ...current, body };
    this.documentsById.set(documentId, updated);
    return { ...updated, tags: [...updated.tags] };
  }

  public getSourcePolicy(): string {
    return this.sourcePolicy;
  }

  public isReadOnly(): boolean {
    return this.readOnly;
  }

  public replaceDocuments(
    documents: DocumentRecord[],
    options: { sourcePolicy: string; readOnly: boolean }
  ): void {
    this.documentsById = new Map(documents.map((document) => [document.id, { ...document }]));
    this.sourcePolicy = options.sourcePolicy;
    this.readOnly = options.readOnly;
  }
}
