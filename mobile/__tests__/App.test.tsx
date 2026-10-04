/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { Text } from 'react-native';
import App from '../App';

test('shows authentication without pretending a camera is available', async () => {
  let renderer!: ReactTestRenderer.ReactTestRenderer;
  await ReactTestRenderer.act(async () => {
    renderer = ReactTestRenderer.create(<App />);
  });
  const texts = renderer.root
    .findAllByType(Text)
    .map(node => node.props.children);
  expect(texts).toContain('Me connecter');
  expect(texts).toContain('Créer un compte');
  expect(texts).toContain(
    'L’analyse de peau ne remplace pas un avis dermatologique.',
  );
  await ReactTestRenderer.act(async () => renderer.unmount());
});
