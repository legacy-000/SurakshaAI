import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { ForecastPage } from '../ForecastPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('ForecastPage', () => {
  test('renders heading', () => {
    render(<ForecastPage />, { wrapper });
    expect(screen.getByText(/Crime Forecast/i)).toBeInTheDocument();
  });

  test('renders tabs after loading', async () => {
    render(<ForecastPage />, { wrapper });
    await waitFor(() => expect(screen.getAllByText(/By Crime Type/i).length).toBeGreaterThan(0));
  });
});