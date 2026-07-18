import React from 'react';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('App', () => {
  test('renders login page by default', () => {
    render(<App />);
    const elements = screen.getAllByText(/Suraksha AI/i);
    expect(elements.length).toBeGreaterThan(0);
  });
});