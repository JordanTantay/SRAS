package com.example.sras.utils

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.AsyncTask
import android.util.Log
import android.widget.ImageView
import com.example.sras.R
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.InputStream

object SimpleImageLoader {
    
    fun loadAuthenticatedImage(context: Context, imageView: ImageView, imageUrl: String) {
        // Get access token from SharedPreferences
        val prefs = context.getSharedPreferences("user_session", Context.MODE_PRIVATE)
        val accessToken = prefs.getString("access_token", null)
        
        Log.d("SimpleImageLoader", "Loading image: $imageUrl")
        Log.d("SimpleImageLoader", "Access token: ${accessToken?.take(20)}...")
        
        // Set placeholder first
        imageView.setImageResource(R.drawable.ic_image_placeholder)
        
        if (accessToken != null) {
            // Load image with authentication
            LoadImageTask(imageView).execute(imageUrl, accessToken)
        } else {
            Log.d("SimpleImageLoader", "No access token available")
            imageView.setImageResource(R.drawable.ic_image_placeholder)
        }
    }
    
    private class LoadImageTask(private val imageView: ImageView) : AsyncTask<String, Void, Bitmap?>() {
        
        override fun doInBackground(vararg params: String): Bitmap? {
            val imageUrl = params[0]
            val accessToken = params[1]
            
            return try {
                val client = OkHttpClient()
                val request = Request.Builder()
                    .url(imageUrl)
                    .addHeader("Authorization", "Bearer $accessToken")
                    .build()
                
                Log.d("SimpleImageLoader", "Making request to: $imageUrl")
                val response = client.newCall(request).execute()
                
                if (response.isSuccessful) {
                    val inputStream: InputStream? = response.body?.byteStream()
                    BitmapFactory.decodeStream(inputStream)
                } else {
                    Log.e("SimpleImageLoader", "Failed to load image: ${response.code}")
                    null
                }
            } catch (e: Exception) {
                Log.e("SimpleImageLoader", "Error loading image", e)
                null
            }
        }
        
        override fun onPostExecute(bitmap: Bitmap?) {
            if (bitmap != null) {
                imageView.setImageBitmap(bitmap)
                Log.d("SimpleImageLoader", "Image loaded successfully")
            } else {
                imageView.setImageResource(R.drawable.ic_image_placeholder)
                Log.d("SimpleImageLoader", "Failed to load image, showing placeholder")
            }
        }
    }
}
