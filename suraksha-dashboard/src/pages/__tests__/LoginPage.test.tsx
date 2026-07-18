import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { LoginPage } from '../LoginPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('LoginPage', () => {
  test('renders login form', () => {
    render(<LoginPage />, { wrapper });
    expect(screen.getByText(/sign in/i)).toBeInTheDocument();
  });

  test('renders KGID input', () => {
    render(<LoginPage />, { wrapper });
    expect(screen.getByPlaceholderText(/enter your kgid/i)).toBeInTheDocument();
  });

  test('renders password input', () => {
    render(<LoginPage />, { wrapper });
    expect(screen.getByPlaceholderText(/enter your password/i)).toBeInTheDocument();
  });
});