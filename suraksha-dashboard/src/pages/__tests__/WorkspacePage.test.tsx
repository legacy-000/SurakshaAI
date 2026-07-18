import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { WorkspacePage } from '../WorkspacePage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('WorkspacePage', () => {
  test('renders workspace heading', async () => {
    render(<WorkspacePage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/workspace/i)).toBeInTheDocument());
  });

  test('renders create investigation button', async () => {
    render(<WorkspacePage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/create/i)).toBeInTheDocument());
  });

  test('renders investigation list', async () => {
    render(<WorkspacePage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/Test Investigation/i)).toBeInTheDocument());
  });
});
