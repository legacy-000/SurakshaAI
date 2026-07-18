import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { OffenderPage } from '../OffenderPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('OffenderPage', () => {
  test('renders heading', () => {
    render(<OffenderPage />, { wrapper });
    expect(screen.getByText(/Offender Profile/i)).toBeInTheDocument();
  });

  test('renders search input', () => {
    render(<OffenderPage />, { wrapper });
    expect(screen.getByPlaceholderText(/Search accused/i)).toBeInTheDocument();
  });
});