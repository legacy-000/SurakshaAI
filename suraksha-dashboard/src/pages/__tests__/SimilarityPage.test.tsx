import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { SimilarityPage } from '../SimilarityPage';



const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('SimilarityPage', () => {
  test('renders similarity heading', () => {
    render(<SimilarityPage />, { wrapper });
    expect(screen.getByText(/similarity/i)).toBeInTheDocument();
  });

  test('renders case select input', () => {
    render(<SimilarityPage />, { wrapper });
    expect(screen.getByText(/select case/i)).toBeInTheDocument();
  });

  test('renders pattern bot section', () => {
    render(<SimilarityPage />, { wrapper });
    const elements = screen.getAllByText(/PatternBot/i);
    expect(elements.length).toBeGreaterThanOrEqual(2);
  });
});
