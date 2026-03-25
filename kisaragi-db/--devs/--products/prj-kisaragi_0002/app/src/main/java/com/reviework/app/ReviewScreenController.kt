package com.reviework.app

class ReviewScreenController {

    private val demoSnapshot =
        ReviewContractSnapshot(
            intake =
                SessionIntakeReport(
                    frames = 1240,
                    usableFrames = 1092,
                    tracking = "partial",
                    mainVideoReady = true,
                    mainImuReady = true,
                    workerImuDeviceCount = 2,
                    workerVisibility = WorkerVisibility.SUFFICIENT,
                    optionalPoseReady = true,
                    optionalGnssReady = false,
                ),
            space =
                SpaceReviewSummary(
                    coordinateSystem = "arcore_local",
                    mainCameraPathReady = true,
                    colmapReadyForDensification = true,
                    spaceQuality = "0.78",
                    weakArea = "主カメラの右側通路で sparse coverage が薄い",
                ),
            trajectory =
                TrajectoryReviewSummary(
                    workerPathCount = 2,
                    trajectoryQuality = "0.64",
                    relinkDecisions =
                        listOf(
                            RelinkDecision("worker-01", 0.42, 7, 2.4, RelinkMode.RELINKED),
                            RelinkDecision("worker-02", 0.31, 11, 4.8, RelinkMode.BRIDGED),
                        ),
                    attentionPoints =
                        listOf(
                            AttentionPoint("00:42-00:49", "worker-01 の visual relink confidence が閾値未満"),
                            AttentionPoint("01:12-01:18", "主カメラ coverage が局所的に不足"),
                        ),
                    sameTimeHighlights =
                        listOf(
                            TimelineHighlight("00:45", "主カメラと worker-01 が同じ棚前に接近"),
                            TimelineHighlight("01:14", "worker-02 が主カメラの死角へ入る"),
                        ),
                ),
            artifact =
                ReviewArtifactSummary(
                    generatedBy = "Assembly",
                    viewerMode = "read-only",
                    supports3dgsControls = true,
                    supportsSameTimeHighlights = true,
                ),
        )

    private val demoStates = buildJourney(demoSnapshot)

    fun initialState(): ReviewScreenState = demoStates.first()

    fun stateAt(index: Int): ReviewScreenState = demoStates[index.coerceIn(0, demoStates.lastIndex)]

    fun lastIndex(): Int = demoStates.lastIndex

    fun diagnoseState(snapshot: ReviewContractSnapshot): ReviewScreenState {
        val missingInputs = mutableListOf<String>()
        if (!snapshot.intake.mainVideoReady) missingInputs += "主カメラ動画"
        if (!snapshot.intake.mainImuReady) missingInputs += "主カメラ IMU"
        if (snapshot.intake.workerImuDeviceCount == 0) missingInputs += "人物側 IMU"

        val issues = mutableListOf<ReviewIssue>()
        if (missingInputs.isNotEmpty()) {
            issues +=
                ReviewIssue(
                    severity = ReviewIssueSeverity.ERROR,
                    code = "missing_input",
                    message = "必須入力が不足しています: ${missingInputs.joinToString("、")}",
                    suggestedAction = "不足入力を補ってから再診断します。",
                )
        }
        if (snapshot.intake.workerVisibility != WorkerVisibility.SUFFICIENT) {
            issues +=
                ReviewIssue(
                    severity = ReviewIssueSeverity.WARNING,
                    code = "worker_visibility_insufficient",
                    message = "人物映り込みが ${snapshot.intake.workerVisibility.name.lowercase()} です。",
                    suggestedAction = "人物が十分映る区間を増やすか、再拘束前提の review として扱います。",
                )
        }
        if (!snapshot.intake.optionalPoseReady) {
            issues +=
                ReviewIssue(
                    severity = ReviewIssueSeverity.WARNING,
                    code = "missing_pose",
                    message = "camera pose が不足しています。",
                    suggestedAction = "pose 欠落区間を確認し、必要なら再入力します。",
                )
        }
        if (snapshot.intake.tracking != "good") {
            issues +=
                ReviewIssue(
                    severity = ReviewIssueSeverity.WARNING,
                    code = "low_tracking",
                    message = "tracking quality が区間によって低下しています。",
                    suggestedAction = "低追跡区間を review attention point として保持します。",
                )
        }

        return ReviewScreenState(
            nextActionTitle = if (missingInputs.isEmpty()) "診断結果を確認" else "入力条件を見直す",
            nextActionReason = "不足入力と人物映り込み、追跡品質を先に確認します。",
            thinStatus =
                ReviewThinStatus(
                    phase = ReviewPhase.DIAGNOSE,
                    dataHealth =
                        DataHealth(
                            frames = snapshot.intake.frames,
                            usable = snapshot.intake.usableFrames,
                            tracking = snapshot.intake.tracking,
                            workerVisibility = snapshot.intake.workerVisibility.name.lowercase(),
                            workerImuDevices = snapshot.intake.workerImuDeviceCount,
                        ),
                    issues = issues,
                ),
        )
    }

