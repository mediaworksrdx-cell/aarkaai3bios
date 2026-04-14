package com.example.aarkaai.network

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {
    // Note: If using Android Emulator connecting to local FastAPI, use 10.0.2.2. 
    // If your backend is deployed, replace with your HTTPS url.
    private const val BASE_URL = "http://10.0.2.2:5000/" 

    // Extend timeouts significantly, LLM generation (especially local CPU) takes time.
    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(60, TimeUnit.SECONDS)
        .readTimeout(180, TimeUnit.SECONDS) // 3 mins read timeout for deep reasoning loops
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()

    val apiService: ApiService by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}
