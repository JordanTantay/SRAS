package com.example.sras.model

import com.google.gson.annotations.SerializedName

data class ViolationVerification(
    val status: String,
    @SerializedName("verification_notes")
    val verificationNotes: String? = null
)
