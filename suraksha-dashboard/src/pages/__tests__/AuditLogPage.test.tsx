import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { AuditLogPage } from '../AuditLogPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('AuditLogPage', () => {
  test('renders audit log heading', () => {
    render(<AuditLogPage />, { wrapper });
    expect(screen.getByText(/Audit Log/i)).toBeInTheDocument();
  });

  test('renders log entries', async () => {
    render(<AuditLogPage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/User logged in/i)).toBeInTheDocument());
  });

  test('renders search input', () => {
    render(<AuditLogPage />, { wrapper });
    expect(screen.getByPlaceholderText(/search logs/i)).toBeInTheDocument();
  });
});
