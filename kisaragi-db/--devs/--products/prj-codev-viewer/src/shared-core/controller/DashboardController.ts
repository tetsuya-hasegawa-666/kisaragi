import { DocumentWorkspaceController } from "../../document-workspace/controller/DocumentWorkspaceController";
import type {
  DocumentTreeNode,
  DocumentWorkspaceState
} from "../../document-workspace/controller/DocumentWorkspaceController";
import type { DocumentRepository } from "../../document-workspace/model/DocumentRepository";
import { DocumentWorkspaceView } from "../../document-workspace/view/DocumentWorkspaceView";

type PaneId = "left" | "right";

interface PaneControllerState {
  activeProfileId?: string;
  expandedPaths: Set<string>;
  hasHydratedExpansion: boolean;
  selectedPath?: string;
  searchQuery: string;
  searchSelectionStart?: number;
  searchSelectionEnd?: number;
  isComposingSearch: boolean;
  expandDepth: number;
}

export class DashboardController {
  private static readonly STORAGE_KEY_PREFIX = "codev-viewer.v2.pane.";
  private readonly documentController: DocumentWorkspaceController;
  private static readonly DEFAULT_EXPAND_DEPTH = 1;
  private readonly panes: Record<PaneId, PaneControllerState> = {
    left: this.createPaneState("left"),
    right: this.createPaneState("right")
  };

  public constructor(
    private readonly rootElement: HTMLElement,
    documentRepository: DocumentRepository
  ) {
    this.documentController = new DocumentWorkspaceController(documentRepository);
  }

  public start(): void {
    this.render();
    this.rootElement.addEventListener("click", (event) => this.handleClick(event));
    this.rootElement.addEventListener("input", (event) => this.handleInput(event));
    this.rootElement.addEventListener("compositionstart", (event) => this.handleCompositionStart(event));
    this.rootElement.addEventListener("compositionend", (event) => this.handleCompositionEnd(event));
  }

  private createPaneState(paneId: PaneId): PaneControllerState {
    const hydrated = this.loadPaneStateFromStorage(paneId);
    if (hydrated) {
      return hydrated;
    }
    return {
      expandedPaths: new Set<string>(),
      hasHydratedExpansion: false,
      searchQuery: "",
      isComposingSearch: false,
      expandDepth: DashboardController.DEFAULT_EXPAND_DEPTH
    };
  }

  private handleClick(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) {
      return;
    }
    const paneId = this.resolvePaneId(target);
    if (!paneId) {
      return;
    }
    const pane = this.panes[paneId];

    const expandAllButton = target.closest<HTMLElement>("[data-role='expand-all']");
    if (expandAllButton) {
      this.expandAll(paneId);
      this.persistPaneState(paneId);
      this.render();
      return;
    }
    const collapseAllButton = target.closest<HTMLElement>("[data-role='collapse-all']");
    if (collapseAllButton) {
      this.collapseAll(paneId);
      this.persistPaneState(paneId);
      this.render();
      return;
    }
    const backToSearchButton = target.closest<HTMLElement>("[data-role='back-to-search']");
    if (backToSearchButton) {
      pane.selectedPath = undefined;
      this.persistPaneState(paneId);
      this.render();
      return;
    }
    const profileTab = target.closest<HTMLElement>("[data-role='profile-tab']");
    if (profileTab?.dataset.profileId) {
      pane.activeProfileId = profileTab.dataset.profileId;
      pane.expandedPaths.clear();
      pane.hasHydratedExpansion = false;
      pane.selectedPath = undefined;
      this.persistPaneState(paneId);
      this.render();
      return;
    }

    const file = target.closest<HTMLElement>("[data-role='tree-file']");
    if (file?.dataset.path) {
      pane.selectedPath = file.dataset.path;
      this.persistPaneState(paneId);
      this.render();
      return;
    }

