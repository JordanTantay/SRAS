package com.example.sras.model

import com.google.gson.annotations.SerializedName

data class Violation(
    val id: Int,
    val camera: Camera,
    val timestamp: String,
    @SerializedName("plate_number")
    val plateNumber: String?,
    val sms_sent: Boolean,
    @SerializedName("rider_hash")
    val riderHash: String?,
    val status: String?,
    @SerializedName("verified_by")
    val verifiedBy: Int?,
    @SerializedName("verified_at")
    val verifiedAt: String?,
    @SerializedName("verification_notes")
    val verificationNotes: String?
)

data class Camera(
    val id: Int,
    val name: String,
    @SerializedName("stream_url")
    val streamUrl: String
)
