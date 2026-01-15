class AppConfig {
  // TODO: REPLACE WITH YOUR ACTUAL WOOCOMMERCE SITE URL
  static const String baseUrl = 'https://your-wordpress-site.local'; 

  // TODO: REPLACE WITH YOUR REAL CONSUMER KEY
  static const String consumerKey = 'ck_1ac020fec4811da696868e124e0839bae7557c39';

  // TODO: REPLACE WITH YOUR REAL CONSUMER SECRET
  static const String consumerSecret = 'cs_5f7280bb565d7fe063b6cc44cf4f37089adb5ea7';

  // Automation Service URL (FastAPI)
  // Use 10.0.2.2 for Android Emulator to access host localhost
  // Use actual IP for physical device
  static const String automationApiUrl = 'http://10.0.2.2:8000'; 
}
