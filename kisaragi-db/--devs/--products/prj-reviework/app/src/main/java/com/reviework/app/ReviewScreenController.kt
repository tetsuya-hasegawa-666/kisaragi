package com.reviework.app

class ReviewScreenController {

    private val demoStates: List<ReviewScreenState> =
        listOf(
            ReviewScreenState(
                nextActionTitle = "データフォルダを選択",
                nextActionReason = "まず review 対象の session package を取り込みます。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.INTAKE,
                        dataHealth = DataHealth(frames = 0),
                    ),
            ),
            ReviewScreenState(
                nextActionTitle = "診断結果を確認",
                nextActionReason = "不足データと追跡品質を先に確認します。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.DIAGNOSE,
                        dataHealth = DataHealth(frames = 1240, usable = 1092, tracking = "partial"),
                        issues =
                            listOf(
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.WARNING,
                                    code = "missing_pose",
                                    message = "camera pose が一部欠落しています。",
                                    suggestedAction = "pose 欠落区間を確認し、必要なら再入力または relink 前提で続行します。",
                                ),
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.WARNING,
                                    code = "low_tracking",
                                    message = "tracking quality が区間によって低下しています。",
                                    suggestedAction = "低追跡区間を review attention point として保持します。",
                                ),
                            ),
                    ),
            ),
            ReviewScreenState(
                nextActionTitle = "処理を開始",
                nextActionReason = "intake と diagnose の必須条件を満たしています。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.DIAGNOSE,
                        pipeline =
                            PipelineStatus(
                                preprocess = PipelineState.READY,
                                colmap = PipelineState.READY,
                                gs3d = PipelineState.READY,
                                trajectory = PipelineState.READY,
                            ),
                        dataHealth = DataHealth(frames = 1240, usable = 1092, tracking = "good"),
                    ),
            ),
            ReviewScreenState(
                nextActionTitle = "完了を待つ",
                nextActionReason = "現在ステップだけを追えば十分です。ほかの判断は不要です。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.RUN,
                        pipeline =
                            PipelineStatus(
                                preprocess = PipelineState.OK,
                                colmap = PipelineState.RUNNING,
                                gs3d = PipelineState.PENDING,
                                trajectory = PipelineState.PENDING,
                            ),
                        dataHealth = DataHealth(frames = 1240, usable = 1092, tracking = "partial"),
                        issues =
                            listOf(
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.INFO,
                                    code = "feature_match_low",
                                    message = "feature match 密度が低めです。",
                                    suggestedAction = "COLMAP 完了後に sparse coverage を確認します。",
                                ),
                            ),
                        activeStepLabel = "COLMAP / feature matching 42%",
                    ),
            ),
            ReviewScreenState(
                nextActionTitle = "結果を確認",
                nextActionReason = "space quality と trajectory quality を先に確認します。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.VERIFY,
                        pipeline =
                            PipelineStatus(
                                preprocess = PipelineState.OK,
                                colmap = PipelineState.OK,
                                gs3d = PipelineState.OK,
                                trajectory = PipelineState.OK,
                            ),
                        quality = QualityStatus(space = "0.78", trajectory = "0.64"),
                        issues =
                            listOf(
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.WARNING,
                                    code = "weak_area",
                                    message = "空間表現が弱い領域があります。",
                                    suggestedAction = "viewer で coverage の薄い領域を確認します。",
                                ),
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.WARNING,
                                    code = "relink_insufficient",
                                    message = "trajectory relink が十分ではない区間があります。",
                                    suggestedAction = "attention point を開いて relink 候補を確認します。",
                                ),
                            ),
                    ),
            ),
            ReviewScreenState(
                nextActionTitle = "この区間を見る",
                nextActionReason = "判断が必要なのは attention point だけです。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.REVIEW,
                        pipeline =
                            PipelineStatus(
                                preprocess = PipelineState.OK,
                                colmap = PipelineState.OK,
                                gs3d = PipelineState.OK,
                                trajectory = PipelineState.OK,
                            ),
                        quality = QualityStatus(space = "0.78", trajectory = "0.64"),
                        issues =
                            listOf(
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.WARNING,
                                    code = "attention_required",
                                    message = "review attention point が 2 件あります。",
                                    suggestedAction = "時間範囲ごとに理由を確認します。",
                                ),
                            ),
                    ),
                attentionPoints =
                    listOf(
                        AttentionPoint("00:42-00:49", "visual relink confidence が閾値未満"),
                        AttentionPoint("01:12-01:18", "sparse coverage が局所的に不足"),
                    ),
            ),
        )

    fun initialState(): ReviewScreenState = demoStates.first()

    fun stateAt(index: Int): ReviewScreenState = demoStates[index.coerceIn(0, demoStates.lastIndex)]

    fun lastIndex(): Int = demoStates.lastIndex

    fun formatThinStatus(state: ReviewScreenState): String =
        buildString {
            appendLine("phase: ${state.thinStatus.phase.name.lowercase()}")
            appendLine(
                "pipeline: preprocess=${state.thinStatus.pipeline.preprocess.name.lowercase()} / " +
                    "colmap=${state.thinStatus.pipeline.colmap.name.lowercase()} / " +
                    "3dgs=${state.thinStatus.pipeline.gs3d.name.lowercase()} / " +
                    "trajectory=${state.thinStatus.pipeline.trajectory.name.lowercase()}",
            )
            append("data_health: frames=${state.thinStatus.dataHealth.frames}")
            state.thinStatus.dataHealth.usable?.let { append(" / usable=$it") }
            state.thinStatus.dataHealth.tracking?.let { append(" / tracking=$it") }
            appendLine()
            if (state.thinStatus.quality.space != null || state.thinStatus.quality.trajectory != null) {
                append("quality:")
                state.thinStatus.quality.space?.let { append(" space=$it") }
                state.thinStatus.quality.trajectory?.let { append(" trajectory=$it") }
                appendLine()
            }
            state.thinStatus.activeStepLabel?.let { appendLine("current_step: $it") }
            if (state.thinStatus.issues.isEmpty()) {
                append("issues: none")
            } else {
                append(
                    "issues: " +
                        state.thinStatus.issues.joinToString(" / ") {
                            "${it.severity.name.lowercase()}:${it.code}"
                        },
                )
            }
        }.trim()

    fun formatAttentionPoints(state: ReviewScreenState): String =
        state.attentionPoints.joinToString("\n") { "${it.timeRange} | ${it.reason}" }.ifBlank { "attention: none" }
}
