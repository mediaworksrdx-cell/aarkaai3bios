# Proguard rules for release builds

# ─── Network models (Gson serialization) ───
-keep class com.aarkaai.app.network.** { *; }
-keepattributes Signature
-keepattributes *Annotation*

# ─── BuildConfig ───
-keep class com.aarkaai.app.BuildConfig { *; }
-keep class com.aarkaai.app.AarkaaiApplication { *; }
-keep class com.aarkaai.app.MainActivity { *; }

# ─── Retrofit ───
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepclasseswithmembers class * {
    @retrofit2.http.* <methods>;
}

# ─── Gson ───
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer
-keepclassmembers,allowobfuscation class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# ─── OkHttp ───
-dontwarn okhttp3.**
-dontwarn okio.**
-keep class okhttp3.** { *; }

# ─── Coroutines ───
-keepnames class kotlinx.coroutines.internal.MainDispatcherFactory {}
-keepnames class kotlinx.coroutines.CoroutineExceptionHandler {}
-keepclassmembers class kotlinx.coroutines.** { volatile <fields>; }

# ─── Markwon (Markdown rendering) ───
-keep class io.noties.markwon.** { *; }
-dontwarn io.noties.markwon.**

# ─── DataStore ───
-keep class androidx.datastore.** { *; }
-keepclassmembers class * extends com.google.protobuf.GeneratedMessageLite { *; }

# ─── Compose / AndroidX ───
-keep class androidx.compose.** { *; }
-dontwarn androidx.compose.**
-keep class androidx.lifecycle.** { *; }