    fun readyState(snapshot: ReviewContractSnapshot): ReviewScreenState {
        val readyToRun =
            snapshot.intake.mainVideoReady &&
                snapshot.intake.mainImuReady &&
                snapshot.intake.workerImuDeviceCount > 0 &&
                snapshot.intake.workerVisibility != WorkerVisibility.INSUFFICIENT

        return ReviewScreenState(
            nextActionTitle = if (readyToRun) "処理を開始" else "入力条件を見直す",
            nextActionReason = if (readyToRun) "主カメラ入力と人物入力の必須条件を満たしています。" else "実行前提が不足しています。",
            thinStatus =
                ReviewThinStatus(
                    phase = ReviewPhase.DIAGNOSE,
                    pipeline =
                        PipelineStatus(
                            preprocess = if (readyToRun) PipelineState.READY else PipelineState.BLOCKED,
                            colmap = if (readyToRun) PipelineState.READY else PipelineState.BLOCKED,
                            gs3d = if (readyToRun) PipelineState.READY else PipelineState.BLOCKED,
                            trajectory = if (readyToRun) PipelineState.READY else PipelineState.BLOCKED,
                        ),
                    dataHealth =
                        DataHealth(
                            frames = snapshot.intake.frames,
                            usable = snapshot.intake.usableFrames,
                            tracking = snapshot.intake.tracking,
                            workerVisibility = snapshot.intake.workerVisibility.name.lowercase(),
                            workerImuDevices = snapshot.intake.workerImuDeviceCount,
                        ),
                    issues =
                        if (readyToRun) {
                            emptyList()
                        } else {
                            listOf(
                                ReviewIssue(
                                    severity = ReviewIssueSeverity.ERROR,
                                    code = "execute_gate_blocked",
                                    message = "主入力または人物入力の条件が不足しています。",
                                    suggestedAction = "主カメラ動画、主カメラ IMU、人物側 IMU、映り込み条件を満たします。",
                                ),
                            )
                        },
                ),
        )
    }

