package com.reviework.app

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.reviework.app.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val controller = ReviewScreenController()
    private var currentIndex: Int = 0

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
    }
}
