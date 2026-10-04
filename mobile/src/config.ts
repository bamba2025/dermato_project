// adb reverse tcp:8000 tcp:8000 pour Android ; localhost sur le simulateur iOS.
// Configurer un endpoint HTTPS contrôlé avant toute distribution.
export const API_BASE_URL = __DEV__
  ? 'http://localhost:8000/api/v1'
  : 'https://api.example.invalid/api/v1';
