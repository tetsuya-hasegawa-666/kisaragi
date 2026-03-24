import type { CodeTargetRepository } from "../model/CodeTargetRepository";

export interface CodeConsultationResponse {
  summary: string;
  evidence: string[];
  nextAction: string;
}

export interface CodeConsultationState {
  selectedTargetIds: string[];
  focusPrompt: string;
  lastResponse: CodeConsultationResponse | null;
}

export interface CodeWorkspaceState {
  targets: Array<{
    id: string;
    title: string;
    path: string;
    description: string;
    kind?: string;
    updatedAt?: string;
  }>;
  policyNote: string;
  sourcePolicy: string;
  selectedTargets: Array<{
    id: string;
    title: string;
    path: string;
    description: string;
    kind?: string;
    updatedAt?: string;
  }>;
  consultation: CodeConsultationState;
}

export class CodeWorkspaceController {
  public constructor(private readonly repository: CodeTargetRepository) {}

  public createState(consultationState?: Partial<CodeConsultationState>): CodeWorkspaceState {
    const targets = this.repository.listTargets();
    const selectedTargetIds =
      consultationState?.selectedTargetIds?.filter((targetId) =>
        targets.some((target) => target.id === targetId)
      ) ?? (targets[0] ? [targets[0].id] : []);

    return {
      targets,
      policyNote: "読み取り専用です。実行、attach、保存はできません。",
      sourcePolicy: this.repository.getSourcePolicy(),
      selectedTargets: targets.filter((target) => selectedTargetIds.includes(target.id)),
      consultation: {
        selectedTargetIds,
        focusPrompt: consultationState?.focusPrompt ?? "",
        lastResponse: consultationState?.lastResponse ?? null
      }
    };
  }

  public toggleTargetSelection(
    targetId: string,
    consultationState?: Partial<CodeConsultationState>
  ): CodeWorkspaceState {
    const state = this.createState(consultationState);
    const nextSelectedTargetIds = state.consultation.selectedTargetIds.includes(targetId)
      ? state.consultation.selectedTargetIds.filter((selectedId) => selectedId !== targetId)
      : [...state.consultation.selectedTargetIds, targetId];

    return this.createState({
      ...state.consultation,
      selectedTargetIds: nextSelectedTargetIds,
      lastResponse: null
    });
  }

  public updateConsultationFocus(
    focusPrompt: string,
    consultationState?: Partial<CodeConsultationState>
  ): CodeWorkspaceState {
    const state = this.createState(consultationState);
    return this.createState({
      ...state.consultation,
      focusPrompt
    });
  }

  public consultTargets(
    consultationState?: Partial<CodeConsultationState>
  ): CodeWorkspaceState {
    const state = this.createState(consultationState);
    const focusPrompt = state.consultation.focusPrompt.trim();

    return this.createState({
      ...state.consultation,
      lastResponse: {
        summary:
          state.selectedTargets.length > 0
            ? `${state.selectedTargets.length} 件の code target を read-only consultation material として固定しました。`
            : "相談対象の code target を 1 件以上選択してください。",
        evidence: state.selectedTargets.map((target) => `${target.title} (${target.path})`),
        nextAction:
          focusPrompt.length > 0
            ? `focus: ${focusPrompt}`
            : "phase gate 内で確認したい論点を補足する"
      }
    });
  }
}
