import { ApiClient, ApiError, SessionStore } from '../src/api/client';

function store(initial: string | null = null) {
  let token = initial;
  const result: SessionStore = {
    read: jest.fn(async () => token),
    write: jest.fn(async value => {
      token = value;
    }),
    clear: jest.fn(async () => {
      token = null;
    }),
  };
  return result;
}
function response(status: number, data = {}) {
  return { ok: status >= 200 && status < 300, status, json: async () => data };
}
const fetchMock = jest.fn();
beforeEach(() => {
  fetchMock.mockReset();
  globalThis.fetch = fetchMock;
});

test('saves only the refresh token in the secure store', async () => {
  const secure = store();
  const api = new ApiClient('http://localhost/api/v1', secure);
  fetchMock.mockResolvedValue(
    response(200, { access_token: 'access', refresh_token: 'refresh' }),
  );
  await api.authenticate('patient@example.com', 'test-password', false);
  expect(secure.write).toHaveBeenCalledWith('refresh');
  expect(secure.write).not.toHaveBeenCalledWith('access');
});
test('simultaneous restoration sends a single rotation request', async () => {
  const secure = store('old-refresh');
  const api = new ApiClient('http://localhost/api/v1', secure);
  fetchMock.mockResolvedValue(
    response(200, { access_token: 'access', refresh_token: 'new-refresh' }),
  );
  expect(await Promise.all([api.restore(), api.restore()])).toEqual([
    true,
    true,
  ]);
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(secure.write).toHaveBeenCalledWith('new-refresh');
});
test('invalid session is cleared, network failure preserves it', async () => {
  const secure = store('refresh');
  const api = new ApiClient('http://localhost/api/v1', secure);
  fetchMock.mockRejectedValueOnce(new Error('offline'));
  await expect(api.restore()).rejects.toThrow('offline');
  expect(secure.clear).not.toHaveBeenCalled();
  fetchMock.mockResolvedValueOnce(response(401));
  expect(await api.restore()).toBe(false);
  expect(secure.clear).toHaveBeenCalledTimes(1);
});
test('expired access retries once after refreshing', async () => {
  const api = new ApiClient('http://localhost/api/v1', store('refresh'));
  fetchMock
    .mockResolvedValueOnce(response(401))
    .mockResolvedValueOnce(
      response(200, { access_token: 'renewed', refresh_token: 'new' }),
    )
    .mockResolvedValueOnce(response(200, { id: 'user-id' }));
  expect((await api.me()).id).toBe('user-id');
  expect(fetchMock).toHaveBeenCalledTimes(3);
  expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe(
    'Bearer renewed',
  );
});
test('logout clears the session even when server is unreachable', async () => {
  const secure = store();
  const api = new ApiClient('http://localhost/api/v1', secure);
  fetchMock.mockResolvedValueOnce(
    response(200, { access_token: 'access', refresh_token: 'refresh' }),
  );
  await api.authenticate('patient@example.com', 'test-password', false);
  fetchMock.mockRejectedValueOnce(new Error('offline'));
  await expect(api.logout()).rejects.toThrow('offline');
  expect(secure.clear).toHaveBeenCalledTimes(1);
});
test('placeholder production URL refuses a request', async () => {
  const api = new ApiClient('https://api.example.invalid/api/v1', store());
  await expect(api.me()).rejects.toThrow('configuré');
  expect(fetchMock).not.toHaveBeenCalled();
});
test('server errors use safe messages', async () => {
  const api = new ApiClient('http://localhost/api/v1', store());
  fetchMock.mockResolvedValueOnce(response(429));
  await expect(
    api.authenticate('patient@example.com', 'test-password', false),
  ).rejects.toBeInstanceOf(ApiError);
});
