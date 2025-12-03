
package com.example.sras.model

data class LoginResponse(
    val success: Boolean,
    val user_id: Int?,
    val username: String?,
    val full_name: String?,
    val role: String?,
    val message: String? = null
)
