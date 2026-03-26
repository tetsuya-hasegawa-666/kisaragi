package com.isensorium.app

import org.json.JSONObject
import java.io.BufferedInputStream
import java.io.BufferedReader
import java.io.File
import java.io.InputStreamReader
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.HttpURLConnection
import java.net.InetAddress
import java.net.NetworkInterface
import java.net.SocketTimeoutException
import java.net.URL
import java.nio.charset.StandardCharsets
import java.util.Collections
import java.util.UUID
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

data class PcTransferResult(
    val sessionId: String,
    val resolvedHost: String,
    val resolvedPort: Int,
    val targetRoot: String,
    val uploadedBytes: Long,
)

data class PcTransferTarget(
    val displayName: String,
    val host: String,
    val port: Int,
    val targetRoot: String,
)

class PcTransferService {

    fun discoverTargets(
        bootstrapPort: Int = DEFAULT_BOOTSTRAP_PORT,
        timeoutMs: Int = DEFAULT_TIMEOUT_MS,
    ): List<PcTransferTarget> {
        val payload = "TRAJECTREVIEW_BOOTSTRAP|${DEFAULT_TRANSFER_PORT}".toByteArray(StandardCharsets.UTF_8)
        val responseBuffer = ByteArray(2048)
        val targets = linkedMapOf<String, PcTransferTarget>()

        DatagramSocket().use { socket ->
            socket.broadcast = true
            socket.soTimeout = timeoutMs.coerceAtMost(1000)
            broadcastAddresses().forEach { address ->
                runCatching {
                    socket.send(DatagramPacket(payload, payload.size, address, bootstrapPort))
                }
            }
            val deadline = System.currentTimeMillis() + timeoutMs
            while (System.currentTimeMillis() < deadline) {
                val packet = DatagramPacket(responseBuffer, responseBuffer.size)
                try {
                    socket.receive(packet)
                } catch (_: SocketTimeoutException) {
                    continue
                }
                val response = String(packet.data, 0, packet.length, StandardCharsets.UTF_8).trim()
                parseDiscoveryResponse(response)?.let { target ->
                    targets[target.displayName + "|" + target.host + "|" + target.port] = target
                }
            }
        }

        return targets.values.sortedBy { it.displayName }
    }

    fun transferCheckedSession(
        sessionDir: File,
        dataCheckCount: Int,
        target: PcTransferTarget? = null,
        hostOverride: String? = null,
        bootstrapPort: Int = DEFAULT_BOOTSTRAP_PORT,
        transferPort: Int = DEFAULT_TRANSFER_PORT,
        timeoutMs: Int = DEFAULT_TIMEOUT_MS,
    ): PcTransferResult {
        require(dataCheckCount > 0) { "先に 1 回以上 data-check を実行してください。" }
        require(sessionDir.isDirectory) { "session directory が見つかりません。" }

        val sessionId = sessionDir.name
        val endpoint =
            target?.let { TransferEndpoint(it.host, it.port) }
                ?: resolveEndpoint(
                    hostOverride = hostOverride,
                    bootstrapPort = bootstrapPort,
                    fallbackTransferPort = transferPort,
                    timeoutMs = timeoutMs,
                )

        val archiveFile = File.createTempFile("trajectreview-transfer-${UUID.randomUUID()}", ".zip")
        try {
            buildSessionArchive(sessionDir, archiveFile)
            return uploadArchive(
                archiveFile = archiveFile,
                sessionId = sessionId,
                host = endpoint.host,
                port = endpoint.port,
                timeoutMs = timeoutMs,
            )
        } finally {
            archiveFile.delete()
        }
    }

