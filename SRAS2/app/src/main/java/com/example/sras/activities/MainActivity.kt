package com.example.sras.activities

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.sras.R

class MainActivity : AppCompatActivity() {

    private lateinit var welcomeText: TextView
    private lateinit var btnPendingVerification: Button
    private lateinit var btnLogout: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        setupViews()
        setupClickListeners()
        displayUserInfo()
    }

    private fun setupViews() {
        welcomeText = findViewById(R.id.tvWelcome)
        btnPendingVerification = findViewById(R.id.btnPendingVerification)
        btnLogout = findViewById(R.id.btnLogout)
    }

    private fun setupClickListeners() {
        btnPendingVerification.setOnClickListener {
            val intent = Intent(this, PendingVerificationActivity::class.java)
            startActivity(intent)
        }

        btnLogout.setOnClickListener {
            // Clear shared preferences
            getSharedPreferences("user_session", MODE_PRIVATE).edit().clear().apply()
            
            // Go back to login
            val intent = Intent(this, LoginActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            startActivity(intent)
            finish()
        }
    }

    private fun displayUserInfo() {
        val sharedPrefs = getSharedPreferences("user_session", MODE_PRIVATE)
        val fullName = sharedPrefs.getString("full_name", null)
        val username = sharedPrefs.getString("username", "User")
        val role = sharedPrefs.getString("role", "user")
        
        val displayName = fullName ?: username
        welcomeText.text = "Welcome, $displayName! ($role)"
    }
}
