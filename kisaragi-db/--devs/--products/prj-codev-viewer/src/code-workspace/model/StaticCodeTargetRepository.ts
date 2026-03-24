import type { CodeTargetRecord } from "./CodeTargetRecord";
import type { CodeTargetRepository } from "./CodeTargetRepository";

export class StaticCodeTargetRepository implements CodeTargetRepository {
  private targetsById: Map<string, CodeTargetRecord>;
  private sourcePolicyValue: string;

  public constructor(
    targets: CodeTargetRecord[],
    sourcePolicy = "seed read-only browse"
  ) {
    this.targetsById = new Map(targets.map((target) => [target.id, { ...target }]));
    this.sourcePolicyValue = sourcePolicy;
  }

  public listTargets(): CodeTargetRecord[] {
    return [...this.targetsById.values()].map((target) => ({ ...target }));
  }

  public getSourcePolicy(): string {
    return this.sourcePolicyValue;
  }

  public replaceTargets(targets: CodeTargetRecord[], sourcePolicy: string): void {
    this.targetsById = new Map(targets.map((target) => [target.id, { ...target }]));
    this.sourcePolicyValue = sourcePolicy;
  }
}
