import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { CoordinationPage } from '../CoordinationPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('CoordinationPage', () => {
  test('renders heading', () => {
    render(<CoordinationPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /Coordination/i })).toBeInTheDocument();
  });

  test('renders buttons', () => {
    render(<CoordinationPage />, { wrapper });
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});