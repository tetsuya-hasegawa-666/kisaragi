export type ConsultationWorkspaceId = "document" | "data" | "code";
export type ConsultationApprovalState =
  | "consultation-only"
  | "phase-gated-read-only"
  | "approval-pending"
  | "approved"
  | "cancelled";

export interface ConsultationBundleItem {
  id: string;
  kind: "document" | "dataset" | "code";
  label: string;
  path: string;
}

export interface ConsultationResponseField {
  key: "summary" | "evidence" | "next_action";
  label: string;
  description: string;
}

export interface ConsultationSessionState {
  storyId: string;
  workspaceId: ConsultationWorkspaceId;
  storySummary: string;
  touchpoints: string[];
  bundle: ConsultationBundleItem[];
  bundleSourcePolicy: string;
  responseFields: ConsultationResponseField[];
  approvalState: ConsultationApprovalState;
  approvalGuidance: string;
  behaviorLeaves: string[];
}

interface ConsultationSessionInput {
  workspaceId: ConsultationWorkspaceId;
  sourcePolicy: string;
  bundle: ConsultationBundleItem[];
}

export function createConsultationSession(
  input: ConsultationSessionInput
): ConsultationSessionState {
  const responseFields: ConsultationResponseField[] = [
    {
      key: "summary",
      label: "Summary",
      description: "相談対象に対する短い結論"
    },
    {
      key: "evidence",
      label: "Evidence",
      description: "bundle に含めた材料から引いた根拠"
    },
    {
      key: "next_action",
      label: "Next Action",
      description: "次に user が選べる action"
    }
  ];

  switch (input.workspaceId) {
    case "document":
      return {
        storyId: "document-consultation",
        workspaceId: input.workspaceId,
        storySummary: "利用者が文書 bundle を選び、Codex へ相談し、根拠つきの提案を受け取る。",
        touchpoints: [
          "文書を選ぶ",
          "相談の焦点を言語化する",
          "根拠つきの応答を受け取る",
          "apply 前に approval state を確認する"
        ],
        bundle: input.bundle,
        bundleSourcePolicy: input.sourcePolicy,
        responseFields,
        approvalState: "consultation-only",
        approvalGuidance: "この line では consultation までを扱い、apply は approval line へ送る。",
        behaviorLeaves: [
          "document-bundle-fixed",
          "document-response-schema-fixed",
          "document-approval-state-visible"
        ]
      };
    case "data":
      return {
        storyId: "data-consultation",
        workspaceId: input.workspaceId,
        storySummary: "利用者が dataset bundle を選び、異常や次 action を相談できる。",
        touchpoints: [
          "dataset を選ぶ",
          "観点を入力する",
          "summary / anomaly / next action を受け取る",
          "apply 前に approval state を確認する"
        ],
        bundle: input.bundle,
        bundleSourcePolicy: input.sourcePolicy,
        responseFields,
        approvalState: "consultation-only",
        approvalGuidance: "この line では dataset 変更を行わず、相談結果だけを返す。",
        behaviorLeaves: [
          "data-bundle-fixed",
          "data-response-schema-fixed",
          "data-approval-state-visible"
        ]
      };
    case "code":
      return {
        storyId: "code-consultation",
        workspaceId: input.workspaceId,
        storySummary: "利用者が code target を相談材料として選び、phase gate 内で read-only に確認できる。",
        touchpoints: [
          "code target を選ぶ",
          "相談材料として参照する",
          "read-only の範囲で応答を受け取る",
          "phase gate を超える要求は保留する"
        ],
        bundle: input.bundle,
        bundleSourcePolicy: input.sourcePolicy,
        responseFields,
        approvalState: "phase-gated-read-only",
        approvalGuidance: "コードは consultation material のみであり、実行、attach、apply は許可しない。",
        behaviorLeaves: [
          "code-bundle-fixed",
          "code-response-schema-fixed",
          "code-phase-gate-visible"
        ]
      };
  }
}
