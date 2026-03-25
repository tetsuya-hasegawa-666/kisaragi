package com.reviework.app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.documentfile.provider.DocumentFile
import com.reviework.app.databinding.ActivityMainBinding
import java.io.File
import kotlin.concurrent.thread

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val controller = ReviewScreenController()
    private val extractionService = ISensoriumExtractionService()
    private var currentIndex: Int = 0
    private var sourceTreeUri: Uri? = null
    private var extractionState = ExtractionUiState()

    private val sourceTreePicker =
        registerForActivityResult(androidx.activity.result.contract.ActivityResultContracts.OpenDocumentTree()) { uri ->
            if (uri == null) {
                return@registerForActivityResult
            }
            contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
            sourceTreeUri = uri
            val label = DocumentFile.fromTreeUri(this, uri)?.name ?: uri.toString()
            extractionState =
                extractionState.copy(
                    sourceLabel = "選択元: $label",
                    detail = "抽出元を選択しました。抽出を実行すると raw と追加出力を書き出します。",
                    canExport = true,
                )
            renderExtraction()
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
            currentIndex = (currentIndex + 1).coerceAtMost(controller.lastIndex())
            render()
        }
        binding.selectSourceButton.setOnClickListener {
            sourceTreePicker.launch(null)
        }
        binding.exportButton.setOnClickListener {
            runExtraction()
        }

        render()
    }

    private fun render() {
        val state = controller.stateAt(currentIndex)
        binding.nextActionTitle.text = state.nextActionTitle
        binding.nextActionReason.text = state.nextActionReason
        binding.thinStatusText.text = controller.formatThinStatus(state)
        binding.attentionText.text = controller.formatAttentionPoints(state)
        binding.phaseBadge.text = state.thinStatus.phase.name.lowercase()
        binding.stepCounter.text = getString(R.string.step_counter, currentIndex + 1, controller.lastIndex() + 1)
        binding.prevButton.isEnabled = currentIndex > 0
        binding.nextButton.isEnabled = currentIndex < controller.lastIndex()
        renderExtraction()
    }

    private fun renderExtraction() {
        binding.extractionSourceText.text = extractionState.sourceLabel
        binding.extractionResultText.text = extractionState.detail
        binding.exportButton.isEnabled = extractionState.canExport && !extractionState.running
        binding.selectSourceButton.isEnabled = !extractionState.running
    }

    private fun runExtraction() {
        val treeUri = sourceTreeUri ?: run {
            extractionState =
                extractionState.copy(
                    detail = "抽出元が未選択です。先に iSensorium session folder を選択してください。",
                )
            renderExtraction()
            return
        }
        extractionState =
            extractionState.copy(
                running = true,
                detail = getString(R.string.extract_running),
            )
        renderExtraction()

        thread {
            val nextState =
                try {
                    val source = DocumentTreeSessionInput(this, treeUri)
                    val exportBaseDir = getExternalFilesDir("session_exports") ?: filesDir
                    val output = FileSessionOutput(exportBaseDir)
                    val result = extractionService.export(source, output)
                    ExtractionUiState(
                        sourceLabel = extractionState.sourceLabel,
                        detail =
                            buildString {
                                appendLine("抽出先: ${File(exportBaseDir, result.exportRelativeRoot).absolutePath}")
                                appendLine("診断進行可: ${result.readyForDiagnose}")
                                appendLine("空間再構成進行可: ${result.readyForSpaceReconstruction}")
                                appendLine("欠落入力: ${result.missingRequiredInputs.joinToString(", ").ifBlank { "なし" }}")
                                appendLine("空間再構成 blocker: ${result.spaceReconstructionBlockers.joinToString(", ").ifBlank { "なし" }}")
                                appendLine("充足率: ${"%.2f".format(result.completenessScore)}")
                                appendLine("pose 対応率: ${"%.2f".format(result.poseCoverageRatio)}")
                                append("pose 最近傍差分(ns): ${result.nearestPoseDeltaNs ?: "該当なし"}")
                            },
                        canExport = true,
                        running = false,
                    )
                } catch (error: Exception) {
                    ExtractionUiState(
                        sourceLabel = extractionState.sourceLabel,
                        detail = "抽出に失敗しました: ${error.message ?: error::class.java.simpleName}",
                        canExport = true,
                        running = false,
                    )
                }

            runOnUiThread {
                extractionState = nextState
                renderExtraction()
            }
        }
    }

    private data class ExtractionUiState(
        val sourceLabel: String = "選択元: 未選択",
        val detail: String = "iSensorium session folder を選択すると、raw と trajectreview 追加出力を抽出できます。",
        val canExport: Boolean = false,
        val running: Boolean = false,
    )

    private class DocumentTreeSessionInput(
        activity: AppCompatActivity,
        treeUri: Uri,
    ) : SessionInputReader {
        private val resolver = activity.contentResolver
        private val root = DocumentFile.fromTreeUri(activity, treeUri)
            ?: throw IllegalArgumentException("選択した tree を開けません。")

        override fun exists(filename: String): Boolean = root.findFile(filename)?.exists() == true

        override fun readText(filename: String): String? {
            val file = root.findFile(filename) ?: findFileRecursive(root, filename) ?: return null
            return resolver.openInputStream(file.uri)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
        }

        override fun readBytes(filename: String): ByteArray? {
            val file = root.findFile(filename) ?: findFileRecursive(root, filename) ?: return null
            return resolver.openInputStream(file.uri)?.use { it.readBytes() }
        }

        override fun listChildDirectories(): List<SessionInputReader> =
            root.listFiles()
                .filter { it.isDirectory }
                .map { child -> ChildDocumentTreeSessionInput(resolver, child) }

        private fun findFileRecursive(directory: DocumentFile, filename: String): DocumentFile? {
            directory.listFiles().forEach { child ->
                if (child.name == filename) {
                    return child
                }
                if (child.isDirectory) {
                    val found = findFileRecursive(child, filename)
                    if (found != null) {
                        return found
                    }
                }
            }
            return null
        }
    }

    private class ChildDocumentTreeSessionInput(
        private val resolver: android.content.ContentResolver,
        private val root: DocumentFile,
    ) : SessionInputReader {
        override fun exists(filename: String): Boolean = root.findFile(filename)?.exists() == true

        override fun readText(filename: String): String? {
            val file = root.findFile(filename) ?: return null
            return resolver.openInputStream(file.uri)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
        }

        override fun readBytes(filename: String): ByteArray? {
            val file = root.findFile(filename) ?: return null
            return resolver.openInputStream(file.uri)?.use { it.readBytes() }
        }
    }

    private class FileSessionOutput(
        private val baseDir: File,
    ) : SessionOutputWriter {
        override fun writeText(relativePath: String, content: String) {
            val file = File(baseDir, relativePath)
            file.parentFile?.mkdirs()
            file.writeText(content, Charsets.UTF_8)
        }

        override fun writeBytes(relativePath: String, content: ByteArray) {
            val file = File(baseDir, relativePath)
            file.parentFile?.mkdirs()
            file.writeBytes(content)
        }
    }
}
