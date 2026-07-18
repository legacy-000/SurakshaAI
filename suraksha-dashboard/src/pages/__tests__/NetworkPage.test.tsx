import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { NetworkPage } from '../NetworkPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('NetworkPage', () => {
  test('renders heading', () => {
    render(<NetworkPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /Network/i })).toBeInTheDocument();
  });

  test('renders search input', () => {
    render(<NetworkPage />, { wrapper });
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });
});