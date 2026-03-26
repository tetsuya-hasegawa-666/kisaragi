package com.isensorium.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.nio.file.Files
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
}
