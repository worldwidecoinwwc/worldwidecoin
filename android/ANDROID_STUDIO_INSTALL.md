# Android Studio Installation Guide

This guide will help you install Android Studio to develop the WorldWideCoin Android wallet application.

## System Requirements

### Minimum Requirements
- **Windows**: Windows 10/11 (64-bit)
- **RAM**: 8 GB (recommended 16 GB)
- **Disk Space**: 8 GB (free space for Android Studio and SDK)
- **Screen Resolution**: 1280 x 800 minimum

### Recommended Requirements
- **RAM**: 16 GB or more
- **Disk Space**: 16 GB SSD
- **CPU**: Modern multi-core processor

## Installation Steps

### Step 1: Download Android Studio

1. **Official Download**: Go to https://developer.android.com/studio
2. **Click "Download Android Studio"**
3. **Accept Terms**: Check the agreement box
4. **Download**: Choose Windows (64-bit) version (~1.2 GB)

### Step 2: Install Android Studio

#### Windows Installation:
1. **Run Installer**: Double-click the downloaded `.exe` file
2. **Welcome Screen**: Click "Next"
3. **Installation Options**: 
   - Choose "Android Studio" (default)
   - Click "Next"
4. **Configuration Settings**:
   - Leave default settings
   - Click "Next"
5. **Choose Start Menu Folder**: Click "Install"
6. **Installation Progress**: Wait for installation to complete
7. **Complete Setup**: Click "Next" then "Finish"

### Step 3: Initial Setup

#### First Launch:
1. **Start Android Studio**: From Start Menu or Desktop shortcut
2. **Import Settings**: Choose "Do not import settings" (first-time setup)
3. **Welcome Wizard**: Click "Next"
4. **Installation Type**: Choose "Standard" (recommended)
5. **Verify Settings**: Review and click "Next"
6. **Download Components**: Wait for SDK and tools to download
7. **Finish Setup**: Click "Finish" when complete

### Step 4: Configure Android Studio

#### Essential Settings:
1. **Open Preferences**: File > Settings (or Ctrl+Alt+S)
2. **Appearance & Behavior**:
   - Theme: Choose Darcula (dark) or Light
   - Font size: Adjust if needed
3. **Build, Execution, Deployment > Build Tools > Gradle**:
   - Gradle JDK: Use embedded JDK (recommended)
4. **Editor > Code Style > Kotlin**:
   - Set to "Official" style guide
5. **Plugins**: Ensure these are installed:
   - Kotlin
   - Android Support
   - Git Integration

### Step 5: Create a Virtual Device (Emulator)

#### Setup Android Emulator:
1. **Open Device Manager**: Tools > Device Manager
2. **Create Device**: Click "Create device"
3. **Choose Hardware**: 
   - Select "Pixel 6" or similar
   - Click "Next"
4. **Select System Image**:
   - Choose API 34 (Android 14.0) or latest
   - Click "Download" if not available
   - Click "Next"
5. **Verify Configuration**: 
   - AVD Name: Give it a name (e.g., "Pixel_6_API_34")
   - Click "Finish"
6. **Launch Emulator**: Click the play button to start

### Step 6: Open WorldWideCoin Project

#### Import Project:
1. **Open Android Studio**
2. **Choose Option**: Select "Open" (or File > Open)
3. **Navigate to Project**: Browse to `c:\Users\jinum\worldwidecoin\android`
4. **Select Folder**: Click on the `android` folder
5. **Wait for Gradle Sync**: Initial sync may take several minutes

#### Troubleshooting Gradle Sync:
- **JDK Issues**: See `JAVA_SETUP.md`
- **Network Issues**: Check internet connection
- **Memory Issues**: Increase Gradle heap size in settings

## Project Configuration

### Verify Project Setup:
1. **Build Variants**: Check in Build > Build Variants
2. **SDK Manager**: Ensure Android SDK is installed
3. **Gradle Wrapper**: Verify `gradle-wrapper.properties`
4. **Dependencies**: Check `app/build.gradle`

### Build the Project:
1. **Build Project**: Build > Make Project (Ctrl+F9)
2. **Run App**: Run > Run 'app' (Shift+F10)
3. **Debug App**: Run > Debug 'app' (Shift+F9)

## Essential Android Studio Features

### Key Windows:
- **Project Explorer**: Left panel - file structure
- **Code Editor**: Center - write code
- **Logcat**: Bottom - app logs and debugging
- **Build Output**: Bottom - build messages
- **Device Manager**: Tools > Device Manager

### Useful Shortcuts:
- **Ctrl+F9**: Build project
- **Shift+F10**: Run app
- **Shift+F9**: Debug app
- **Ctrl+Shift+A**: Find action
- **Alt+Enter**: Quick fix
- **Ctrl+Alt+S**: Settings
- **Ctrl+Shift+F**: Find in files

## Common Issues and Solutions

### Issue 1: Gradle Sync Failed
**Solution:**
1. Check internet connection
2. File > Invalidate Caches > Restart
3. Update Gradle wrapper if needed
4. Check JDK configuration

### Issue 2: Emulator Not Starting
**Solution:**
1. Enable virtualization in BIOS
2. Install Intel HAXM or AMD Hypervisor
3. Use hardware acceleration
4. Reduce emulator RAM if needed

### Issue 3: Build Errors
**Solution:**
1. Clean project: Build > Clean Project
2. Rebuild project: Build > Rebuild Project
3. Check for missing dependencies
4. Update Android Studio

### Issue 4: Device Not Detected
**Solution:**
1. Enable USB debugging on device
2. Install device drivers
3. Check USB cable
4. Try different USB port

## Performance Optimization

### Improve Android Studio Performance:
1. **Increase Memory**: In `studio64.exe.vmoptions`
   ```
   -Xms2048m
   -Xmx4096m
   ```
2. **Enable Power Saving**: File > Power Save Mode
3. **Disable Plugins**: Remove unused plugins
4. **SSD Storage**: Install on SSD if possible

### Gradle Optimization:
1. **Enable Gradle Daemon**: Default enabled
2. **Parallel Build**: In `gradle.properties`
   ```
   org.gradle.parallel=true
   ```
3. **Configuration Cache**: 
   ```
   org.gradle.configuration-cache=true
   ```

## Next Steps

After installing Android Studio:

1. **Open the WorldWideCoin project** from `android/` folder
2. **Sync Gradle** dependencies
3. **Create or run an emulator**
4. **Build and run** the application
5. **Start development** with the wallet features

## Additional Resources

### Official Documentation:
- [Android Studio User Guide](https://developer.android.com/studio/intro)
- [Android Development Basics](https://developer.android.com/training/basics/firstapp)
- [Kotlin for Android](https://developer.android.com/kotlin)

### Community Support:
- [Stack Overflow Android](https://stackoverflow.com/questions/tagged/android)
- [Android Developers Community](https://developer.android.com/community)
- [Reddit r/androiddev](https://www.reddit.com/r/androiddev/)

### Video Tutorials:
- [Android Studio Official Tutorials](https://www.youtube.com/c/AndroidDevelopers)
- [Kotlin Android Development](https://www.youtube.com/results?search_query=kotlin+android+development)

## Troubleshooting Help

If you encounter issues:

1. **Check the logs** in Android Studio's Build window
2. **Search online** for specific error messages
3. **Consult the official documentation**
4. **Ask in community forums**
5. **Verify system requirements** are met

The WorldWideCoin Android project is configured to work with Android Studio and includes all necessary dependencies for modern Android development with Jetpack Compose.
