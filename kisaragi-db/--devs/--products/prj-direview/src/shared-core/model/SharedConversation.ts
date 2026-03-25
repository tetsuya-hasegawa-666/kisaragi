import type { ConsultationApprovalState, ConsultationBundleItem } from "./ConsultationSession";

export type ProposalAction = "keep" | "discard" | "task" | "apply-request";
export type ApplyState = "idle" | "preview" | "approval-pending" | "approved" | "cancelled";

export interface ConversationEntry {
  id: string;
  workspaceId: "document" | "data" | "code";
  prompt: string;
  bundle: ConsultationBundleItem[];
  summary: string;
  evidence: string[];
  nextAction: string;
  approvalState: ConsultationApprovalState;
  proposalAction: ProposalAction | null;
  applyState: ApplyState;
}

export interface SharedConversationState {
  currentPrompt: string;
  currentBundle: ConsultationBundleItem[];
  currentSummary: string | null;
  currentApprovalState: ConsultationApprovalState | null;
  currentProposalAction: ProposalAction | null;
  applyState: ApplyState;
  history: ConversationEntry[];
}

export function createEmptyConversationState(): SharedConversationState {
  return {
    currentPrompt: "",
    currentBundle: [],
    currentSummary: null,
    currentApprovalState: null,
    currentProposalAction: null,
    applyState: "idle",
    history: []
  };
}

export function appendConversationEntry(
  state: SharedConversationState,
  entry: Omit<ConversationEntry, "id" | "proposalAction" | "applyState">
): SharedConversationState {
  const nextEntry: ConversationEntry = {
    id: `entry-${state.history.length + 1}`,
    ...entry,
    proposalAction: null,
    applyState: "idle"
  };

  return {
    currentPrompt: entry.prompt,
    currentBundle: entry.bundle,
    currentSummary: entry.summary,
    currentApprovalState: entry.approvalState,
    currentProposalAction: null,
    applyState: "idle",
    history: [nextEntry, ...state.history].slice(0, 10)
  };
}

export function applyProposalAction(
  state: SharedConversationState,
  action: ProposalAction
): SharedConversationState {
  const [current, ...rest] = state.history;
  if (!current) {
    return state;
  }

  const applyState =
    action === "apply-request"
      ? current.approvalState === "phase-gated-read-only"
        ? "idle"
        : "preview"
      : state.applyState;

  return {
    ...state,
    currentProposalAction: action,
    applyState,
    history: [
      {
        ...current,
        proposalAction: action,
        applyState
      },
      ...rest
    ]
  };
}

export function updateApplyState(
  state: SharedConversationState,
  applyState: ApplyState,
  approvalState: ConsultationApprovalState
): SharedConversationState {
  const [current, ...rest] = state.history;
  if (!current) {
    return state;
  }

  return {
    ...state,
    applyState,
    currentApprovalState: approvalState,
    history: [
      {
        ...current,
        applyState,
        approvalState
      },
      ...rest
    ]
  };
}
