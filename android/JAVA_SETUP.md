# Java Setup Guide for WorldWideCoin Android Development

## Issue: JDK 17+ Required Error

You're encountering this error because the Android project requires Java 11 or higher, but your system doesn't have the correct Java version configured.

## Quick Solutions

### Option 1: Install Java 11 (Recommended)

**Windows:**
1. Download Java 11 from: https://adoptium.net/temurin/releases?version=11
2. Run the installer
3. Set JAVA_HOME environment variable:
   ```cmd
   set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-11.0.x.x-hotspot
   set PATH=%JAVA_HOME%\bin;%PATH%
   ```

**Verify installation:**
```cmd
java -version
javac -version
echo %JAVA_HOME%
```

### Option 2: Use Android Studio's Built-in JDK

1. Open Android Studio
2. Go to File > Settings > Build, Execution, Deployment > Build Tools > Gradle
3. Set Gradle JDK to use the embedded JDK (usually JDK 17)
4. Click Apply and restart Android Studio

### Option 3: Update System PATH

Add Java to your system PATH:
1. Press Windows Key + R, type `sysdm.cpl`
2. Go to Advanced > Environment Variables
3. Edit PATH and add: `C:\Program Files\Eclipse Adoptium\jdk-11.0.x.x-hotspot\bin`
4. Create JAVA_HOME: `C:\Program Files\Eclipse Adoptium\jdk-11.0.x.x-hotspot`

### Option 4: VS Code Java Extension

If using VS Code:
1. Install Java Extension Pack
2. Open Command Palette (Ctrl+Shift+P)
3. Type "Java: Install Java Extensions"
4. Follow the prompts to install JDK 11

## IDE-Specific Fixes

### Android Studio
```gradle
// In android/app/build.gradle - already updated
compileOptions {
    sourceCompatibility JavaVersion.VERSION_11
    targetCompatibility JavaVersion.VERSION_11
}

kotlinOptions {
    jvmTarget = '11'
}
```

### VS Code
Add to `.vscode/settings.json`:
```json
{
    "java.jdt.ls.java.home": "C:\\Program Files\\Eclipse Adoptium\\jdk-11.0.x.x-hotspot",
    "java.home": "C:\\Program Files\\Eclipse Adoptium\\jdk-11.0.x.x-hotspot"
}
```

## Verification Commands

Run these to verify your setup:

```cmd
# Check Java version
java -version

# Check Java compiler
javac -version

# Check JAVA_HOME
echo %JAVA_HOME%

# Check if Java is in PATH
where java
```

## Expected Output

You should see something like:
```
java version "11.0.xx" 202x-xx-xx
Java(TM) SE Runtime Environment (build 11.0.xx+xx)
Java HotSpot(TM) 64-Bit Server VM (build 11.0.xx+xx, mixed mode, sharing)
```

## Project Configuration

The Android project is now configured to use Java 11:
- Updated `build.gradle` with Java 11 compatibility
- Added `gradle.properties` with Java toolchain settings
- Compatible with most development environments

## Building the Project

Once Java is properly configured:

```cmd
cd android
./gradlew build
```

Or open in Android Studio and sync the project.

## Troubleshooting

### "java command not found"
- Java is not in your PATH
- Install Java or add to PATH

### "Unsupported class file major version"
- Java version mismatch
- Ensure you're using Java 11

### "Gradle could not find Java"
- Set JAVA_HOME environment variable
- Restart your IDE after setting

### "Could not resolve org.jetbrains.kotlin:kotlin-gradle-plugin"
- Check internet connection
- Try building with `--offline` flag first

## Alternative: Use Docker

If you prefer containerized development:

```dockerfile
FROM openjdk:11-jdk
WORKDIR /app
COPY . .
RUN ./gradlew build
```

## Next Steps

1. Install Java 11 using one of the methods above
2. Restart your IDE
3. Open the Android project
4. Sync Gradle
5. Build the project

The project should now compile successfully with Java 11.
