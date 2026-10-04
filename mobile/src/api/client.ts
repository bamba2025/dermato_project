export interface SessionStore {
  read(): Promise<string | null>;
  write(token: string): Promise<void>;
  clear(): Promise<void>;
}

export interface User {
  id: string;
  email: string;
  role: 'USER' | 'DERMATOLOGIST' | 'ADMIN';
  created_at: string;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'bearer';
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message);
  }
}

export class ApiClient {
  private access: string | null = null;
  private refreshInFlight: Promise<boolean> | null = null;
  private generation = 0;

  constructor(
    private readonly baseUrl: string,
    private readonly store: SessionStore,
  ) {}

  private async send<T>(
    path: string,
    method = 'GET',
    body?: object,
    token?: string,
  ): Promise<T> {
    if (this.baseUrl.includes('.invalid')) {
      throw new Error('Le service de production doit être configuré.');
    }
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(this.baseUrl + path, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      if (!response.ok) {
        const messages: Record<number, string> = {
          401: 'Identifiants incorrects ou session expirée.',
          409: 'Inscription impossible avec cette adresse.',
          422: 'Vérifiez votre adresse e-mail et votre mot de passe.',
          429: 'Trop de tentatives. Réessayez dans une minute.',
          503: 'Service temporairement indisponible.',
        };
        throw new ApiError(
          response.status,
          messages[response.status] ?? 'La demande a échoué.',
        );
      }
      return response.status === 204 ? (undefined as T) : await response.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  async authenticate(
    email: string,
    password: string,
    registering: boolean,
  ): Promise<void> {
    const tokens = await this.send<Tokens>(
      registering ? '/auth/register' : '/auth/login',
      'POST',
      {
        email,
        password,
        ...(registering ? { application_consent: true } : {}),
      },
    );
    await this.store.write(tokens.refresh_token);
    this.access = tokens.access_token;
    this.generation++;
  }

  async restore(): Promise<boolean> {
    if (this.refreshInFlight) {
      return this.refreshInFlight;
    }
    const generation = this.generation;
    const refresh = async () => {
      const raw = await this.store.read();
      if (!raw) {
        return false;
      }
      try {
        const tokens = await this.send<Tokens>('/auth/refresh', 'POST', {
          refresh_token: raw,
        });
        if (generation !== this.generation) {
          return false;
        }
        await this.store.write(tokens.refresh_token);
        this.access = tokens.access_token;
        return true;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          if (generation !== this.generation) {
            return false;
          }
          this.access = null;
          await this.store.clear();
          return false;
        }
        // Une panne réseau ne supprime pas une session encore récupérable.
        throw error;
      }
    };
    this.refreshInFlight = refresh();
    try {
      return await this.refreshInFlight;
    } finally {
      this.refreshInFlight = null;
    }
  }

  async me(): Promise<User> {
    try {
      return await this.send<User>(
        '/me',
        'GET',
        undefined,
        this.access ?? undefined,
      );
    } catch (error) {
      if (
        error instanceof ApiError &&
        error.status === 401 &&
        (await this.restore())
      ) {
        return this.send<User>(
          '/me',
          'GET',
          undefined,
          this.access ?? undefined,
        );
      }
      throw error;
    }
  }

  async logout(): Promise<void> {
    this.generation++;
    const access = this.access;
    this.access = null;
    try {
      // Éviter une réécriture du Keychain après la déconnexion.
      await this.refreshInFlight;
      const raw = await this.store.read();
      if (raw && access) {
        await this.send('/auth/logout', 'POST', { refresh_token: raw }, access);
      }
    } finally {
      this.access = null;
      await this.store.clear();
    }
  }
}
