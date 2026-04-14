# Mobile Build Pipeline

## Prerequisites
- Node.js 22+
- Android Studio (for Android builds)
- Xcode 15+ (for iOS builds, macOS only)

## Setup

### Add platforms
```bash
cd frontend
npx next build && npx next export
npx cap add android
npx cap add ios
npx cap sync
```

### Android
```bash
npx cap open android
# Build APK: Build > Build Bundle / APK > Build APK
# Or from CLI:
cd android && ./gradlew assembleRelease
```

### iOS
```bash
npx cap open ios
# Build in Xcode: Product > Archive
```

## Signing

### Android
1. Generate a keystore: `keytool -genkey -v -keystore searchparty.keystore -alias searchparty -keyalg RSA -keysize 2048 -validity 10000`
2. Add to `android/app/build.gradle` signingConfigs
3. Store keystore password in CI secrets

### iOS
1. Create App ID in Apple Developer portal
2. Create provisioning profiles (Development + Distribution)
3. Configure in Xcode signing settings

## Battery Optimization

### GPS Tracking
- Use `maximumAge: 5000` to allow cached positions
- Reduce accuracy to `enableHighAccuracy: false` when team is stationary
- Increase polling interval in standby mode (60s vs 5s deployed)

### Network
- Batch sync operations instead of individual requests
- Only sync when on WiFi for large data (tile downloads)
- Compress payloads when syncing GPS tracks

### Display
- Use dark mode to reduce OLED power consumption
- Reduce map tile quality/resolution for lower bandwidth and rendering cost
- Dim screen during tracking-only mode (no active map interaction)

### Background Processing
- Use Capacitor Background Runner for GPS tracking when app is backgrounded
- Register background fetch for periodic sync attempts
- Minimize wake locks — use passive location updates when possible

## Testing
- Test on physical devices (emulators don't have real GPS/compass/camera)
- Test offline scenarios by enabling airplane mode
- Test battery drain over 4-8 hour simulated field operation
- Test GPS accuracy in forested and canyon environments
