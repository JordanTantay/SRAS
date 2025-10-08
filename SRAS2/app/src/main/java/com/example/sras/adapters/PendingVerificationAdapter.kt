package com.example.sras.adapters

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
// Removed Glide imports - now using SimpleImageLoader
import com.example.sras.R
import com.example.sras.model.Violation
import com.example.sras.utils.SimpleImageLoader
import java.text.SimpleDateFormat
import java.util.*

class PendingVerificationAdapter(
    private var violations: List<Violation>,
    private val onVerifyClick: (Violation) -> Unit = {}
) : RecyclerView.Adapter<PendingVerificationAdapter.ViolationViewHolder>() {

    class ViolationViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val ivViolationImage: ImageView = itemView.findViewById(R.id.ivViolationImage)
        val tvPlateNumber: TextView = itemView.findViewById(R.id.tvPlateNumber)
        val tvCameraName: TextView = itemView.findViewById(R.id.tvCameraName)
        val tvTimestamp: TextView = itemView.findViewById(R.id.tvTimestamp)
        val btnVerify: TextView = itemView.findViewById(R.id.btnVerify)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViolationViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_pending_violation, parent, false)
        return ViolationViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViolationViewHolder, position: Int) {
        val violation = violations[position]
        
        // Set violation data
        holder.tvPlateNumber.text = violation.plateNumber ?: "UNKNOWN"
        holder.tvCameraName.text = violation.camera.name
        
        // Format timestamp
        try {
            val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
            val outputFormat = SimpleDateFormat("MMM dd, yyyy HH:mm", Locale.getDefault())
            val date = inputFormat.parse(violation.timestamp)
            holder.tvTimestamp.text = outputFormat.format(date ?: Date())
        } catch (e: Exception) {
            holder.tvTimestamp.text = violation.timestamp
        }
        
        // Set verification button text
        holder.btnVerify.text = "VERIFY"
        holder.btnVerify.setBackgroundResource(R.drawable.bg_verify_button)
        
        // Load violation image using authenticated SimpleImageLoader
        val imageUrl = "http://192.168.1.7:8000/api/violations/${violation.id}/image/"
        SimpleImageLoader.loadAuthenticatedImage(holder.itemView.context, holder.ivViolationImage, imageUrl)
        
        // Set click listener for verify button
        holder.btnVerify.setOnClickListener {
            onVerifyClick(violation)
        }
        
        // Also allow clicking on the image to verify
        holder.ivViolationImage.setOnClickListener {
            onVerifyClick(violation)
        }
    }

    override fun getItemCount(): Int = violations.size

    fun updateViolations(newViolations: List<Violation>) {
        violations = newViolations
        notifyDataSetChanged()
    }
}
