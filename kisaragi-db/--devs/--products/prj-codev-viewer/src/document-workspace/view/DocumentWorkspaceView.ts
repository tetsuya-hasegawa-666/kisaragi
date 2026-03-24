import type {
  DocumentTreeNode,
  DocumentWorkspaceState
} from "../controller/DocumentWorkspaceController";

type PaneId = "left" | "right";

export interface DashboardWorkspaceViewState {
  left: DocumentWorkspaceState;
  right: DocumentWorkspaceState;
}

export class DocumentWorkspaceView {
  public constructor(private readonly rootElement: HTMLElement) {}

  public render(state: DashboardWorkspaceViewState): void {
    this.rootElement.innerHTML = `
      <main class="selection-stage" data-role="selection-stage">
        ${this.renderPane("left", state.left)}
        ${this.renderPane("right", state.right)}
      </main>
    `;
  }

  private renderPane(paneId: PaneId, state: DocumentWorkspaceState): string {
    if (state.selectedDocument) {
      return this.renderDetailPane(paneId, state);
    }
    return this.renderSelectionPane(paneId, state);
  }

  private renderDetailPane(paneId: PaneId, state: DocumentWorkspaceState): string {
    const selectedDocument = state.selectedDocument;
    if (!selectedDocument) {
      return this.renderSelectionPane(paneId, state);
    }
    const isMarkdown = selectedDocument.path.toLocaleLowerCase("ja").endsWith(".md");
    return `
      <section class="selection-pane story-detail-pane" data-role="selection-pane" data-pane="${paneId}">
        <div class="detail-strip" data-role="detail-strip">
          <div class="detail-strip-tree" data-role="detail-strip-tree">
            ${state.selectedTrail
              .map(
                (node, index) => `
                  <div class="detail-strip-row" data-role="detail-strip-row">
                    <span class="detail-strip-depth" aria-hidden="true">${"&nbsp;".repeat(index * 3)}</span>
                    <span class="detail-strip-kind" aria-hidden="true">${
                      node.kind === "directory" ? "&#9662; &#128193;" : "&#8226;"
                    }</span>
                    <span class="detail-strip-label">${this.escapeHtml(node.label)}</span>
                  </div>
                `
              )
              .join("")}
          </div>
          <div class="detail-strip-actions" data-role="detail-strip-actions">
            <button class="tree-action-button detail-back-button" data-role="back-to-search" type="button">
              &#26908;&#32034;&#12395;&#25147;&#12427;
            </button>
          </div>
        </div>
        <article
          class="document-reading-surface ${isMarkdown ? "markdown-body" : "plain-text-body"}"
          data-role="document-reading-surface"
        >
          <div data-role="document-reading-body">
            ${isMarkdown ? this.renderMarkdown(selectedDocument.body) : this.renderPlainText(selectedDocument.body)}
          </div>
        </article>
      </section>
    `;
  }

