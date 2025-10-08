package com.example.sras.activities

import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.sras.R
import com.example.sras.adapters.PendingVerificationAdapter
import com.example.sras.api.ApiService
import com.example.sras.dialogs.VerificationDialog
import com.example.sras.model.Violation
import com.example.sras.model.ViolationVerification
import okhttp3.OkHttpClient
import retrofit2.*
import retrofit2.converter.gson.GsonConverterFactory

class PendingVerificationActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: PendingVerificationAdapter
    private lateinit var tvCount: TextView
    private lateinit var tvEmptyState: TextView
    private lateinit var btnBack: Button
    private lateinit var btnRefreshToggle: Button
    private var accessToken: String? = null
    
    // Auto-refresh functionality
    private var autoRefreshHandler: Handler? = null
    private var autoRefreshRunnable: Runnable? = null
    private var isAutoRefreshEnabled = true
    private val refreshInterval = 30000L // 30 seconds

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_pending_verification)

        setupViews()
        setupAutoRefresh()
        fetchPendingViolations()
    }

    private fun setupViews() {
        recyclerView = findViewById(R.id.recyclerViewPendingViolations)
        tvCount = findViewById(R.id.tvPendingCount)
        tvEmptyState = findViewById(R.id.tvPendingEmptyState)
        btnBack = findViewById(R.id.btnBack)
        btnRefreshToggle = findViewById(R.id.btnRefreshToggle)

        adapter = PendingVerificationAdapter(emptyList()) { violation ->
            showVerificationDialog(violation)
        }

        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        btnBack.setOnClickListener {
            finish()
        }
        
        btnRefreshToggle.setOnClickListener {
            toggleAutoRefresh()
        }
    }

    private fun showVerificationDialog(violation: Violation) {
        val dialog = VerificationDialog(this, violation) { approved ->
            verifyViolation(violation.id, approved)
        }
        dialog.show()
    }

    private fun verifyViolation(violationId: Int, approved: Boolean) {
        accessToken = getSharedPreferences("user_session", MODE_PRIVATE)
            .getString("access_token", null)
        
        if (accessToken == null) {
            Toast.makeText(this, "No access token", Toast.LENGTH_SHORT).show()
            return
        }

        val status = if (approved) "approved" else "rejected"
        val verification = ViolationVerification(
            status = status,
            verificationNotes = if (approved) "Approved by mobile app user" else "Rejected by mobile app user"
        )

        val retrofit = Retrofit.Builder()
            .baseUrl("http://192.168.1.7:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .client(OkHttpClient())
            .build()

        val api = retrofit.create(ApiService::class.java)
        api.verifyViolation("Bearer $accessToken", violationId, verification).enqueue(object : Callback<okhttp3.ResponseBody> {
            override fun onResponse(call: Call<okhttp3.ResponseBody>, response: Response<okhttp3.ResponseBody>) {
                if (response.isSuccessful) {
                    Toast.makeText(this@PendingVerificationActivity, "Violation ${if (approved) "approved" else "rejected"} successfully", Toast.LENGTH_SHORT).show()
                    fetchPendingViolations() // Refresh the list
                } else {
                    val err = try { response.errorBody()?.string() } catch (e: Exception) { null }
                    Toast.makeText(this@PendingVerificationActivity, "Failed to verify: ${err ?: "Error"}", Toast.LENGTH_LONG).show()
                    Log.e("Verification", "Error: ${response.code()} - $err")
                }
            }

            override fun onFailure(call: Call<okhttp3.ResponseBody>, t: Throwable) {
                Toast.makeText(this@PendingVerificationActivity, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                Log.e("Verification", "Network error", t)
            }
        })
    }

    private fun fetchPendingViolations() {
        accessToken = getSharedPreferences("user_session", MODE_PRIVATE)
            .getString("access_token", null)
        
        if (accessToken == null) {
            Toast.makeText(this, "No access token", Toast.LENGTH_SHORT).show()
            return
        }

        val retrofit = Retrofit.Builder()
            .baseUrl("http://192.168.1.7:8000/")
            .addConverterFactory(GsonConverterFactory.create())
            .client(OkHttpClient())
            .build()

        val api = retrofit.create(ApiService::class.java)
        api.getPendingViolations("Bearer $accessToken").enqueue(object : Callback<List<Violation>> {
            override fun onResponse(call: Call<List<Violation>>, response: Response<List<Violation>>) {
                if (response.isSuccessful) {
                    val violations = response.body() ?: emptyList()
                    adapter.updateViolations(violations)
                    tvCount.text = "${violations.size} violations pending verification"
                    
                    if (violations.isEmpty()) {
                        tvEmptyState.visibility = TextView.VISIBLE
                        recyclerView.visibility = RecyclerView.GONE
                    } else {
                        tvEmptyState.visibility = TextView.GONE
                        recyclerView.visibility = RecyclerView.VISIBLE
                    }
                } else {
                    val err = try { response.errorBody()?.string() } catch (e: Exception) { null }
                    Toast.makeText(this@PendingVerificationActivity, "Failed (${response.code()}): ${err ?: "Error"}", Toast.LENGTH_LONG).show()
                    Log.e("PendingVerification", "Error: ${response.code()} - $err")
                }
            }

            override fun onFailure(call: Call<List<Violation>>, t: Throwable) {
                Toast.makeText(this@PendingVerificationActivity, "Network error: ${t.message}", Toast.LENGTH_SHORT).show()
                Log.e("PendingVerification", "Network error", t)
            }
        })
    }
    
    private fun setupAutoRefresh() {
        autoRefreshHandler = Handler(Looper.getMainLooper())
        autoRefreshRunnable = object : Runnable {
            override fun run() {
                if (isAutoRefreshEnabled) {
                    Log.d("AutoRefresh", "Auto-refreshing pending violations...")
                    fetchPendingViolations()
                }
                autoRefreshHandler?.postDelayed(this, refreshInterval)
            }
        }
        startAutoRefresh()
    }
    
    private fun startAutoRefresh() {
        autoRefreshHandler?.removeCallbacks(autoRefreshRunnable!!)
        autoRefreshHandler?.postDelayed(autoRefreshRunnable!!, refreshInterval)
        updateRefreshButton()
    }
    
    private fun stopAutoRefresh() {
        autoRefreshHandler?.removeCallbacks(autoRefreshRunnable!!)
        updateRefreshButton()
    }
    
    private fun toggleAutoRefresh() {
        isAutoRefreshEnabled = !isAutoRefreshEnabled
        if (isAutoRefreshEnabled) {
            startAutoRefresh()
            Toast.makeText(this, "Auto-refresh enabled (30s)", Toast.LENGTH_SHORT).show()
        } else {
            stopAutoRefresh()
            Toast.makeText(this, "Auto-refresh paused", Toast.LENGTH_SHORT).show()
        }
    }
    
    private fun updateRefreshButton() {
        if (isAutoRefreshEnabled) {
            btnRefreshToggle.text = "⏸️ Pause Auto-Refresh"
            btnRefreshToggle.setBackgroundResource(R.drawable.bg_reject_button)
        } else {
            btnRefreshToggle.text = "▶️ Start Auto-Refresh"
            btnRefreshToggle.setBackgroundResource(R.drawable.bg_approve_button)
        }
    }
    
    override fun onResume() {
        super.onResume()
        if (isAutoRefreshEnabled) {
            startAutoRefresh()
        }
    }
    
    override fun onPause() {
        super.onPause()
        stopAutoRefresh()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        stopAutoRefresh()
        autoRefreshHandler = null
        autoRefreshRunnable = null
    }
}
