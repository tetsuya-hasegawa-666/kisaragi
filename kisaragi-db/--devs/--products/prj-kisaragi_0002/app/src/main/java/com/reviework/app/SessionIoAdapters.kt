package com.reviework.app

import android.content.ContentResolver
import android.content.Context
import android.net.Uri
import androidx.documentfile.provider.DocumentFile
import java.io.File

class DocumentTreeSessionInputReader(
    context: Context,
    treeUri: Uri,
) : SessionInputReader {
    private val resolver = context.contentResolver
    private val root =
        DocumentFile.fromTreeUri(context, treeUri)
            ?: throw IllegalArgumentException("選択した tree を開けません。")

    override fun exists(filename: String): Boolean = findFileRecursive(root, filename) != null

    override fun readText(filename: String): String? {
        val file = findFileRecursive(root, filename) ?: return null
        return resolver.openInputStream(file.uri)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
    }

    override fun readBytes(filename: String): ByteArray? {
        val file = findFileRecursive(root, filename) ?: return null
        return resolver.openInputStream(file.uri)?.use { it.readBytes() }
    }

    override fun listChildDirectories(): List<SessionInputReader> =
        root.listFiles()
            .filter { it.isDirectory }
            .map { child -> NestedDocumentTreeSessionInputReader(resolver, child) }

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

private class NestedDocumentTreeSessionInputReader(
    private val resolver: ContentResolver,
    private val root: DocumentFile,
) : SessionInputReader {
    override fun exists(filename: String): Boolean = findFileRecursive(root, filename) != null

    override fun readText(filename: String): String? {
        val file = findFileRecursive(root, filename) ?: return null
        return resolver.openInputStream(file.uri)?.bufferedReader(Charsets.UTF_8)?.use { it.readText() }
    }

    override fun readBytes(filename: String): ByteArray? {
        val file = findFileRecursive(root, filename) ?: return null
        return resolver.openInputStream(file.uri)?.use { it.readBytes() }
    }

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

class FileSessionOutputWriter(
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

class DocumentTreeSessionOutputWriter(
    context: Context,
    treeUri: Uri,
) : SessionOutputWriter {
    private val resolver = context.contentResolver
    private val root =
        DocumentFile.fromTreeUri(context, treeUri)
            ?: throw IllegalArgumentException("出力先 tree を開けません。")

    override fun writeText(relativePath: String, content: String) {
        writeBytes(relativePath, content.toByteArray(Charsets.UTF_8))
    }

    override fun writeBytes(relativePath: String, content: ByteArray) {
        val target = resolveFile(relativePath)
        resolver.openOutputStream(target.uri, "wt")?.use { stream ->
            stream.write(content)
        } ?: throw IllegalStateException("出力 file を開けません: $relativePath")
    }

    private fun resolveFile(relativePath: String): DocumentFile {
        val parts = relativePath.split('/').filter { it.isNotBlank() }
        require(parts.isNotEmpty()) { "relativePath が空です。" }
        var current = root
        parts.dropLast(1).forEach { part ->
            current =
                current.findFile(part)
                    ?: current.createDirectory(part)
                    ?: throw IllegalStateException("directory を作成できません: $part")
        }
        val filename = parts.last()
        return current.findFile(filename)
            ?: current.createFile(mimeTypeFor(filename), filename)
            ?: throw IllegalStateException("file を作成できません: $filename")
    }

    private fun mimeTypeFor(filename: String): String =
        when {
            filename.endsWith(".json") || filename.endsWith(".jsonl") -> "application/json"
            filename.endsWith(".csv") -> "text/csv"
            filename.endsWith(".mp4") -> "video/mp4"
            else -> "application/octet-stream"
        }
}

class PrefixedSessionOutputWriter(
    private val delegate: SessionOutputWriter,
    private val prefix: String,
) : SessionOutputWriter {
    override fun writeText(relativePath: String, content: String) {
        delegate.writeText(joinPath(prefix, relativePath), content)
    }

    override fun writeBytes(relativePath: String, content: ByteArray) {
        delegate.writeBytes(joinPath(prefix, relativePath), content)
    }

    private fun joinPath(prefix: String, relativePath: String): String =
        listOf(prefix.trim('/'), relativePath.trim('/'))
            .filter { it.isNotBlank() }
            .joinToString("/")
}
