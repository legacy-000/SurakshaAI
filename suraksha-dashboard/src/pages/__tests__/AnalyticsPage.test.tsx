import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { AnalyticsPage } from '../AnalyticsPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('AnalyticsPage', () => {
  test('renders heading', () => {
    render(<AnalyticsPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /analytics/i })).toBeInTheDocument();
  });

  test('renders chart area', () => {
    render(<AnalyticsPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /Crime Analytics/i })).toBeInTheDocument();
  });
});