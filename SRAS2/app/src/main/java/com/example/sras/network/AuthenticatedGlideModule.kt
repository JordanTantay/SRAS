package com.example.sras.network

import android.content.Context
import com.bumptech.glide.Glide
import com.bumptech.glide.Registry
import com.bumptech.glide.annotation.GlideModule
import com.bumptech.glide.integration.okhttp3.OkHttpUrlLoader
import com.bumptech.glide.load.model.GlideUrl
import com.bumptech.glide.module.AppGlideModule
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import java.io.InputStream

@GlideModule
class AuthenticatedGlideModule : AppGlideModule() {

    override fun registerComponents(context: Context, glide: Glide, registry: Registry) {
        // Create OkHttp client with authentication interceptor
        val authInterceptor = Interceptor { chain ->
            val request = chain.request()
            val url = request.url.toString()
            
            // Only add auth header for violation image URLs
            if (url.contains("/api/violations/") && url.contains("/image/")) {
                // Get access token from SharedPreferences
                val prefs = context.getSharedPreferences("user_session", Context.MODE_PRIVATE)
                val accessToken = prefs.getString("access_token", null)
                
                if (accessToken != null) {
                    val authenticatedRequest = request.newBuilder()
                        .addHeader("Authorization", "Bearer $accessToken")
                        .build()
                    chain.proceed(authenticatedRequest)
                } else {
                    chain.proceed(request)
                }
            } else {
                chain.proceed(request)
            }
        }
        
        val client = OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .build()
        
        // Register OkHttp loader for Glide
        registry.replace(GlideUrl::class.java, InputStream::class.java, OkHttpUrlLoader.Factory(client))
    }
}
