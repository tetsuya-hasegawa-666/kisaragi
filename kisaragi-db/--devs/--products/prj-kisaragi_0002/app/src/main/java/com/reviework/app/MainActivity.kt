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
    private var workspaceUri: Uri? = null
    private var lastIntegratedExportUri: Uri? = null
    private var extractionState = WorkspaceUiState.idle(workflowProfile)
    private var workflowSnapshot: ReviewContractSnapshot? = null

    private val treePicker =
        registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) {
                return@registerForActivityResult
            }
            contentResolver.takePersistableUriPermission(
                uri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            )
            workspaceUri = uri
            val label = DocumentFile.fromTreeUri(this, uri)?.name ?: uri.toString()
            extractionState = extractionState.withSelection("選択先: $label")
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
            treePicker.launch(null)
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
            when (workflowProfile.mode) {
                AppWorkflowMode.INTEGRATED -> runIntegratedModeling()
                AppWorkflowMode.CORRECTING, AppWorkflowMode.MODELING, AppWorkflowMode.REVIEWING -> Unit
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
        binding.extractionCard.visibility = android.view.View.VISIBLE
        renderWorkspaceCard()
    }

    private fun renderWorkspaceCard() {
        binding.extractTitleText.text = extractionState.cardTitle
        binding.extractionSourceText.text = extractionState.sourceLabel
        binding.extractionResultText.text = extractionState.detail
        binding.selectSourceButton.text = extractionState.selectButtonLabel
        binding.exportButton.text = extractionState.primaryButtonLabel
        binding.exportButton.isEnabled = extractionState.canPrimary && !extractionState.running
        binding.selectSourceButton.isEnabled = !extractionState.running
        if (extractionState.secondaryButtonLabel == null) {
            binding.secondaryActionButton.visibility = android.view.View.GONE
        } else {
            binding.secondaryActionButton.visibility = android.view.View.VISIBLE
            binding.secondaryActionButton.text = extractionState.secondaryButtonLabel
            binding.secondaryActionButton.isEnabled = extractionState.canSecondary && !extractionState.running
        }
    }

    private fun runExtraction() {
        val treeUri = workspaceUri ?: run {
            extractionState = extractionState.withFailure("先に iSensorium session folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.extract_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, treeUri)
                    val output = PrefixedSessionOutputWriter(DocumentTreeSessionOutputWriter(this, treeUri), "trajectreview_export")
                    val result = extractionService.export(source, output)
                    val exportedSessionUri = DocumentFile.fromTreeUri(this, treeUri)?.findFile("trajectreview_export")?.findFile(result.sessionId)?.uri
                    if (workflowProfile.mode == AppWorkflowMode.INTEGRATED) {
                        lastIntegratedExportUri = exportedSessionUri
                    }
                    if (exportedSessionUri != null) {
                        workflowSnapshot = bundleService.loadSnapshot(DocumentTreeSessionInputReader(this, exportedSessionUri))
                        currentIndex = 0
                    }
                    WorkspaceUiState.afterExtraction(workflowProfile, extractionState.sourceLabel, result, exportedSessionUri != null)
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
        val treeUri = workspaceUri ?: run {
            extractionState = extractionState.withFailure("先に trajectreview_export/session_id folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.modeling_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, treeUri)
                    val result = localModelingService.run(source, PrefixedSessionOutputWriter(DocumentTreeSessionOutputWriter(this, treeUri), "trajectreview"))
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
        val treeUri = workspaceUri ?: run {
            extractionState = extractionState.withFailure("先に modeling 済み trajectreview folder を選択してください。")
            renderWorkspaceCard()
            return
        }
        extractionState = extractionState.withRunning(getString(R.string.review_load_running))
        renderWorkspaceCard()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInputReader(this, treeUri)
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
                    WorkspaceUiState.afterIntegratedModeling(workflowProfile, extractionState.sourceLabel, result)
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
        val detail: String,
        val selectButtonLabel: String,
        val primaryButtonLabel: String,
        val secondaryButtonLabel: String?,
        val canPrimary: Boolean,
        val canSecondary: Boolean,
        val running: Boolean,
    ) {
        fun withSelection(label: String): WorkspaceUiState =
            copy(
                sourceLabel = label,
                detail =
                    when (primaryButtonLabel) {
                        "抽出を実行" -> "抽出を実行すると、選択した tree 配下の trajectreview_export/ に raw と派生 bundle を出力します。"
                        "軽量 model を実行" -> "選択した trajectreview bundle から local sample model と Colab handoff request を生成します。"
                        else -> "選択した modeling 結果から実データ review 状態を読込みます。"
                    },
                canPrimary = true,
            )

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
                canPrimary = sourceLabel != "選択先: 未選択",
            )

        companion object {
            fun idle(profile: AppWorkflowProfile): WorkspaceUiState =
                when (profile.mode) {
                    AppWorkflowMode.CORRECTING ->
                        WorkspaceUiState(
                            cardTitle = "correcting 実データ",
                            sourceLabel = "選択先: 未選択",
                            detail = "iSensorium session folder を選択すると、trajectreview_export/ に raw と派生 bundle を出力します。",
                            selectButtonLabel = "入力 tree を選択",
                            primaryButtonLabel = "抽出を実行",
                            secondaryButtonLabel = null,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                    AppWorkflowMode.MODELING ->
                        WorkspaceUiState(
                            cardTitle = "modeling 実データ",
                            sourceLabel = "選択先: 未選択",
                            detail = "trajectreview_export/session_id folder を選択すると、local sample model と Colab request を生成します。",
                            selectButtonLabel = "bundle を選択",
                            primaryButtonLabel = "軽量 model を実行",
                            secondaryButtonLabel = null,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                    AppWorkflowMode.REVIEWING ->
                        WorkspaceUiState(
                            cardTitle = "reviewing 実データ",
                            sourceLabel = "選択先: 未選択",
                            detail = "modeling 済み trajectreview folder を選択すると、実 bundle から review 状態を読込みます。",
                            selectButtonLabel = "結果 folder を選択",
                            primaryButtonLabel = "結果を読込",
                            secondaryButtonLabel = null,
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                    AppWorkflowMode.INTEGRATED ->
                        WorkspaceUiState(
                            cardTitle = "統合 workflow 実データ",
                            sourceLabel = "選択先: 未選択",
                            detail = "iSensorium session folder を選択し、抽出後に同じ app で軽量 model まで進めます。",
                            selectButtonLabel = "入力 tree を選択",
                            primaryButtonLabel = "抽出を実行",
                            secondaryButtonLabel = "軽量 model を実行",
                            canPrimary = false,
                            canSecondary = false,
                            running = false,
                        )
                }

            fun afterExtraction(
                profile: AppWorkflowProfile,
                sourceLabel: String,
                result: SessionExportResult,
                integratedModelReady: Boolean,
            ): WorkspaceUiState =
                idle(profile).copy(
                    sourceLabel = sourceLabel,
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
                result: LocalModelingResult,
            ): WorkspaceUiState =
                afterModeling(profile, sourceLabel, result).copy(canSecondary = true, secondaryButtonLabel = "軽量 model を実行")

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
