module.exports = {
  preset: 'react-native',
  // Premier chargement des composants natifs par Babel, notamment sous Windows.
  testTimeout: 30000,
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|react-native-safe-area-context)/)',
  ],
  setupFilesAfterEnv: ['./jest.setup.js'],
};
