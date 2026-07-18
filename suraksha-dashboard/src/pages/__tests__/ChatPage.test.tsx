import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { ChatPage } from '../ChatPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('ChatPage', () => {
  test('renders chat input', () => {
    render(<ChatPage />, { wrapper });
    expect(screen.getByPlaceholderText(/Ask about crime data/i)).toBeInTheDocument();
  });

  test('renders greeting message', () => {
    render(<ChatPage />, { wrapper });
    expect(screen.getByText(/I am Suraksha AI/i)).toBeInTheDocument();
  });
});