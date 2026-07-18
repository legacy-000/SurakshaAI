import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { InboxPage } from '../InboxPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('InboxPage', () => {
  test('renders inbox heading', async () => {
    render(<InboxPage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/Message Inbox/i)).toBeInTheDocument());
  });

  test('renders messages from API', async () => {
    render(<InboxPage />, { wrapper });
    await waitFor(() => expect(screen.getByText('Test Subject')).toBeInTheDocument());
  });

  test('renders new message button', async () => {
    render(<InboxPage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/New Message/i)).toBeInTheDocument());
  });

  test('renders priority badge', async () => {
    render(<InboxPage />, { wrapper });
    await waitFor(() => expect(screen.getByText(/HIGH/i)).toBeInTheDocument());
  });
});