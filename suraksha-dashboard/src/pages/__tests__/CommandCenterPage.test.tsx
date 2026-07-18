import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { CommandCenterPage } from '../CommandCenterPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('CommandCenterPage', () => {
  test('renders heading', () => {
    render(<CommandCenterPage />, { wrapper });
    expect(screen.getByText(/Command Center/i)).toBeInTheDocument();
  });

  test('renders table with district data', () => {
    render(<CommandCenterPage />, { wrapper });
    expect(screen.getByText('Bengaluru Urban')).toBeInTheDocument();
  });
});