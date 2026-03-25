import type { DocumentRecord } from "../../document-workspace/model/DocumentRecord";

export interface DashboardSourceProfile {
  profileId: string;
  label: string;
  projectRoot: string;
  sourcePolicy: string;
  documents: DocumentRecord[];
}

export interface DashboardBootstrap {
  mode: "seed" | "live";
  profiles: DashboardSourceProfile[];
  readOnly: boolean;
  sourceSignature: string;
  loadedAt: string;
}

interface LiveDashboardResponse {
  profiles: DashboardSourceProfile[];
  readOnly: boolean;
  sourceSignature: string;
}

export async function loadDashboardBootstrap(
  documentSeed: Array<
    Omit<DocumentRecord, "profileId" | "profileLabel" | "nodeKind"> &
      Partial<Pick<DocumentRecord, "profileId" | "profileLabel" | "nodeKind">>
  >
): Promise<DashboardBootstrap> {
  if (typeof window === "undefined") {
    return createSeedBootstrap(documentSeed);
  }

  try {
    const response = await fetch("/api/dashboard/live-state");

    if (!response.ok) {
      throw new Error(`Live state endpoint returned ${response.status}.`);
    }

    const payload = (await response.json()) as LiveDashboardResponse;

    return {
      mode: "live",
      profiles: payload.profiles,
      readOnly: payload.readOnly,
      sourceSignature: payload.sourceSignature,
      loadedAt: new Date().toISOString()
    };
  } catch {
    return createSeedBootstrap(documentSeed);
  }
}

function createSeedBootstrap(
  documentSeed: Array<
    Omit<DocumentRecord, "profileId" | "profileLabel" | "nodeKind"> &
      Partial<Pick<DocumentRecord, "profileId" | "profileLabel" | "nodeKind">>
  >
): DashboardBootstrap {
  const seedDocuments = documentSeed.map((document) => ({
    ...document,
    profileId: document.profileId ?? "seed",
    profileLabel: document.profileLabel ?? "seed basis",
    nodeKind: document.nodeKind ?? "file"
  }));

  return {
    mode: "seed",
    profiles: [
      {
        profileId: "seed",
        label: "seed basis",
        projectRoot: "seed",
        sourcePolicy: "seed read-only",
        documents: seedDocuments
      }
    ],
    readOnly: true,
    sourceSignature: `seed:${seedDocuments.length}`,
    loadedAt: new Date().toISOString()
  };
}
