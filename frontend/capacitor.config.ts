import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.searchparty.app",
  appName: "SearchParty",
  webDir: "out",
  plugins: {
    PushNotifications: {
      presentationOptions: ["badge", "sound", "alert"],
    },
    SplashScreen: {
      launchAutoHide: true,
      showSpinner: false,
    },
    Geolocation: {
      // Request always-on permission for background tracking
    },
  },
  android: {
    allowMixedContent: false,
    backgroundColor: "#ffffff",
  },
  ios: {
    backgroundColor: "#ffffff",
    preferredContentMode: "mobile",
  },
};

export default config;
