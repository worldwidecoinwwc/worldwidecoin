# WorldWideCoin Mobile App - APK Build Instructions

This guide provides step-by-step instructions to build pre-built APK files for WorldWideCoin React Native mobile app distribution.

## 📋 Prerequisites

### **Required Software:**
- **Node.js** 16.x or higher
- **React Native CLI**: `npm install -g react-native-cli`
- **Android Studio**: Latest version with Android SDK
- **Java Development Kit (JDK)**: Version 11 or higher
- **Git**: For cloning repository

### **Environment Setup:**
```bash
# Verify Node.js version
node --version  # Should be 16.x or higher

# Verify React Native CLI
npx react-native --version

# Set Android environment variables (Windows)
set ANDROID_HOME=C:\Users\%USERNAME%\AppData\Local\Android\Sdk
set PATH=%PATH%;%ANDROID_HOME%\tools;%ANDROID_HOME%\platform-tools
```

## 🔨 Building APK Files

### **Step 1: Clone Repository**
```bash
git clone https://github.com/worldwidecoinwwc/worldwidecoin.git
cd worldwidecoin
```

### **Step 2: Install Dependencies**
```bash
cd mobile
npm install
```

### **Step 3: Build Debug APK**
```bash
# Build debug APK for testing
cd android
./gradlew assembleDebug

# APK location: android/app/build/outputs/apk/debug/app-debug.apk
```

### **Step 4: Build Release APK**
```bash
# Build release APK for distribution
cd android
./gradlew assembleRelease

# APK location: android/app/build/outputs/apk/release/app-release.apk
```

### **Step 5: Build Signed APK**
```bash
# Generate signing key (first time only)
keytool -genkey -v -keystore worldwidecoin-release.keystore \
  -alias worldwidecoin \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -storepass worldwidecoin123 \
  -keypass worldwidecoin123

# Build signed APK
cd android
./gradlew assembleRelease

# Sign APK
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 \
  -keystore worldwidecoin-release.keystore \
  -storepass worldwidecoin123 \
  -keypass worldwidecoin123 \
  app/build/outputs/apk/release/app-release-unsigned.apk \
  worldwidecoin
```

## 📱 APK File Locations

After building, APK files will be available at:

| APK Type | File Location | Size | Use Case |
|-----------|---------------|------|---------|
| **Debug** | `android/app/build/outputs/apk/debug/app-debug.apk` | ~15MB | Development & Testing |
| **Release** | `android/app/build/outputs/apk/release/app-release.apk` | ~12MB | Distribution (Unsigned) |
| **Signed** | `worldwidecoin-signed.apk` | ~12MB | Distribution (Signed) |

## 📲 Installation Instructions

### **For Android Users:**

#### **Method 1: Direct APK Installation**
1. **Download APK** from the links below
2. **Enable Unknown Sources** in Settings > Security
3. **Install APK** by tapping the downloaded file
4. **Allow permissions** when prompted
5. **Launch app** from home screen

#### **Method 2: ADB Installation (Development)**
```bash
# Enable USB Debugging on device
adb devices

# Install APK
adb install app-debug.apk

# Launch app
adb shell am start -n com.worldwidecoin
```

#### **Method 3: Android Studio Installation**
1. **Open Android Studio**
2. **Import project**: `File > Open` → Select `worldwidecoin/android` directory
3. **Build APK**: `Build > Build Bundle(s) / APK(s) > Build APK(s)`
4. **Find APK**: Check `android/app/build/outputs/apk/` folder
5. **Run on Device**: Select device and click Run button

## 🔐 APK Information

### **App Details:**
- **Package Name**: `com.worldwidecoin`
- **App Name**: `WorldWideCoin`
- **Version**: `1.0.0`
- **Minimum SDK**: 24 (Android 7.0+)
- **Target SDK**: 34 (Android 14+)
- **Architecture**: ARM64, ARMv7, x86, x86_64

