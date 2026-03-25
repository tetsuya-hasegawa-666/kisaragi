import type { DocumentRecord } from "./DocumentRecord";
import type { DocumentRepository } from "./DocumentRepository";

export class UnlockableDocumentRepository implements DocumentRepository {
  private draftDocumentsById: Map<string, DocumentRecord> | null = null;

  public constructor(private readonly baseRepository: DocumentRepository) {}

  public listDocuments(): DocumentRecord[] {
    if (!this.draftDocumentsById) {
      return this.baseRepository.listDocuments();
    }

    return [...this.draftDocumentsById.values()].map((document) => ({
      ...document,
      tags: [...document.tags]
    }));
  }

  public saveDocument(documentId: string, body: string): DocumentRecord {
    if (!this.draftDocumentsById) {
      return this.baseRepository.saveDocument(documentId, body);
    }

    const current = this.draftDocumentsById.get(documentId);

    if (!current) {
      throw new Error(`Document '${documentId}' was not found.`);
    }

    const updated = { ...current, body };
    this.draftDocumentsById.set(documentId, updated);
    return { ...updated, tags: [...updated.tags] };
  }

  public getSourcePolicy(): string {
    if (!this.draftDocumentsById) {
      return this.baseRepository.getSourcePolicy();
    }

    return `${this.baseRepository.getSourcePolicy()} -> local draft unlock`;
  }

  public isReadOnly(): boolean {
    return this.draftDocumentsById ? false : this.baseRepository.isReadOnly();
  }

  public isLocalDraftUnlocked(): boolean {
    return this.draftDocumentsById !== null;
  }

  public unlockLocalDraft(): void {
    if (this.draftDocumentsById || !this.baseRepository.isReadOnly()) {
      return;
    }

    this.draftDocumentsById = new Map(
      this.baseRepository.listDocuments().map((document) => [
        document.id,
        { ...document, tags: [...document.tags] }
      ])
    );
  }
}
