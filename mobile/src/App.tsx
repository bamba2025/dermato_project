import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { ApiClient, User } from './api/client';
import { API_BASE_URL } from './config';
import { secureSessionStore } from './auth/secureStore';

const api = new ApiClient(API_BASE_URL, secureSessionStore);

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [registering, setRegistering] = useState(false);
  const [consented, setConsented] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api
      .restore()
      .then(async restored => {
        if (restored) {
          const current = await api.me();
          if (active) {
            setUser(current);
          }
        }
      })
      .catch(() => {
        if (active) {
          setError(
            'Connexion indisponible. Vérifiez votre accès Internet puis réessayez.',
          );
        }
      })
      .finally(() => {
        if (active) {
          setBusy(false);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  async function submit() {
    setBusy(true);
    setError('');
    try {
      await api.authenticate(email.trim(), password, registering);
      setUser(await api.me());
      setPassword('');
    } catch (failure) {
      setError(
        failure instanceof Error ? failure.message : 'Connexion impossible.',
      );
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    setBusy(true);
    setError('');
    try {
      await api.logout();
    } catch {
      setError('Session locale effacée. Le serveur était indisponible.');
    } finally {
      setUser(null);
      setBusy(false);
    }
  }

  const allowed =
    email.includes('@') &&
    password.length >= 12 &&
    password.length <= 128 &&
    (!registering || consented) &&
    !busy;

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="dark-content" backgroundColor="#F5F8F4" />
      <SafeAreaView style={styles.screen}>
        <KeyboardAvoidingView
          style={styles.flex}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <ScrollView
            contentContainerStyle={styles.content}
            keyboardShouldPersistTaps="handled"
          >
            <View style={styles.brandRow}>
              <View style={styles.mark}>
                <Text style={styles.markText}>d.</Text>
              </View>
              <Text style={styles.brand}>derma</Text>
            </View>
            <Text style={styles.eyebrow}>VOTRE PEAU, AU FIL DU TEMPS</Text>
            <Text style={styles.title}>
              {user
                ? 'Bienvenue dans votre espace.'
                : 'Prenez le temps de connaître votre peau.'}
            </Text>
            <Text style={styles.subtitle}>
              Un espace personnel pour accompagner votre suivi cutané.
            </Text>
            {error ? (
              <Text accessibilityRole="alert" style={styles.error}>
                {error}
              </Text>
            ) : null}
            {busy ? (
              <ActivityIndicator
                color="#214E40"
                accessibilityLabel="Chargement"
              />
            ) : null}
            {user ? (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>Votre compte</Text>
                <Text style={styles.body}>{user.email}</Text>
                <Text style={styles.note}>
                  Votre espace est prêt. La capture guidée sera disponible après
                  la validation du module caméra.
                </Text>
                <Pressable
                  accessibilityRole="button"
                  disabled={busy}
                  onPress={logout}
                  style={styles.secondary}
                >
                  <Text style={styles.secondaryText}>Se déconnecter</Text>
                </Pressable>
              </View>
            ) : (
              <View style={styles.card}>
                <Text style={styles.cardTitle}>
                  {registering
                    ? 'Créer votre compte'
                    : 'Retrouver votre espace'}
                </Text>
                <Text style={styles.label}>Adresse e-mail</Text>
                <TextInput
                  accessibilityLabel="Adresse e-mail"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                  autoComplete="email"
                  textContentType="emailAddress"
                  style={styles.input}
                  editable={!busy}
                  placeholder="vous@exemple.com"
                  placeholderTextColor="#7C857E"
                />
                <Text style={styles.label}>Mot de passe</Text>
                <TextInput
                  accessibilityLabel="Mot de passe"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  autoCapitalize="none"
                  autoCorrect={false}
                  style={styles.input}
                  textContentType={registering ? 'newPassword' : 'password'}
                  maxLength={128}
                  editable={!busy}
                  placeholder="12 caractères minimum"
                  placeholderTextColor="#7C857E"
                />
                {registering ? (
                  <View style={styles.consent}>
                    <Switch
                      accessibilityLabel="Accepter l’utilisation de l’application"
                      value={consented}
                      onValueChange={setConsented}
                      disabled={busy}
                      trackColor={{ true: '#214E40' }}
                    />
                    <Text style={styles.consentText}>
                      J’accepte le traitement de mes données pour utiliser
                      l’application. Cela n’autorise ni la recherche ni
                      l’entraînement de l’IA.
                    </Text>
                  </View>
                ) : null}
                <Pressable
                  accessibilityRole="button"
                  disabled={!allowed}
                  onPress={submit}
                  style={[styles.primary, !allowed && styles.disabled]}
                >
                  <Text style={styles.primaryText}>
                    {registering ? 'Créer mon compte' : 'Me connecter'}
                  </Text>
                </Pressable>
                <Pressable
                  accessibilityRole="button"
                  disabled={busy}
                  style={styles.link}
                  onPress={() => {
                    setRegistering(!registering);
                    setError('');
                    setPassword('');
                  }}
                >
                  <Text style={styles.secondaryText}>
                    {registering ? 'J’ai déjà un compte' : 'Créer un compte'}
                  </Text>
                </Pressable>
              </View>
            )}
            <Text style={styles.footer}>
              L’analyse de peau ne remplace pas un avis dermatologique.
            </Text>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  screen: { flex: 1, backgroundColor: '#F5F8F4' },
  content: { padding: 24, paddingTop: 32, gap: 18, flexGrow: 1 },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  mark: {
    backgroundColor: '#214E40',
    borderRadius: 16,
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
  },
  markText: { fontSize: 32, color: '#FFFFFF', fontWeight: '600' },
  brand: { fontSize: 28, color: '#214E40', fontWeight: '600' },
  eyebrow: {
    fontSize: 11,
    letterSpacing: 2,
    color: '#526C5B',
    fontWeight: '600',
  },
  title: { fontSize: 34, lineHeight: 40, fontWeight: '600', color: '#183D31' },
  subtitle: { fontSize: 16, lineHeight: 24, color: '#657168' },
  card: {
    backgroundColor: '#FFFFFF',
    padding: 22,
    borderRadius: 22,
    marginTop: 12,
    gap: 12,
    borderWidth: 1,
    borderColor: '#E1E9DF',
  },
  cardTitle: {
    fontSize: 21,
    fontWeight: '600',
    color: '#183D31',
    marginBottom: 8,
  },
  label: { fontSize: 13, color: '#3D5348', fontWeight: '500' },
  input: {
    borderWidth: 1,
    borderColor: '#D8E1D6',
    borderRadius: 12,
    padding: 14,
    color: '#183D31',
    fontSize: 16,
    backgroundColor: '#FBFCFA',
  },
  primary: {
    backgroundColor: '#214E40',
    minHeight: 52,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 8,
  },
  primaryText: { fontSize: 16, fontWeight: '600', color: '#FFFFFF' },
  disabled: { opacity: 0.45 },
  secondary: {
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#D8E1D6',
    alignItems: 'center',
  },
  secondaryText: { fontSize: 14, color: '#214E40', fontWeight: '600' },
  link: { padding: 12, alignItems: 'center' },
  consent: { flexDirection: 'row', gap: 10, alignItems: 'flex-start' },
  consentText: { flex: 1, fontSize: 12, lineHeight: 18, color: '#657168' },
  body: { fontSize: 16, color: '#3D5348' },
  note: { fontSize: 14, lineHeight: 22, color: '#657168' },
  error: {
    fontSize: 14,
    lineHeight: 20,
    color: '#993C32',
    padding: 12,
    backgroundColor: '#FCEEE9',
    borderRadius: 10,
  },
  footer: {
    fontSize: 12,
    lineHeight: 18,
    textAlign: 'center',
    color: '#657168',
    marginTop: 12,
  },
});
