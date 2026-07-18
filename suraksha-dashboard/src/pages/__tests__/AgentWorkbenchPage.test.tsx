import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { AgentWorkbenchPage } from '../AgentWorkbenchPage';

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('AgentWorkbenchPage', () => {
  test('renders workbench heading', () => {
    render(<AgentWorkbenchPage />, { wrapper });
    expect(screen.getByText(/Agent Workbench/i)).toBeInTheDocument();
  });

  test('renders agent cards', () => {
    render(<AgentWorkbenchPage />, { wrapper });
    expect(screen.getByText('Database Agent')).toBeInTheDocument();
    expect(screen.getByText('Trend Agent')).toBeInTheDocument();
  });

  test('renders query input', () => {
    render(<AgentWorkbenchPage />, { wrapper });
    expect(screen.getByPlaceholderText(/Ask the Commander/i)).toBeInTheDocument();
  });
});