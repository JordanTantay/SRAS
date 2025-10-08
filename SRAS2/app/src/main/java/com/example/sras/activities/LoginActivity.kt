package com.example.sras.activities

import android.os.Bundle
import android.content.Intent
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.example.sras.R
import com.example.sras.api.ApiService
import com.example.sras.model.Credentials
import com.example.sras.model.TokenResponse
import com.example.sras.model.UserProfile
import okhttp3.OkHttpClient
import okhttp3.Interceptor
import retrofit2.*
import retrofit2.converter.gson.GsonConverterFactory

class LoginActivity : AppCompatActivity() {

    private lateinit var usernameInput: EditText
    private lateinit var passwordInput: EditText
    private lateinit var loginButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)


        usernameInput = findViewById(R.id.editUsername)
        passwordInput = findViewById(R.id.editPassword)
        loginButton = findViewById(R.id.btnLogin)

        loginButton.setOnClickListener {
            val username = usernameInput.text.toString()
            val password = passwordInput.text.toString()
            login(username, password)
        }
    }



    private fun login(username: String, password: String) {
        val loggingInterceptor = Interceptor { chain ->
            val request = chain.request()
            android.util.Log.d("HTTP", "-> ${request.method} ${request.url}")
            val response = chain.proceed(request)
            android.util.Log.d("HTTP", "<- ${response.code} ${request.url}")
            response
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl("http://192.168.1.7:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .client(client)
            .build()

        val api = retrofit.create(ApiService::class.java)

        // 1) Obtain JWT tokens from Django SimpleJWT
        api.obtainToken(Credentials(username = username, password = password)).enqueue(object : Callback<TokenResponse> {
            override fun onResponse(call: Call<TokenResponse>, response: Response<TokenResponse>) {
                val tokenBody = response.body()
                if (response.isSuccessful && tokenBody?.access != null) {
                    val access = tokenBody.access
                    val refresh = tokenBody.refresh

                    getSharedPreferences("user_session", MODE_PRIVATE).edit().apply {
                        putString("access_token", access)
                        putString("refresh_token", refresh)
                        putString("username", username)
                        apply()
                    }

                    // 2) Optionally fetch current user profile
                    fetchCurrentUser(api, tokenBody.access)
                    // 3) Navigate to main dashboard
                    startActivity(Intent(this@LoginActivity, MainActivity::class.java))
                    finish()
                } else {
                    val err = try { response.errorBody()?.string() } catch (e: Exception) { null }
                    Toast.makeText(this@LoginActivity, "Login failed (${response.code()}): ${err ?: "Invalid credentials"}", Toast.LENGTH_LONG).show()
                }
            }

            override fun onFailure(call: Call<TokenResponse>, t: Throwable) {
                Toast.makeText(this@LoginActivity, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
            }
        })
    }

    private fun fetchCurrentUser(api: ApiService, accessToken: String) {
        api.getCurrentUser("Bearer $accessToken").enqueue(object : Callback<UserProfile> {
            override fun onResponse(call: Call<UserProfile>, response: Response<UserProfile>) {
                val profile = response.body()
                if (response.isSuccessful && profile != null) {
                    Log.d("LoginDebug", "User ID: ${profile.id}")
                    Log.d("LoginDebug", "Username: ${profile.username}")
                    Log.d("LoginDebug", "Full Name: ${profile.full_name}")
                    Log.d("LoginDebug", "Role: ${profile.role}")

                    getSharedPreferences("user_session", MODE_PRIVATE).edit().apply {
                        putInt("user_id", profile.id ?: -1)
                        putString("full_name", profile.full_name)
                        putString("role", profile.role)
                        apply()
                    }

                    Toast.makeText(this@LoginActivity, "Welcome, ${profile.full_name ?: profile.username}", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(this@LoginActivity, "Login successful", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onFailure(call: Call<UserProfile>, t: Throwable) {
                Toast.makeText(this@LoginActivity, "Logged in, but failed to fetch profile", Toast.LENGTH_SHORT).show()
            }
        })
    }
}
