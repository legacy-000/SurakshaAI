import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { CaseRegistrationPage } from '../CaseRegistrationPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('CaseRegistrationPage', () => {
  test('renders heading', () => {
    render(<CaseRegistrationPage />, { wrapper });
    expect(screen.getByText(/Case Registration/i)).toBeInTheDocument();
  });

  test('renders form fields', () => {
    render(<CaseRegistrationPage />, { wrapper });
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });

  test('renders submit button', () => {
    render(<CaseRegistrationPage />, { wrapper });
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});