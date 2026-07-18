import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import DatabaseModePage from '../DatabaseModePage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('DatabaseModePage', () => {
  test('renders heading', () => {
    render(<DatabaseModePage />, { wrapper });
    expect(screen.getByText(/Database Mode/i)).toBeInTheDocument();
  });

  test('renders text input', () => {
    render(<DatabaseModePage />, { wrapper });
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });
});