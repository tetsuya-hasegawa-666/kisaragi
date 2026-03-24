import type { CodeWorkspaceState } from "../controller/CodeWorkspaceController";

export class CodeWorkspaceView {
  public constructor(private readonly rootElement: HTMLElement) {}

  public render(state: CodeWorkspaceState): void {
    const listMarkup = state.targets
      .map(
        (target) => `
          <article class="code-target">
            <p class="eyebrow">${this.escapeHtml(target.kind ?? "code")}</p>
            <h3>${this.escapeHtml(target.title)}</h3>
            <p>${this.escapeHtml(target.path)}</p>
            <p>${this.escapeHtml(target.description)}</p>
            ${
              target.updatedAt
                ? `<p class="document-path">更新日時: ${this.escapeHtml(target.updatedAt)}</p>`
                : ""
            }
            <button
              class="document-item ${state.selectedTargets.some((selected) => selected.id === target.id) ? "is-selected" : ""}"
              data-role="toggle-code-bundle"
              data-target-id="${this.escapeHtml(target.id)}"
              type="button"
            >
              ${state.selectedTargets.some((selected) => selected.id === target.id) ? "相談対象から外す" : "相談対象に追加"}
            </button>
          </article>
        `
      )
      .join("");

    this.rootElement.innerHTML = `
      <section class="data-workspace">
        <div class="section-heading">
          <p class="eyebrow">コード</p>
          <h2>読み取り専用の確認対象</h2>
          <p class="result-count">読み込みポリシー: ${this.escapeHtml(state.sourcePolicy)}</p>
          <p data-role="code-policy">${this.escapeHtml(state.policyNote)}</p>
        </div>
        <section class="status-chart">
          <p class="eyebrow">Code Consultation</p>
          <p data-role="code-bundle-count">選択 ${state.selectedTargets.length} 件</p>
          <ul class="result-list" data-role="code-bundle-list">
            ${state.selectedTargets
              .map((target) => `<li>${this.escapeHtml(target.title)} <span>${this.escapeHtml(target.path)}</span></li>`)
              .join("")}
          </ul>
          <form data-role="code-consultation-form">
            <textarea
              class="document-editor"
              data-role="code-consultation-focus-input"
              name="code-consultation-focus"
              placeholder="read-only で確認したい論点を入力"
            >${this.escapeHtml(state.consultation.focusPrompt)}</textarea>
            <button class="document-item is-selected" data-role="run-code-consultation" type="submit">相談する</button>
          </form>
          ${
            state.consultation.lastResponse
              ? `
                <div class="document-body" data-role="code-consultation-response">
                  <p><strong>Summary</strong> ${this.escapeHtml(state.consultation.lastResponse.summary)}</p>
                  <ul>
                    ${state.consultation.lastResponse.evidence
                      .map((evidence) => `<li>${this.escapeHtml(evidence)}</li>`)
                      .join("")}
                  </ul>
                  <p><strong>Next Action</strong> ${this.escapeHtml(state.consultation.lastResponse.nextAction)}</p>
                </div>
              `
              : ""
          }
        </section>
        <div class="document-list">${listMarkup || "<p>表示できる code/script はありません。</p>"}</div>
      </section>
    `;
  }

  private escapeHtml(value: string): string {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
}
