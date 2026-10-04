import * as Keychain from 'react-native-keychain';
import { SessionStore } from '../api/client';

const service = 'derma.refresh.v1';

export const secureSessionStore: SessionStore = {
  async read() {
    const value = await Keychain.getGenericPassword({ service });
    return value ? value.password : null;
  },
  async write(token) {
    await Keychain.setGenericPassword('session', token, {
      service,
      accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
    });
  },
  async clear() {
    await Keychain.resetGenericPassword({ service });
  },
};
