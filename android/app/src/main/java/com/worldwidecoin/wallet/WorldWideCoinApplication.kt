package com.worldwidecoin.wallet

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class WorldWideCoinApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
    }
}
