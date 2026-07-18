import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { DashboardPage } from '../DashboardPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('DashboardPage', () => {
  test('renders heading', () => {
    render(<DashboardPage />, { wrapper });
    expect(screen.getByText(/Karnataka State Police/i)).toBeInTheDocument();
  });

  test('renders KPI cards', () => {
    render(<DashboardPage />, { wrapper });
    expect(screen.getByText('Total Cases')).toBeInTheDocument();
    expect(screen.getByText('12,847')).toBeInTheDocument();
  });

  test('renders chart section', () => {
    render(<DashboardPage />, { wrapper });
    expect(screen.getByText(/Crime Trends/i)).toBeInTheDocument();
  });
});