  private renderSelectionPane(paneId: PaneId, state: DocumentWorkspaceState): string {
    const searchQuery = state.searchQuery ?? "";
    const stickyTrail = state.selectedTrail;
    const stickyTrailMarkup =
      stickyTrail.length > 0
        ? stickyTrail
            .map(
              (node) => `
                <span class="selection-trail-chip" data-role="selection-trail-chip">
                  ${this.escapeHtml(node.label)}
                </span>
              `
            )
            .join('<span class="selection-trail-separator" aria-hidden="true">/</span>')
        : `<span class="selection-trail-placeholder" data-role="selection-trail-placeholder"></span>`;
    return `
      <section class="selection-pane" data-role="selection-pane" data-pane="${paneId}">
        <div class="selection-header" data-role="selection-header">
          <div class="tree-actions" data-role="tree-actions">
            <button class="tree-action-button" data-role="collapse-all" type="button">
              &#20840;&#38281;
            </button>
            <button class="tree-action-button" data-role="expand-all" type="button">
              &#20840;&#38283;
            </button>
            <input
              class="expand-depth-input"
              data-role="expand-depth-input"
              type="number"
              min="1"
              step="1"
              value="${this.escapeAttribute(String(state.expandDepth))}"
              aria-label="expand depth"
            />
          </div>
          <div class="profile-tabs" data-role="profile-tabs">
            ${state.availableProfiles
              .map(
                (profile) => `
                  <button
                    class="profile-tab ${profile.profileId === state.activeProfileId ? "is-active" : ""}"
                    data-role="profile-tab"
                    data-profile-id="${this.escapeAttribute(profile.profileId)}"
                    type="button"
                  >
                    ${this.escapeHtml(profile.profileLabel)}
                  </button>
                `
              )
              .join("")}
          </div>
        </div>
        <div class="search-bar-shell">
          <input
            class="search-input"
            data-role="search-input"
            type="text"
            value="${this.escapeAttribute(searchQuery)}"
            placeholder="&#12487;&#12451;&#12524;&#12463;&#12488;&#12522;&#21517; / &#12501;&#12449;&#12452;&#12523;&#21517;&#12434;&#26908;&#32034;"
            autocomplete="off"
            spellcheck="false"
          />
        </div>
        <div class="selection-trail-shell" data-role="selection-trail-shell">
          ${stickyTrailMarkup}
        </div>
        <div class="tree-panel" data-role="tree-panel">
          ${state.tree
            .map((node, index) =>
              this.renderNode(
                state,
                node,
                0,
                new Set(state.expandedPaths),
                [],
                index === state.tree.length - 1
              )
            )
            .join("")}
        </div>
      </section>
    `;
  }

  private renderNode(
    state: DocumentWorkspaceState,
    node: DocumentTreeNode,
    depth: number,
    expandedPaths: Set<string>,
    ancestorLastFlags: boolean[],
    isLast: boolean
  ): string {
    const connectorMarkup = this.renderConnectors(ancestorLastFlags, isLast);
    const isSelected = state.selectedPath === node.path;
    const isMatched = (state.matchedPaths ?? []).includes(node.path);
    const labelMarkup = this.renderHighlightedLabel(node.label, state.searchQuery ?? "");

    if (node.kind === "file") {
      return `
        <div
          class="tree-row tree-file-row ${isSelected ? "is-selected" : ""} ${isMatched ? "is-matched" : ""}"
          data-role="tree-file"
          data-path="${this.escapeAttribute(node.path)}"
          aria-pressed="${isSelected ? "true" : "false"}"
          style="--depth:${depth}"
          tabindex="0"
        >
          <span class="tree-connectors" aria-hidden="true">${connectorMarkup}</span>
          <span class="tree-toggle-spacer" aria-hidden="true"></span>
          <span class="tree-icon tree-file-icon" aria-hidden="true">&#8226;</span>
          <span class="tree-label">${labelMarkup}</span>
        </div>
      `;
    }

    const isExpanded = expandedPaths.has(node.path);
    return `
      <div class="tree-group" data-role="tree-group">
        <div
          class="tree-row tree-folder-row ${isSelected ? "is-selected" : ""} ${isMatched ? "is-matched" : ""}"
          data-role="tree-toggle"
          data-path="${this.escapeAttribute(node.path)}"
          aria-expanded="${isExpanded ? "true" : "false"}"
          aria-pressed="${isSelected ? "true" : "false"}"
          style="--depth:${depth}"
          tabindex="0"
        >
          <span class="tree-connectors" aria-hidden="true">${connectorMarkup}</span>
          <span class="tree-toggle-glyph" aria-hidden="true">${isExpanded ? "&#9662;" : "&#9656;"}</span>
          <span class="tree-icon tree-folder-icon" aria-hidden="true">&#128193;</span>
          <span class="tree-label">${labelMarkup}</span>
        </div>
        ${
          isExpanded
            ? `<div class="tree-children">${node.children
                .map((child, index) =>
                  this.renderNode(
                    state,
                    child,
                    depth + 1,
                    expandedPaths,
                    [...ancestorLastFlags, isLast],
                    index === node.children.length - 1
                  )
                )
                .join("")}</div>`
            : ""
        }
      </div>
    `;
  }

