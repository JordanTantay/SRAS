package com.example.sras.api

import com.example.sras.model.Credentials
import com.example.sras.model.TokenResponse
import com.example.sras.model.UserProfile
import com.example.sras.model.Violation
import com.example.sras.model.ViolationVerification
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.PATCH
import retrofit2.http.POST
import retrofit2.http.Path

interface ApiService {

    // Django SimpleJWT: obtain token (JSON body)
    @POST("api/auth/token/")
    fun obtainToken(
        @Body credentials: Credentials
    ): Call<TokenResponse>

    // Optional: fetch current user profile
    @GET("api/users/me/")
    fun getCurrentUser(
        @Header("Authorization") bearerToken: String
    ): Call<UserProfile>

    // Violations API - Only pending violations for verification
    @GET("api/violations/pending/")
    fun getPendingViolations(
        @Header("Authorization") bearerToken: String
    ): Call<List<Violation>>

    @GET("api/violations/{id}/image/")
    fun getViolationImage(
        @Header("Authorization") bearerToken: String,
        @Path("id") violationId: Int
    ): Call<okhttp3.ResponseBody>

    @PATCH("api/violations/{id}/verify/")
    fun verifyViolation(
        @Header("Authorization") bearerToken: String,
        @Path("id") violationId: Int,
        @Body verification: ViolationVerification
    ): Call<okhttp3.ResponseBody>
}