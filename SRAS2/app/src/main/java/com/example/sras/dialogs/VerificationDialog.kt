package com.example.sras.dialogs

import android.app.Dialog
import android.content.Context
import android.os.Bundle
import android.view.View
import android.view.Window
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
// Removed unused Glide import - using SimpleImageLoader instead
import com.example.sras.R
import com.example.sras.model.Violation
import com.example.sras.utils.SimpleImageLoader
import java.text.SimpleDateFormat
import java.util.*

class VerificationDialog(
    private val context: Context,
    private val violation: Violation,
    private val onVerificationResult: (Boolean) -> Unit
) : Dialog(context) {

    private lateinit var ivViolationImage: ImageView
    private lateinit var tvPlateNumber: TextView
    private lateinit var tvCameraName: TextView
    private lateinit var tvTimestamp: TextView
    private lateinit var btnApprove: Button
    private lateinit var btnReject: Button
    private lateinit var btnCancel: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestWindowFeature(Window.FEATURE_NO_TITLE)
        setContentView(R.layout.dialog_verification)

        setupViews()
        populateData()
    }

    private fun setupViews() {
        ivViolationImage = findViewById(R.id.ivDialogViolationImage)
        tvPlateNumber = findViewById(R.id.tvDialogPlateNumber)
        tvCameraName = findViewById(R.id.tvDialogCameraName)
        tvTimestamp = findViewById(R.id.tvDialogTimestamp)
        btnApprove = findViewById(R.id.btnApprove)
        btnReject = findViewById(R.id.btnReject)
        btnCancel = findViewById(R.id.btnCancel)

        btnApprove.setOnClickListener {
            onVerificationResult(true)
            dismiss()
        }

        btnReject.setOnClickListener {
            onVerificationResult(false)
            dismiss()
        }

        btnCancel.setOnClickListener {
            dismiss()
        }
    }

    private fun populateData() {
        // Set violation data
        tvPlateNumber.text = violation.plateNumber ?: "UNKNOWN"
        tvCameraName.text = violation.camera.name
        
        // Format timestamp
        try {
            val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
            val outputFormat = SimpleDateFormat("MMM dd, yyyy HH:mm", Locale.getDefault())
            val date = inputFormat.parse(violation.timestamp)
            tvTimestamp.text = outputFormat.format(date ?: Date())
        } catch (e: Exception) {
            tvTimestamp.text = violation.timestamp
        }
        
        // Load violation image using authenticated SimpleImageLoader
        val imageUrl = "http://192.168.1.7:8000/api/violations/${violation.id}/image/"
        SimpleImageLoader.loadAuthenticatedImage(context, ivViolationImage, imageUrl)
    }
}