  private renderConnectors(ancestorLastFlags: boolean[], isLast: boolean): string {
    const prefix = ancestorLastFlags.map((ancestorIsLast) => (ancestorIsLast ? "   " : "\u2502  ")).join("");
    const joint = isLast ? "\u2514\u2500 " : "\u251C\u2500 ";
    return this.escapeHtml(`${prefix}${joint}`);
  }

  private renderHighlightedLabel(label: string, searchQuery: string): string {
    const normalizedQuery = searchQuery.trim();
    if (normalizedQuery.length === 0) {
      return this.escapeHtml(label);
    }

    const lowerLabel = label.toLocaleLowerCase("ja");
    const lowerQuery = normalizedQuery.toLocaleLowerCase("ja");
    let cursor = 0;
    let markup = "";

    while (cursor < label.length) {
      const index = lowerLabel.indexOf(lowerQuery, cursor);
      if (index === -1) {
        markup += this.escapeHtml(label.slice(cursor));
        break;
      }
      markup += this.escapeHtml(label.slice(cursor, index));
      markup += `<mark class="tree-match">${this.escapeHtml(label.slice(index, index + normalizedQuery.length))}</mark>`;
      cursor = index + normalizedQuery.length;
    }

    return markup;
  }

  private renderMarkdown(body: string): string {
    const lines = body.replaceAll("\r\n", "\n").split("\n");
    const chunks: string[] = [];
    let paragraphLines: string[] = [];
    let listItems: string[] = [];
    let codeLines: string[] = [];
    let inCodeBlock = false;

    const flushParagraph = (): void => {
      if (paragraphLines.length === 0) {
        return;
      }
      chunks.push(`<p>${this.renderInlineMarkdown(paragraphLines.join(" "))}</p>`);
      paragraphLines = [];
    };

    const flushList = (): void => {
      if (listItems.length === 0) {
        return;
      }
      chunks.push(`<ul>${listItems.map((item) => `<li>${item}</li>`).join("")}</ul>`);
      listItems = [];
    };

    const flushCode = (): void => {
      if (codeLines.length === 0) {
        return;
      }
      chunks.push(`<pre><code>${this.escapeHtml(codeLines.join("\n"))}</code></pre>`);
      codeLines = [];
    };

    for (const line of lines) {
      if (line.startsWith("```")) {
        flushParagraph();
        flushList();
        if (inCodeBlock) {
          flushCode();
          inCodeBlock = false;
        } else {
          inCodeBlock = true;
        }
        continue;
      }
      if (inCodeBlock) {
        codeLines.push(line);
        continue;
      }
      const headingMatch = /^(#{1,6})\s+(.+)$/.exec(line);
      if (headingMatch) {
        flushParagraph();
        flushList();
        const level = headingMatch[1].length;
        chunks.push(`<h${level}>${this.renderInlineMarkdown(headingMatch[2])}</h${level}>`);
        continue;
      }
      const listMatch = /^[-*]\s+(.+)$/.exec(line);
      if (listMatch) {
        flushParagraph();
        listItems.push(this.renderInlineMarkdown(listMatch[1]));
        continue;
      }
      if (line.trim().length === 0) {
        flushParagraph();
        flushList();
        continue;
      }
      paragraphLines.push(line.trim());
    }

    flushParagraph();
    flushList();
    flushCode();

    return chunks.join("");
  }

  private renderPlainText(body: string): string {
    return `<pre class="plain-text-pre">${this.escapeHtml(body)}</pre>`;
  }

  private renderInlineMarkdown(text: string): string {
    const escaped = this.escapeHtml(text);
    return escaped
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  }

  private escapeHtml(value: string): string {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  private escapeAttribute(value: string): string {
    return this.escapeHtml(value);
  }
}