    const toggle = target.closest<HTMLElement>("[data-role='tree-toggle']");
    if (!toggle?.dataset.path) {
      return;
    }
    pane.selectedPath = toggle.dataset.path;
    if (pane.expandedPaths.has(toggle.dataset.path)) {
      pane.expandedPaths.delete(toggle.dataset.path);
    } else {
      pane.expandedPaths.add(toggle.dataset.path);
    }
    this.persistPaneState(paneId);
    this.render();
  }

  private handleInput(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) {
      return;
    }
    const paneId = this.resolvePaneId(target);
    if (!paneId) {
      return;
    }
    const pane = this.panes[paneId];

    if (target.dataset.role === "expand-depth-input") {
      const parsed = Number.parseInt(target.value, 10);
      pane.expandDepth = Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
      pane.expandedPaths = new Set(
        this.collectDirectoryPaths(
          this.documentController.createSelectionState(
            pane.activeProfileId,
            [],
            pane.selectedPath,
            pane.searchQuery,
            pane.expandDepth
          ).tree,
          pane.expandDepth - 1
        )
      );
      pane.hasHydratedExpansion = true;
      this.persistPaneState(paneId);
      this.render();
      return;
    }
    if (target.dataset.role !== "search-input") {
      return;
    }
    pane.searchQuery = target.value;
    pane.searchSelectionStart = target.selectionStart ?? pane.searchQuery.length;
    pane.searchSelectionEnd = target.selectionEnd ?? pane.searchQuery.length;
    if (pane.isComposingSearch) {
      return;
    }
    this.persistPaneState(paneId);
    this.render();
  }

  private handleCompositionStart(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || target.dataset.role !== "search-input") {
      return;
    }
    const paneId = this.resolvePaneId(target);
    if (!paneId) {
      return;
    }
    this.panes[paneId].isComposingSearch = true;
  }

  private handleCompositionEnd(event: Event): void {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || target.dataset.role !== "search-input") {
      return;
    }
    const paneId = this.resolvePaneId(target);
    if (!paneId) {
      return;
    }
    const pane = this.panes[paneId];
    pane.isComposingSearch = false;
    pane.searchQuery = target.value;
    pane.searchSelectionStart = target.selectionStart ?? pane.searchQuery.length;
    pane.searchSelectionEnd = target.selectionEnd ?? pane.searchQuery.length;
    this.persistPaneState(paneId);
    this.render();
  }

  private render(): void {
    this.rootElement.innerHTML = `<div data-role="workspace-content"></div>`;

    const content = this.rootElement.querySelector<HTMLElement>("[data-role='workspace-content']");
    if (!content) {
      throw new Error("Workspace content host was not found.");
    }

    const leftState = this.buildPaneWorkspaceState("left");
    const rightState = this.buildPaneWorkspaceState("right");
    new DocumentWorkspaceView(content).render({ left: leftState, right: rightState });
    this.restoreSearchInputSelection(content, "left");
    this.restoreSearchInputSelection(content, "right");
  }

  private buildPaneWorkspaceState(paneId: PaneId): DocumentWorkspaceState {
    const pane = this.panes[paneId];
    const state = this.documentController.createSelectionState(
      pane.activeProfileId,
      [...pane.expandedPaths],
      pane.selectedPath,
      pane.searchQuery,
      pane.expandDepth
    );
    pane.activeProfileId = state.activeProfileId;
    if (!pane.hasHydratedExpansion) {
      this.collectDirectoryPaths(state.tree, pane.expandDepth - 1).forEach((path) =>
        pane.expandedPaths.add(path)
      );
      state.expandedPaths = [...pane.expandedPaths];
      pane.hasHydratedExpansion = true;
    }
    this.persistPaneState(paneId);
    return state;
  }

  private expandAll(paneId: PaneId): void {
    const pane = this.panes[paneId];
    const state = this.documentController.createSelectionState(
      pane.activeProfileId,
      [],
      pane.selectedPath,
      pane.searchQuery,
      pane.expandDepth
    );
    pane.activeProfileId = state.activeProfileId;
    pane.expandedPaths = new Set(this.collectDirectoryPaths(state.tree, pane.expandDepth - 1));
    pane.hasHydratedExpansion = true;
  }

  private collapseAll(paneId: PaneId): void {
    const pane = this.panes[paneId];
    const state = this.documentController.createSelectionState(
      pane.activeProfileId,
      [],
      pane.selectedPath,
      pane.searchQuery,
      1
    );
    pane.activeProfileId = state.activeProfileId;
    pane.expandedPaths = new Set(this.collectDirectoryPaths(state.tree, 0));
    pane.hasHydratedExpansion = true;
  }

  private collectDirectoryPaths(
    tree: DocumentTreeNode[],
    maxDepth: number,
    currentDepth = 0
  ): string[] {
    if (currentDepth >= maxDepth) {
      return [];
    }
    const paths: string[] = [];
    for (const node of tree) {
      if (node.kind !== "directory") {
        continue;
      }
      paths.push(
        node.path,
        ...this.collectDirectoryPaths(node.children, maxDepth, currentDepth + 1)
      );
    }
    return paths;
  }

  private restoreSearchInputSelection(content: HTMLElement, paneId: PaneId): void {
    const searchInput = content.querySelector<HTMLInputElement>(
      `[data-pane='${paneId}'] [data-role='search-input']`
    );
    const pane = this.panes[paneId];
    if (!searchInput) {
      return;
    }
    if (document.activeElement instanceof HTMLInputElement && document.activeElement === searchInput) {
      return;
    }
    if (pane.searchSelectionStart === undefined || pane.searchSelectionEnd === undefined) {
      return;
    }
    searchInput.focus();
    searchInput.setSelectionRange(pane.searchSelectionStart, pane.searchSelectionEnd);
  }

  private resolvePaneId(target: HTMLElement): PaneId | null {
    const paneElement = target.closest<HTMLElement>("[data-pane]");
    if (!paneElement) {
      return null;
    }
    return paneElement.dataset.pane === "right" ? "right" : "left";
  }

  private loadPaneStateFromStorage(paneId: PaneId): PaneControllerState | null {
    if (typeof window === "undefined") {
      return null;
    }
    const raw = window.sessionStorage.getItem(`${DashboardController.STORAGE_KEY_PREFIX}${paneId}`);
    if (!raw) {
      return null;
    }
    try {
      const parsed = JSON.parse(raw) as Partial<{
        activeProfileId: string;
        expandedPaths: string[];
        hasHydratedExpansion: boolean;
        selectedPath: string;
        searchQuery: string;
        expandDepth: number;
      }>;
      return {
        activeProfileId: parsed.activeProfileId,
        expandedPaths: new Set(parsed.expandedPaths ?? []),
        hasHydratedExpansion: parsed.hasHydratedExpansion ?? false,
        selectedPath: parsed.selectedPath,
        searchQuery: parsed.searchQuery ?? "",
        isComposingSearch: false,
        expandDepth:
          typeof parsed.expandDepth === "number" && Number.isFinite(parsed.expandDepth) && parsed.expandDepth > 0
            ? parsed.expandDepth
            : DashboardController.DEFAULT_EXPAND_DEPTH
      };
    } catch {
      return null;
    }
  }

  private persistPaneState(paneId: PaneId): void {
    if (typeof window === "undefined") {
      return;
    }
    const pane = this.panes[paneId];
    const payload = {
      activeProfileId: pane.activeProfileId,
      expandedPaths: [...pane.expandedPaths],
      hasHydratedExpansion: pane.hasHydratedExpansion,
      selectedPath: pane.selectedPath,
      searchQuery: pane.searchQuery,
      expandDepth: pane.expandDepth
    };
    window.sessionStorage.setItem(
      `${DashboardController.STORAGE_KEY_PREFIX}${paneId}`,
      JSON.stringify(payload)
    );
  }
}
