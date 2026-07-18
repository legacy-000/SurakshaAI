import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { AccessControlPage } from '../AccessControlPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('AccessControlPage', () => {
  test('renders heading', () => {
    render(<AccessControlPage />, { wrapper });
    expect(screen.getByText(/Access Control/i)).toBeInTheDocument();
  });

  test('renders buttons', () => {
    render(<AccessControlPage />, { wrapper });
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});