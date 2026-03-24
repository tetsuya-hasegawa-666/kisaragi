import type { CodeTargetRecord } from "./CodeTargetRecord";

export interface CodeTargetRepository {
  listTargets(): CodeTargetRecord[];
  getSourcePolicy(): string;
}