    internal fun buildSessionArchive(sessionDir: File, archiveFile: File) {
        archiveFile.outputStream().buffered().use { output ->
            ZipOutputStream(output).use { zip ->
                sessionDir.walkTopDown()
                    .filter { it.isFile }
                    .forEach { file ->
                        val relativePath =
                            sessionDir.parentFile
                                ?.toPath()
                                ?.relativize(file.toPath())
                                ?.toString()
                                ?.replace('\\', '/')
                                ?: "${sessionDir.name}/${file.name}"
                        zip.putNextEntry(ZipEntry(relativePath))
                        file.inputStream().buffered().use { input -> input.copyTo(zip) }
                        zip.closeEntry()
                    }
            }
        }
    }

    private fun resolveEndpoint(
        hostOverride: String?,
        bootstrapPort: Int,
        fallbackTransferPort: Int,
        timeoutMs: Int,
    ): TransferEndpoint {
        val normalizedHost = hostOverride?.trim()?.takeIf { it.isNotEmpty() }
        if (normalizedHost != null) {
            return TransferEndpoint(normalizedHost, fallbackTransferPort)
        }

        val target =
            discoverTargets(
                bootstrapPort = bootstrapPort,
                timeoutMs = timeoutMs,
            ).firstOrNull()
                ?: throw IllegalStateException("同一ネットワーク上の PC 候補が見つかりません。PC で bootstrap script を起動してください。")
        return TransferEndpoint(target.host, target.port.takeIf { it > 0 } ?: fallbackTransferPort)
    }

    private fun uploadArchive(
        archiveFile: File,
        sessionId: String,
        host: String,
        port: Int,
        timeoutMs: Int,
    ): PcTransferResult {
        val connection =
            (URL("http://$host:$port/upload?sessionId=$sessionId").openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                doOutput = true
                connectTimeout = timeoutMs
                readTimeout = timeoutMs
                setRequestProperty("Content-Type", "application/zip")
                setRequestProperty("Content-Length", archiveFile.length().toString())
            }

        try {
            connection.outputStream.buffered().use { output ->
                archiveFile.inputStream().buffered().use { input -> input.copyTo(output) }
            }
            val code = connection.responseCode
            val body =
                (if (code in 200..299) connection.inputStream else connection.errorStream)?.use { stream ->
                    BufferedReader(InputStreamReader(BufferedInputStream(stream), StandardCharsets.UTF_8)).readText()
                }.orEmpty()
            require(code in 200..299) { "PC 転送に失敗しました: HTTP $code ${body.ifBlank { "" }}".trim() }
            val json = runCatching { JSONObject(body) }.getOrDefault(JSONObject())
            return PcTransferResult(
                sessionId = sessionId,
                resolvedHost = host,
                resolvedPort = port,
                targetRoot = json.optString("targetRoot").ifBlank { "不明" },
                uploadedBytes = archiveFile.length(),
            )
        } finally {
            connection.disconnect()
        }
    }

    private fun broadcastAddresses(): List<InetAddress> {
        val addresses = linkedSetOf<InetAddress>()
        addresses += InetAddress.getByName("255.255.255.255")
        Collections.list(NetworkInterface.getNetworkInterfaces()).forEach { network ->
            if (!network.isUp || network.isLoopback) {
                return@forEach
            }
            network.interfaceAddresses
                .mapNotNull { it.broadcast }
                .forEach { addresses += it }
        }
        return addresses.toList()
    }

    internal fun parseDiscoveryResponse(response: String): PcTransferTarget? {
        val parts = response.split("|")
        if (parts.size < 5 || parts[0] != "READY") {
            return null
        }
        return PcTransferTarget(
            displayName = parts[3],
            host = parts[1],
            port = parts[2].toIntOrNull() ?: return null,
            targetRoot = parts.subList(4, parts.size).joinToString("|"),
        )
    }

    private data class TransferEndpoint(
        val host: String,
        val port: Int,
    )

    companion object {
        const val DEFAULT_BOOTSTRAP_PORT = 47110
        const val DEFAULT_TRANSFER_PORT = 47111
        const val DEFAULT_TIMEOUT_MS = 10_000
    }
}
