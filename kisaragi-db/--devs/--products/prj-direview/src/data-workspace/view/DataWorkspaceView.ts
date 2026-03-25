import type { DatasetRecord } from "../model/DatasetRecord";
import type { DataWorkspaceState, DatasetStatusSummary } from "../controller/DataWorkspaceController";

export class DataWorkspaceView {
  public constructor(private readonly rootElement: HTMLElement) {}

  public render(state: DataWorkspaceState): void {
    const maxRecordCount = Math.max(...state.summary.byStatus.map((item) => item.recordCount), 1);
    const chartMarkup = state.summary.byStatus
      .map((item) => this.renderChartBar(item, maxRecordCount))
      .join("");
    const resultMarkup = state.results
      .map(
        (result) => `
          <li data-role="result-row">
            <strong>${this.escapeHtml(result.datasetId)}</strong> ${this.escapeHtml(result.summary)}
          </li>
        `
      )
      .join("");
    const directoryMarkup = state.directoryGroups
      .map(
        (group) => `
          <section class="archive-group" data-role="archive-group">
            <div class="archive-group-header">
              <p class="eyebrow">Top Directory</p>
              <h3>${this.escapeHtml(group.topDirectory)}</h3>
              <p>${group.datasets.length} 件</p>
            </div>
            <div class="archive-group-list">
              ${group.datasets
                .map((dataset) =>
                  this.renderDatasetRow(
                    dataset,
                    state.isReadOnly,
                    state.selectedDatasets.some((selected) => selected.id === dataset.id),
                    dataset.id === state.selectedDataset?.id
                  )
                )
                .join("")}
            </div>
          </section>
        `
      )
      .join("");
    const selectedPreview = state.selectedDataset
      ? this.renderSelectedDataset(state.selectedDataset, state)
      : `
        <section class="status-chart">
          <p class="eyebrow">Preview</p>
          <p data-role="empty-preview">archive explorer から 1 件選ぶと、session metadata と download action を確認できます。</p>
        </section>
      `;
    const issueMarkup = state.issue
      ? `
        <div class="status-chart issue-panel issue-${state.issue.severity}" data-role="data-issue">
          <p class="eyebrow">${this.escapeHtml(state.issue.title)}</p>
          <p>${this.escapeHtml(state.issue.message)}</p>
        </div>
      `
      : "";
    const sourceGuidance = state.isReadOnly
      ? `
        <div class="unlock-guidance" data-role="unlock-data-guidance">
          <p><strong>読み取り方針:</strong> local draft を開くと、現状の archive 一覧をブラウザ内コピーとして編集できます。</p>
          <p><strong>注意:</strong> 元の source は変更されません。safe apply を進めるまで local draft のみです。</p>
          <button class="document-item is-selected" data-role="unlock-data-editing" type="button">local draft を開く</button>
        </div>
      `
      : `
        <div class="unlock-guidance">
          <p>現在は local draft 上で更新できます。元の source は safe apply まで変わりません。</p>
        </div>
      `;

    this.rootElement.innerHTML = `
      <div class="dashboard-shell" data-role="data-layout">
        <section class="workspace-panel data-explorer-panel" data-role="data-explorer-panel">
          <div class="workspace-panel-frame">
            <div class="workspace-panel-header">
              <div class="section-heading">
                <p class="eyebrow">Archive Explorer</p>
                <h2>session archive と export metadata</h2>
                <p>top directory ごとに compact に並べ、選択した archive を右側で確認します。</p>
                <p class="result-count">読み込み方針: ${this.escapeHtml(state.sourcePolicy)}</p>
                <p class="result-count" data-role="data-mode-note">${state.isReadOnly ? "Read-only / 読み取り専用" : "Editable / local draft 可"}</p>
              </div>
              ${sourceGuidance}
              <div class="metric-grid">
                <article class="metric-card">
                  <p class="eyebrow">アーカイブ件数</p>
                  <strong data-role="total-datasets">${state.summary.totalDatasets}</strong>
                </article>
                <article class="metric-card">
                  <p class="eyebrow">ファイル総数</p>
                  <strong data-role="total-records">${state.summary.totalRecords}</strong>
                </article>
              </div>
              <div class="status-chart">${chartMarkup}</div>
            </div>
            <div class="workspace-panel-body">
              <div class="archive-tree-scroll">${directoryMarkup}</div>
            </div>
          </div>
        </section>
        <section class="preview-panel data-preview-panel">
          ${issueMarkup}
          ${selectedPreview}
          <section class="status-chart">
            <p class="eyebrow">最新結果</p>
            <ul class="result-list">${resultMarkup || "<li>No result yet.</li>"}</ul>
          </section>
          <section class="status-chart">
            <p class="eyebrow">Data Consultation</p>
            <p data-role="data-bundle-count">選択済み ${state.selectedDatasets.length} 件</p>
            <ul data-role="data-bundle-list" class="result-list">
              ${state.selectedDatasets
                .map(
                  (dataset) =>
                    `<li>${this.escapeHtml(dataset.name)} <span>${this.escapeHtml(this.getStatusLabel(dataset.status))}</span></li>`
                )
                .join("")}
            </ul>
            <div class="capability-note" data-role="consultation-capabilities">
              <p class="eyebrow">consultation で返す内容</p>
              <ul>
                <li><strong>Summary</strong> bundle の要点</li>
                <li><strong>Evidence</strong> status と file basis の要約</li>
                <li><strong>Next Action</strong> 次に確認すべき観点</li>
              </ul>
            </div>
            <form data-role="data-consultation-form">
              <textarea
                class="document-editor"
                data-role="data-consultation-focus-input"
                name="data-consultation-focus"
                placeholder="確認したい観点を入力"
              >${this.escapeHtml(state.consultation.focusPrompt)}</textarea>
              <button class="document-item is-selected" data-role="run-data-consultation" type="submit">consultation を実行</button>
            </form>
            ${
              state.consultation.lastResponse
                ? `
                  <div class="document-body" data-role="data-consultation-response">
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
        </section>
      </div>
    `;
  }

  private renderSelectedDataset(dataset: DatasetRecord, state: DataWorkspaceState): string {
    const downloadMarkup = dataset.download
      ? `
        <a
          class="document-item is-selected download-link"
          data-role="download-dataset"
          href="${this.escapeAttribute(this.buildDownloadUrl(dataset.download.relativePath))}"
          download="${this.escapeAttribute(dataset.download.fileName)}"
        >
          1 ボタンでダウンロード
        </a>
      `
      : `
        <button class="document-item" data-role="download-dataset-disabled" type="button" disabled>
          ダウンロード元が未設定です
        </button>
      `;
    const fileMarkup = (dataset.files ?? [])
      .map(
        (file) => `
          <li data-role="archive-file-row">
            <strong>${this.escapeHtml(file.name)}</strong>
            <span>${this.escapeHtml(file.relativePath)}</span>
            <span>${file.present ? "available" : "missing"}</span>
          </li>
        `
      )
      .join("");
    const statusMarkup = [
      dataset.recordingMode ? `recordingMode: ${dataset.recordingMode}` : null,
      dataset.requestedRoute ? `requestedRoute: ${dataset.requestedRoute}` : null,
      dataset.activeRoute ? `activeRoute: ${dataset.activeRoute}` : null,
      dataset.startedAt ? `startedAt: ${dataset.startedAt}` : null,
      dataset.finalizedAt ? `finalizedAt: ${dataset.finalizedAt}` : null
    ]
      .filter((value): value is string => value !== null)
      .map((value) => `<li>${this.escapeHtml(value)}</li>`)
      .join("");

    return `
      <section class="status-chart archive-preview" data-role="archive-preview">
        <p class="eyebrow">Preview</p>
        <h2 data-role="selected-dataset-title">${this.escapeHtml(dataset.name)}</h2>
        <p>${this.escapeHtml(dataset.path ?? dataset.id)}</p>
        <p><strong>status:</strong> ${this.escapeHtml(this.getStatusLabel(dataset.status))}</p>
        ${dataset.statusMessage ? `<p><strong>detail:</strong> ${this.escapeHtml(dataset.statusMessage)}</p>` : ""}
        ${downloadMarkup}
        <div class="archive-preview-grid">
          <div class="directory-group">
            <p class="eyebrow">Session Contract</p>
            <ul class="result-list" data-role="archive-session-fields">${statusMarkup || "<li>session metadata はありません。</li>"}</ul>
          </div>
          <div class="directory-group">
            <p class="eyebrow">Files</p>
            <ul class="result-list" data-role="archive-file-list">${fileMarkup || "<li>file list はありません。</li>"}</ul>
          </div>
        </div>
        <div class="document-body" data-role="archive-preview-text">${this.escapeHtml(dataset.previewText ?? "preview text はありません。")}</div>
        ${
          !state.isReadOnly
            ? `
              <div class="editor-actions">
                <button class="document-item" data-role="save-dataset" data-dataset-id="${this.escapeAttribute(dataset.id)}" type="button">状態を保存</button>
              </div>
            `
            : ""
        }
      </section>
    `;
  }

  private renderDatasetRow(
    dataset: DatasetRecord,
    isReadOnly: boolean,
    isInBundle: boolean,
    isSelected: boolean
  ): string {
    const statusControl = isReadOnly
      ? `<span>${this.escapeHtml(this.getStatusLabel(dataset.status))}</span>`
      : `
        <select data-role="dataset-status" data-dataset-id="${this.escapeAttribute(dataset.id)}">
          ${["draft", "ready", "review", "live"]
            .map(
              (status) =>
                `<option value="${status}" ${
                  dataset.status === status ? "selected" : ""
                }>${this.getStatusLabel(status)}</option>`
            )
            .join("")}
        </select>
      `;
    return `
      <div class="archive-row" data-role="dataset-row">
        <button
          class="document-item ${isSelected ? "is-selected" : ""}"
          data-role="dataset-item"
          data-dataset-id="${this.escapeAttribute(dataset.id)}"
          type="button"
        >
          <strong>${this.escapeHtml(dataset.name)}</strong>
          <p>${this.escapeHtml(dataset.path ?? dataset.id)}</p>
        </button>
        <div class="archive-row-side">
          ${statusControl}
          <button
            class="tree-toggle ${isInBundle ? "is-selected" : ""}"
            data-role="toggle-dataset-bundle"
            data-dataset-id="${this.escapeAttribute(dataset.id)}"
            type="button"
          >
            ${isInBundle ? "相談対象から外す" : "相談対象に追加"}
          </button>
        </div>
      </div>
    `;
  }

  private renderChartBar(item: DatasetStatusSummary, maxRecordCount: number): string {
    const ratio = Math.round((item.recordCount / maxRecordCount) * 100);

    return `
      <div class="chart-row">
        <span>${this.escapeHtml(this.getStatusLabel(item.status))}</span>
        <div class="chart-track">
          <span
            class="chart-bar"
            data-role="chart-bar"
            data-status="${this.escapeHtml(item.status)}"
            style="width: ${ratio}%"
          ></span>
        </div>
        <strong>${item.recordCount}</strong>
      </div>
    `;
  }

  private buildDownloadUrl(relativePath: string): string {
    return `/api/dashboard/download?path=${encodeURIComponent(relativePath)}`;
  }

  private getStatusLabel(status: string): string {
    switch (status) {
      case "draft":
        return "下書き";
      case "ready":
        return "準備完了";
      case "review":
        return "レビュー中";
      case "live":
        return "live";
      default:
        return status;
    }
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
