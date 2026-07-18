import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { AlertsPage } from '../AlertsPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('AlertsPage', () => {
  test('renders heading', () => {
    render(<AlertsPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /Alerts/i })).toBeInTheDocument();
  });

  test('renders filter tabs', async () => {
    render(<AlertsPage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/all/i)).toBeInTheDocument());
  });
});