package com.reviework.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.documentfile.provider.DocumentFile
import com.reviework.app.databinding.ActivityMainBinding
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val controller = ReviewScreenController()
    private val extractionService = ISensoriumExtractionService()
    private val bundleService = WorkflowBundleService()
    private val localModelingService = LocalModelingService()
    private val workflowProfile = appWorkflowProfileFromBuildConfig()
    private var currentIndex: Int = 0
    private var sourceTreeUri: Uri? = null
    private var exportTreeUri: Uri? = null
    private var bundleTreeUri: Uri? = null
    private var lastIntegratedExportUri: Uri? = null
    private var extractionState = WorkspaceUiState.idle(workflowProfile)
    private var workflowSnapshot: ReviewContractSnapshot? = null

    private val sourceTreePicker =
        registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) {
                return@registerForActivityResult
            }
            contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            sourceTreeUri = uri
            val label = DocumentFile.fromTreeUri(this, uri)?.name ?: uri.toString()
            extractionState = extractionState.withSourceSelection("取得元: $label")
            renderWorkspaceCard()
        }

    private val exportTreePicker =
        registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) {
                return@registerForActivityResult
            }
            contentResolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            )
            exportTreeUri = uri
            val label = DocumentFile.fromTreeUri(this, uri)?.name ?: uri.toString()
            extractionState = extractionState.withExportSelection("保存先: $label")
            renderWorkspaceCard()
        }

    private val bundleTreePicker =
        registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) {
                return@registerForActivityResult
            }
            contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            bundleTreeUri = uri
            val label = DocumentFile.fromTreeUri(this, uri)?.name ?: uri.toString()
            extractionState = extractionState.withSourceSelection("取得元: $label")
            renderWorkspaceCard()
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.prevButton.setOnClickListener {
            currentIndex = (currentIndex - 1).coerceAtLeast(0)
            render()
        }
        binding.nextButton.setOnClickListener {
            currentIndex = (currentIndex + 1).coerceAtMost(controller.lastIndex(workflowProfile.mode, activeSnapshot()))
            render()
        }
        binding.selectSourceButton.setOnClickListener {
            when (workflowProfile.mode) {
                AppWorkflowMode.CORRECTING, AppWorkflowMode.INTEGRATED -> sourceTreePicker.launch(null)
                AppWorkflowMode.MODELING, AppWorkflowMode.REVIEWING -> bundleTreePicker.launch(null)
            }
        }
        binding.selectOutputButton.setOnClickListener {
            when (workflowProfile.mode) {
                AppWorkflowMode.CORRECTING, AppWorkflowMode.INTEGRATED -> exportTreePicker.launch(null)
                AppWorkflowMode.MODELING, AppWorkflowMode.REVIEWING -> Unit
            }
        }
        binding.exportButton.setOnClickListener {
            when (workflowProfile.mode) {
                AppWorkflowMode.CORRECTING -> runExtraction()
                AppWorkflowMode.MODELING -> runLocalModeling()
                AppWorkflowMode.REVIEWING -> loadReviewBundle()
                AppWorkflowMode.INTEGRATED -> runExtraction()
            }
        }
        binding.secondaryActionButton.setOnClickListener {
            if (workflowProfile.mode == AppWorkflowMode.INTEGRATED) {
                runIntegratedModeling()
            }
        }

        render()
    }

    private fun activeSnapshot(): ReviewContractSnapshot = workflowSnapshot ?: controller.defaultSnapshot()

    private fun render() {
        val snapshot = activeSnapshot()
        val state = controller.stateAt(currentIndex, workflowProfile.mode, snapshot)
        binding.workflowRoleText.text = workflowProfile.roleLabel
        binding.workflowSummaryText.text = workflowProfile.scopeSummary
        binding.workflowPhaseText.text = "covered_phases: ${workflowProfile.coveredPhases}"
        binding.nextActionTitle.text = state.nextActionTitle
        binding.nextActionReason.text = state.nextActionReason
        binding.thinStatusText.text = controller.formatThinStatus(state)
        binding.attentionText.text = controller.formatAttentionPoints(state)
        binding.phaseBadge.text = state.thinStatus.phase.name.lowercase()
        binding.stepCounter.text = getString(R.string.step_counter, currentIndex + 1, controller.lastIndex(workflowProfile.mode, snapshot) + 1)
        binding.prevButton.isEnabled = currentIndex > 0
        binding.nextButton.isEnabled = currentIndex < controller.lastIndex(workflowProfile.mode, snapshot)

        if (workflowProfile.mode == AppWorkflowMode.CORRECTING) {
            binding.nextActionCard.visibility = android.view.View.GONE
            binding.statusCard.visibility = android.view.View.GONE
            binding.actionsRow.visibility = android.view.View.GONE
        } else {
            binding.nextActionCard.visibility = android.view.View.VISIBLE
            binding.statusCard.visibility = android.view.View.VISIBLE
            binding.actionsRow.visibility = android.view.View.VISIBLE
        }

        binding.extractionCard.visibility = android.view.View.VISIBLE
        renderWorkspaceCard()
    }

    private fun renderWorkspaceCard() {
        binding.extractTitleText.text = extractionState.cardTitle
        binding.extractionSourceText.text = extractionState.sourceLabel
        binding.extractionOutputText.text = extractionState.exportLabel
        binding.extractionResultText.text = extractionState.detail
        binding.selectSourceButton.text = extractionState.selectButtonLabel
        binding.selectOutputButton.visibility = if (extractionState.showOutputSelector) android.view.View.VISIBLE else android.view.View.GONE
        binding.selectOutputButton.text = extractionState.outputButtonLabel
        binding.exportButton.text = extractionState.primaryButtonLabel
        binding.exportButton.isEnabled = extractionState.canPrimary && !extractionState.running
        binding.selectSourceButton.isEnabled = !extractionState.running
        binding.selectOutputButton.isEnabled = extractionState.showOutputSelector && !extractionState.running
        if (extractionState.secondaryButtonLabel == null) {
            binding.secondaryActionButton.visibility = android.view.View.GONE
        } else {
            binding.secondaryActionButton.visibility = android.view.View.VISIBLE
            binding.secondaryActionButton.text = extractionState.secondaryButtonLabel
            binding.secondaryActionButton.isEnabled = extractionState.canSecondary && !extractionState.running
        }
    }

    private fun runExtraction() {
        val sourceUri = sourceTreeUri ?: run {
            extractionState = extractionState.withFailure("先に取得元 folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        val exportUri = exportTreeUri ?: run {
            extractionState = extractionState.withFailure("先に保存先 folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.extract_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, sourceUri)
                    val output = PrefixedSessionOutputWriter(DocumentTreeSessionOutputWriter(this, exportUri), "trajectreview_export")
                    val result = extractionService.export(source, output)
                    val exportedSessionUri =
                        DocumentFile.fromTreeUri(this, exportUri)
                            ?.findFile("trajectreview_export")
                            ?.findFile(result.sessionId)
                            ?.uri
                    if (workflowProfile.mode == AppWorkflowMode.INTEGRATED) {
                        lastIntegratedExportUri = exportedSessionUri
                    }
                    if (exportedSessionUri != null) {
                        workflowSnapshot = bundleService.loadSnapshot(DocumentTreeSessionInputReader(this, exportedSessionUri))
                        currentIndex = 0
                    }
                    WorkspaceUiState.afterExtraction(workflowProfile, extractionState.sourceLabel, extractionState.exportLabel, result, exportedSessionUri != null)
                } catch (error: Exception) {
                    extractionState.withFailure("抽出に失敗しました: ${error.message ?: error::class.java.simpleName}")
                }

            runOnUiThread {
                extractionState = nextState
                render()
            }
        }
    }

    private fun runLocalModeling() {
        val bundleUri = bundleTreeUri ?: run {
            extractionState = extractionState.withFailure("先に trajectreview_export/session_id folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.modeling_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, bundleUri)
                    val result = localModelingService.run(source, PrefixedSessionOutputWriter(DocumentTreeSessionOutputWriter(this, bundleUri), "trajectreview"))
                    workflowSnapshot = bundleService.loadSnapshot(source)
                    currentIndex = 0
                    WorkspaceUiState.afterModeling(workflowProfile, extractionState.sourceLabel, result)
                } catch (error: Exception) {
                    extractionState.withFailure("軽量 model に失敗しました: ${error.message ?: error::class.java.simpleName}")
                }

            runOnUiThread {
                extractionState = nextState
                render()
            }
        }
    }

    private fun loadReviewBundle() {
        val bundleUri = bundleTreeUri ?: run {
            extractionState = extractionState.withFailure("先に modeling 済み trajectreview folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.review_load_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, bundleUri)
                    workflowSnapshot = bundleService.loadSnapshot(source)
                    currentIndex = 0
                    val artifactSummary = controller.artifactBoundarySummary(activeSnapshot())
                    WorkspaceUiState.afterReviewLoad(workflowProfile, extractionState.sourceLabel, artifactSummary)
                } catch (error: Exception) {
                    extractionState.withFailure("結果読込に失敗しました: ${error.message ?: error::class.java.simpleName}")
                }

            runOnUiThread {
                extractionState = nextState
                render()
            }
        }
    }

    private fun runIntegratedModeling() {
        val exportUri = lastIntegratedExportUri ?: run {
            extractionState = extractionState.withFailure("先に統合 app で抽出を完了してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.modeling_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, exportUri)
                    val result = localModelingService.run(source, PrefixedSessionOutputWriter(DocumentTreeSessionOutputWriter(this, exportUri), "trajectreview"))
                    workflowSnapshot = bundleService.loadSnapshot(source)
                    currentIndex = 0
                    WorkspaceUiState.afterIntegratedModeling(workflowProfile, extractionState.sourceLabel, extractionState.exportLabel, result)
                } catch (error: Exception) {
                    extractionState.withFailure("統合 modeling に失敗しました: ${error.message ?: error::class.java.simpleName}")
                }

            runOnUiThread {
                extractionState = nextState
                render()
            }
        }
    }

    private data class WorkspaceUiState(
        val cardTitle: String,
        val sourceLabel: String,
        val exportLabel: String,
        val detail: String,
        val selectButtonLabel: String,
        val outputButtonLabel: String,
        val primaryButtonLabel: String,
        val secondaryButtonLabel: String?,
        val showOutputSelector: Boolean,
        val canPrimary: Boolean,
        val canSecondary: Boolean,
        val running: Boolean,
    ) {
        fun withSourceSelection(label: String): WorkspaceUiState {
            val next = copy(sourceLabel = label)
            return next.updatePrimaryAvailability()
        }

        fun withExportSelection(label: String): WorkspaceUiState {
            val next = copy(exportLabel = label)
            return next.updatePrimaryAvailability()
        }

        fun withRunning(detail: String): WorkspaceUiState =
            copy(
                detail = detail,
                running = true,
                canPrimary = false,
                canSecondary = false,
            )

        fun withFailure(detail: String): WorkspaceUiState =
            copy(
                detail = detail,
                running = false,
            ).updatePrimaryAvailability()

        private fun updatePrimaryAvailability(): WorkspaceUiState {
            val sourceReady = sourceLabel != "取得元: 未選択"
            val exportReady = !showOutputSelector || exportLabel != "保存先: 未選択"
            return copy(
                canPrimary = sourceReady && exportReady,
                canSecondary = canSecondary && !running,
            )
        }

        companion object {
            fun idle(profile: AppWorkflowProfile): WorkspaceUiState =
                when (profile.mode) {
                    AppWorkflowMode.CORRECTING ->
                        WorkspaceUiState(
                            cardTitle = "取得と補正",
                            sourceLabel = "取得元: 未選択",
                            exportLabel = "保存先: 未選択",
                            detail = "取得元 folder と保存先 folder を選ぶと、補正前確認付きの抽出を実行できます。",
                            selectButtonLabel = "取得元を選択",
                            outputButtonLabel = "保存先を選択",
                            primaryButtonLabel = "抽出を実行",
                            secondaryButtonLabel = null,
                            showOutputSelector = true,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                    AppWorkflowMode.MODELING ->
                        WorkspaceUiState(
                            cardTitle = "modeling 実データ",
                            sourceLabel = "取得元: 未選択",
                            exportLabel = "保存先: modeling 結果を同じ folder に保存",
                            detail = "trajectreview_export/session_id folder を選択すると、local sample model と Colab request を生成します。",
                            selectButtonLabel = "bundle を選択",
                            outputButtonLabel = "",
                            primaryButtonLabel = "軽量 model を実行",
                            secondaryButtonLabel = null,
                            showOutputSelector = false,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                    AppWorkflowMode.REVIEWING ->
                        WorkspaceUiState(
                            cardTitle = "reviewing 実データ",
                            sourceLabel = "取得元: 未選択",
                            exportLabel = "保存先: 不要",
                            detail = "modeling 済み trajectreview folder を選択すると、実 bundle から review 状態を読込みます。",
                            selectButtonLabel = "結果 folder を選択",
                            outputButtonLabel = "",
                            primaryButtonLabel = "結果を読込",
                            secondaryButtonLabel = null,
                            showOutputSelector = false,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                    AppWorkflowMode.INTEGRATED ->
                        WorkspaceUiState(
                            cardTitle = "統合 workflow 実データ",
                            sourceLabel = "取得元: 未選択",
                            exportLabel = "保存先: 未選択",
                            detail = "取得元 folder と保存先 folder を選び、抽出の後に同じ app で軽量 model まで進めます。",
                            selectButtonLabel = "取得元を選択",
                            outputButtonLabel = "保存先を選択",
                            primaryButtonLabel = "抽出を実行",
                            secondaryButtonLabel = "軽量 model を実行",
                            showOutputSelector = true,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                }

            fun afterExtraction(
                profile: AppWorkflowProfile,
                sourceLabel: String,
                exportLabel: String,
                result: SessionExportResult,
                integratedModelReady: Boolean,
            ): WorkspaceUiState =
                idle(profile).copy(
                    sourceLabel = sourceLabel,
                    exportLabel = exportLabel,
                    detail =
                        buildString {
                            appendLine("抽出結果: trajectreview_export/${result.sessionId}")
                            appendLine("診断進行可: ${result.readyForDiagnose}")
                            appendLine("空間再構成進行可: ${result.readyForSpaceReconstruction}")
                            appendLine("欠落入力: ${result.missingRequiredInputs.joinToString(", ").ifBlank { "なし" }}")
                            appendLine("空間再構成 blocker: ${result.spaceReconstructionBlockers.joinToString(", ").ifBlank { "なし" }}")
                            appendLine("充足率: ${"%.2f".format(result.completenessScore)}")
                            append("pose 対応率: ${"%.2f".format(result.poseCoverageRatio)}")
                        },
                    canPrimary = true,
                    canSecondary = integratedModelReady && profile.mode == AppWorkflowMode.INTEGRATED,
                )

            fun afterModeling(
                profile: AppWorkflowProfile,
                sourceLabel: String,
                result: LocalModelingResult,
            ): WorkspaceUiState =
                idle(profile).copy(
                    sourceLabel = sourceLabel,
                    detail =
                        buildString {
                            appendLine("modeling 結果: reviewReady=${result.reviewReady}")
                            appendLine("spaceQuality: ${result.spaceQuality}")
                            appendLine("trajectoryQuality: ${result.trajectoryQuality}")
                            appendLine("blocker: ${result.blockers.joinToString(", ").ifBlank { "なし" }}")
                            append("出力: ${result.outputFiles.joinToString(", ")}")
                        },
                    canPrimary = true,
                )

            fun afterIntegratedModeling(
                profile: AppWorkflowProfile,
                sourceLabel: String,
                exportLabel: String,
                result: LocalModelingResult,
            ): WorkspaceUiState =
                afterModeling(profile, sourceLabel, result).copy(
                    exportLabel = exportLabel,
                    canSecondary = true,
                    secondaryButtonLabel = "軽量 model を実行",
                )

            fun afterReviewLoad(
                profile: AppWorkflowProfile,
                sourceLabel: String,
                artifactSummary: String,
            ): WorkspaceUiState =
                idle(profile).copy(
                    sourceLabel = sourceLabel,
                    detail = "review bundle 読込完了: $artifactSummary",
                    canPrimary = true,
                )
        }
    }
}
