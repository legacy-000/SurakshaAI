import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { ChargesheetPage } from '../ChargesheetPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('ChargesheetPage', () => {
  test('renders heading', () => {
    render(<ChargesheetPage />, { wrapper });
    expect(screen.getByText(/Chargesheet Preparation/i)).toBeInTheDocument();
  });

  test('renders generate button', () => {
    render(<ChargesheetPage />, { wrapper });
    expect(screen.getByText(/generate/i)).toBeInTheDocument();
  });
});