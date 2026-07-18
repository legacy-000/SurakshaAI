import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { GroupManagerPage } from '../GroupManagerPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('GroupManagerPage', () => {
  test('renders heading', () => {
    render(<GroupManagerPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /Group Manager/i })).toBeInTheDocument();
  });

  test('renders tabs', async () => {
    render(<GroupManagerPage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/active/i)).toBeInTheDocument());
  });
});