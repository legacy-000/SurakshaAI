import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { SearchPage } from '../SearchPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('SearchPage', () => {
  test('renders heading', () => {
    render(<SearchPage />, { wrapper });
    expect(screen.getByText(/Case Search/i)).toBeInTheDocument();
  });

  test('renders text input', () => {
    render(<SearchPage />, { wrapper });
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });
});