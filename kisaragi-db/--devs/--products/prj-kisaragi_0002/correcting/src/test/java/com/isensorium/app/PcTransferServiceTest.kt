package com.isensorium.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.file.Files
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.zip.ZipFile

class PcTransferServiceTest {

    private val service = PcTransferService()

    @Test
    fun buildSessionArchiveWritesExpectedEntries() {
        val tempRoot = Files.createTempDirectory("pc-transfer-test").toFile()
        val sessionDir = File(tempRoot, "session-001").apply { mkdirs() }
        File(sessionDir, "session_manifest.json").writeText("""{"sessionId":"session-001"}""")
        File(sessionDir, "trajectreview").mkdirs()
        File(sessionDir, "trajectreview/input_readiness.json").writeText("""{"readyForDiagnose":true}""")
        val archive = File(tempRoot, "session-001.zip")

        try {
            service.buildSessionArchive(sessionDir, archive)
            assertTrue(archive.exists())
            ZipFile(archive).use { zip ->
                assertTrue(zip.getEntry("session-001/session_manifest.json") != null)
                assertTrue(zip.getEntry("session-001/trajectreview/input_readiness.json") != null)
            }
        } finally {
            archive.delete()
            tempRoot.deleteRecursively()
        }
    }

    @Test(expected = IllegalArgumentException::class)
    fun transferCheckedSessionRequiresAtLeastOneDataCheck() {
        val tempRoot = Files.createTempDirectory("pc-transfer-no-check").toFile()
        try {
            service.transferCheckedSession(
                sessionDir = tempRoot,
                dataCheckCount = 0,
                hostOverride = "127.0.0.1",
            )
        } finally {
            tempRoot.deleteRecursively()
        }
    }

    @Test
    fun parseDiscoveryResponseBuildsSelectablePcTarget() {
        val target =
            service.parseDiscoveryResponse("READY|192.168.0.10|47111|DESKTOP-01|C:/kisaragi-transfer")

        requireNotNull(target)
        assertEquals("DESKTOP-01", target.displayName)
        assertEquals("192.168.0.10", target.host)
        assertEquals(47111, target.port)
        assertEquals("C:/kisaragi-transfer", target.targetRoot)
    }

    @Test
    fun discoverTargetsFindsLocalUdpResponder() {
        val bootstrapPort = 47121
        val responderReady = CountDownLatch(1)
        val responder =
            Thread {
                DatagramSocket(bootstrapPort, InetAddress.getByName("127.0.0.1")).use { socket ->
                    responderReady.countDown()
                    val request = DatagramPacket(ByteArray(2048), 2048)
                    socket.receive(request)
                    val replyBytes =
                        "READY|127.0.0.1|47111|TEST-PC|C:/kisaragi-transfer".toByteArray(Charsets.UTF_8)
                    val reply =
                        DatagramPacket(
                            replyBytes,
                            replyBytes.size,
                            request.address,
                            request.port,
                        )
                    socket.send(reply)
                }
            }
        responder.isDaemon = true
        responder.start()
        assertTrue(responderReady.await(3, TimeUnit.SECONDS))

        val targets =
            service.discoverTargets(
                bootstrapPort = bootstrapPort,
                timeoutMs = 1500,
                additionalProbeHosts = listOf(InetAddress.getByName("127.0.0.1")),
            )

        assertTrue(targets.any { it.displayName == "TEST-PC" && it.host == "127.0.0.1" })
        responder.join(3000)
    }
}