### **Permissions Required:**
- `android.permission.INTERNET`
- `android.permission.CAMERA`
- `android.permission.USE_FINGERPRINT`
- `android.permission.WRITE_EXTERNAL_STORAGE`
- `android.permission.READ_EXTERNAL_STORAGE`
- `android.permission.ACCESS_NETWORK_STATE`

## 🚀 Distribution Options

### **Option 1: GitHub Releases**
- Upload APK files to GitHub Releases
- Create release notes and changelog
- Provide direct download links for users

### **Option 2: Website Distribution**
- Add APK download links to main website
- Provide QR codes for easy mobile access
- Include installation instructions for users

### **Option 3: App Store Submission**
- Create Google Play Developer account
- Prepare store listing and screenshots
- Submit signed APK for review and approval

## 🔧 Build Variants

### **Development Builds:**
- **Debug APK**: For testing and development
- **Development Build**: Faster build times, debug symbols included

### **Production Builds:**
- **Release APK**: Optimized, minified code
- **Signed APK**: Production-ready with digital signature
- **Bundle**: For Google Play Store submission

## ⚠️ Troubleshooting

### **Common Build Issues:**
```bash
# Clean build if errors occur
cd android
./gradlew clean
./gradlew assembleDebug

# Clear React Native cache
npx react-native start --reset-cache
npm start -- --reset-cache

# Check Android SDK installation
echo $ANDROID_HOME
./gradlew androidDependencies
```

### **Installation Issues:**
- **Parse Error**: Check `AndroidManifest.xml` syntax
- **Version Conflict**: Update `build.gradle` with correct SDK versions
- **Missing Dependencies**: Run `npm install` again
- **Signing Failed**: Verify keystore and passwords

## 📊 Build Performance

### **Expected Build Times:**
- **Clean Build**: 2-3 minutes
- **Incremental Build**: 30-60 seconds
- **APK Generation**: 1-2 minutes

### **Optimization Tips:**
```bash
# Enable ProGuard for release builds
android {
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt')
            signingConfig signingConfigs.release
        }
    }
}

# Split APKs for different architectures
android {
    splits {
        abi {
            reset()
            include 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'
            universalApk false
        }
    }
}
```

## 🎯 Success Verification

### **Test Your Build:**
```bash
# Verify APK installation
adb install -r app-release.apk

# Check app installation
adb shell pm list packages | grep worldwidecoin

# Launch app and check logs
adb logcat | grep WorldWideCoin
```

## 📱 Quick Start Commands

```bash
# Quick build and install
cd worldwidecoin/mobile
npm run build:android
adb install android/app/build/outputs/apk/release/app-release.apk
adb shell am start -n com.worldwidecoin

# Development build and test
npm run build:android
adb install android/app/build/outputs/apk/debug/app-debug.apk
adb shell am start -n com.worldwidecoin
```

## 🔗 Download Links

### **Pre-built APKs (Coming Soon)**
Once the build pipeline is set up, pre-built APKs will be available at:

- **Debug APK**: [Will be available after build]
- **Release APK**: [Will be available after build]
- **Signed APK**: [Will be available after build]

### **Current Status:**
⚠️ **Build pipeline setup in progress**
- APK files need to be built from source code
- Follow instructions above to build manually
- Automated builds coming soon

## 📞 Support

For build issues or questions:
- **Documentation**: Check `mobile/REACT_NATIVE_SETUP.md`
- **Issues**: Report on [GitHub Issues](https://github.com/worldwidecoinwwc/worldwidecoin/issues)
- **Community**: Join our development community

---

**Next Steps:**
1. Set up development environment
2. Clone repository and install dependencies
3. Build APK using provided commands
4. Test on emulator or physical device
5. Distribute to users

The WorldWideCoin mobile app APK build system provides professional cryptocurrency wallet functionality for Android devices with easy distribution and installation options.