    fun runState(snapshot: ReviewContractSnapshot): ReviewScreenState =
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
                    dataHealth =
                        DataHealth(
                            frames = snapshot.intake.frames,
                            usable = snapshot.intake.usableFrames,
                            tracking = snapshot.intake.tracking,
                            workerVisibility = snapshot.intake.workerVisibility.name.lowercase(),
                            workerImuDevices = snapshot.intake.workerImuDeviceCount,
                        ),
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
        )

    fun colmapBlockedState(snapshot: ReviewContractSnapshot): ReviewScreenState =
        ReviewScreenState(
            nextActionTitle = "入力条件を見直す",
            nextActionReason = "主空間再構成が densification 条件を満たしていないため、3DGS を開始しません。",
            thinStatus =
                ReviewThinStatus(
                    phase = ReviewPhase.DIAGNOSE,
                    pipeline =
                        PipelineStatus(
                            preprocess = PipelineState.OK,
                            colmap = PipelineState.BLOCKED,
                            gs3d = PipelineState.BLOCKED,
                            trajectory = PipelineState.PENDING,
                        ),
                    dataHealth =
                        DataHealth(
                            frames = snapshot.intake.frames,
                            usable = snapshot.intake.usableFrames,
                            tracking = snapshot.intake.tracking,
                            workerVisibility = snapshot.intake.workerVisibility.name.lowercase(),
                            workerImuDevices = snapshot.intake.workerImuDeviceCount,
                        ),
                    issues =
                        listOf(
                            ReviewIssue(
                                severity = ReviewIssueSeverity.ERROR,
                                code = "colmap_not_ready",
                                message = "主空間再構成が densification 不可です。",
                                suggestedAction = "主カメラ coverage と tracking 条件を見直して再実行します。",
                            ),
                        ),
                ),
        )

    fun verifyState(snapshot: ReviewContractSnapshot): ReviewScreenState =
        ReviewScreenState(
            nextActionTitle = "結果を確認",
            nextActionReason = "空間品質、人物経路品質、同時刻比較の弱点を先に確認します。",
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
                    quality =
                        QualityStatus(
                            space = snapshot.space.spaceQuality,
                            trajectory = snapshot.trajectory.trajectoryQuality,
                            coordinateSystem = snapshot.space.coordinateSystem,
                            workerPathCount = snapshot.trajectory.workerPathCount,
                        ),
                    issues =
                        buildList {
                            snapshot.space.weakArea?.let {
                                add(
                                    ReviewIssue(
                                        severity = ReviewIssueSeverity.WARNING,
                                        code = "weak_area",
                                        message = it,
                                        suggestedAction = "viewer で coverage の薄い領域を確認します。",
                                    ),
                                )
                            }
                            if (snapshot.trajectory.sameTimeHighlights.isEmpty()) {
                                add(
                                    ReviewIssue(
                                        severity = ReviewIssueSeverity.WARNING,
                                        code = "same_time_missing",
                                        message = "同時刻ハイライト候補が不足しています。",
                                        suggestedAction = "人物映り込み区間を増やして再拘束点を増やします。",
                                    ),
                                )
                            }
                            if (snapshot.trajectory.relinkDecisions.any { it.mode != RelinkMode.OBSERVED }) {
                                add(
                                    ReviewIssue(
                                        severity = ReviewIssueSeverity.WARNING,
                                        code = "relink_insufficient",
                                        message = "人物経路に再拘束または橋渡し区間があります。",
                                        suggestedAction = "attention point を開いて relink 候補と不確実区間を確認します。",
                                    ),
                                )
                            }
                        },
                ),
            sameTimeHighlights = snapshot.trajectory.sameTimeHighlights,
        )

    fun reviewState(snapshot: ReviewContractSnapshot): ReviewScreenState =
        ReviewScreenState(
            nextActionTitle = "この区間を見る",
            nextActionReason = "判断が必要なのは attention point と同時刻ハイライトです。",
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
                    quality =
                        QualityStatus(
                            space = snapshot.space.spaceQuality,
                            trajectory = snapshot.trajectory.trajectoryQuality,
                            coordinateSystem = snapshot.space.coordinateSystem,
                            workerPathCount = snapshot.trajectory.workerPathCount,
                        ),
                    issues =
                        listOf(
                            ReviewIssue(
                                severity = ReviewIssueSeverity.WARNING,
                                code = "attention_required",
                                message = "attention point が ${snapshot.trajectory.attentionPoints.size} 件あります。",
                                suggestedAction = "時間範囲ごとに理由と同時刻ハイライトを確認します。",
                            ),
                        ),
                ),
            attentionPoints = snapshot.trajectory.attentionPoints,
            sameTimeHighlights = snapshot.trajectory.sameTimeHighlights,
        )

    fun artifactBoundarySummary(snapshot: ReviewContractSnapshot): String =
        "generated_by=${snapshot.artifact.generatedBy} / viewer_mode=${snapshot.artifact.viewerMode} / " +
            "3dgs_controls=${snapshot.artifact.supports3dgsControls} / " +
            "same_time_highlights=${snapshot.artifact.supportsSameTimeHighlights}"

    fun buildJourney(snapshot: ReviewContractSnapshot): List<ReviewScreenState> {
        val diagnose = diagnoseState(snapshot)
        val ready = readyState(snapshot)
        val colmap =
            if (snapshot.space.colmapReadyForDensification) {
                runState(snapshot)
            } else {
                colmapBlockedState(snapshot)
            }
        return listOf(
            ReviewScreenState(
                nextActionTitle = "データフォルダを選択",
                nextActionReason = "主カメラ動画と人物入力を取り込みます。",
                thinStatus =
                    ReviewThinStatus(
                        phase = ReviewPhase.INTAKE,
                        dataHealth =
                            DataHealth(
                                frames = snapshot.intake.frames,
                                usable = snapshot.intake.usableFrames,
                                tracking = snapshot.intake.tracking,
                                workerVisibility = snapshot.intake.workerVisibility.name.lowercase(),
                                workerImuDevices = snapshot.intake.workerImuDeviceCount,
                            ),
                    ),
            ),
            diagnose,
            ready,
            colmap,
            verifyState(snapshot),
            reviewState(snapshot),
        )
    }

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
            state.thinStatus.dataHealth.workerImuDevices?.let { append(" / worker_imu=$it") }
            state.thinStatus.dataHealth.workerVisibility?.let { append(" / worker_visibility=$it") }
            appendLine()
            if (state.thinStatus.quality.space != null || state.thinStatus.quality.trajectory != null) {
                append("quality:")
                state.thinStatus.quality.space?.let { append(" space=$it") }
                state.thinStatus.quality.trajectory?.let { append(" trajectory=$it") }
                state.thinStatus.quality.coordinateSystem?.let { append(" coordinate_system=$it") }
                state.thinStatus.quality.workerPathCount?.let { append(" worker_paths=$it") }
                appendLine()
            }
            if (state.sameTimeHighlights.isNotEmpty()) {
                appendLine("same_time_highlights: ${state.sameTimeHighlights.size}")
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
        buildString {
            if (state.attentionPoints.isEmpty()) {
                appendLine("attention: none")
            } else {
                state.attentionPoints.forEach { appendLine("${it.timeRange} | ${it.reason}") }
            }
            if (state.sameTimeHighlights.isEmpty()) {
                append("same_time: none")
            } else {
                appendLine("same_time:")
                state.sameTimeHighlights.forEach { appendLine("${it.timeRange} | ${it.description}") }
            }
        }.trim()
}
