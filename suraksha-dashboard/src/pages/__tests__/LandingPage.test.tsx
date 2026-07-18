import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { LandingPage } from '../LandingPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('LandingPage', () => {
  test('renders Suraksha AI heading', () => {
    render(<LandingPage />, { wrapper });
    const elements = screen.getAllByText(/Suraksha AI/i);
    expect(elements.length).toBeGreaterThanOrEqual(2);
  });

  test('renders get started link', () => {
    render(<LandingPage />, { wrapper });
    expect(screen.getByText(/Get Started/i)).toBeInTheDocument();
  });

  test('renders sign in link', () => {
    render(<LandingPage />, { wrapper });
    expect(screen.getByText(/Sign In/i)).toBeInTheDocument();
  });
});