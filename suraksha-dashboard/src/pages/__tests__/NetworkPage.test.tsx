import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../context/AuthContext';
import { LanguageProvider } from '../../context/LanguageContext';
import { NetworkPage } from '../NetworkPage';

jest.mock('../../services/api', () => ({
  api: {
    getNetwork: jest.fn().mockImplementation((_name: string, _searchType?: string) => Promise.resolve({
      nodes: [
        { id: 'case_101', label: 'Case #101', node_type: 'case', cases: 3, crime_type: 'Theft', risk_tier: 'LOW', sub_label: 'Theft' },
        { id: 'case_102', label: 'Case #102', node_type: 'case', cases: 2, crime_type: 'Theft', risk_tier: 'LOW', sub_label: 'Theft' },
        { id: 'n0', label: 'Ravi Kumar', node_type: 'accused', cases: 3, risk_tier: 'ELEVATED', crime_type: 'Theft', person_id: 'Ravi Kumar', sub_label: '3 cases' },
        { id: 'n1', label: 'Suresh P', node_type: 'accused', cases: 2, risk_tier: 'MODERATE', crime_type: 'Robbery', person_id: 'Suresh P', sub_label: '2 cases' },
      ],
      edges: [
        { id: 'e0', source: 'case_101', target: 'n0', weight: 1, shared_cases: [101], connection_basis: 'accused in Case #101' },
        { id: 'e1', source: 'case_101', target: 'n1', weight: 1, shared_cases: [101], connection_basis: 'accused in Case #101' },
        { id: 'e2', source: 'case_102', target: 'n0', weight: 1, shared_cases: [102], connection_basis: 'accused in Case #102' },
      { id: 'e3', source: 'case_101', target: 'case_102', weight: 1, shared_cases: [101, 102], connection_basis: 'shared: Ravi Kumar', edge_type: 'case_case' },
    ],
    })),
    networkAiQuery: jest.fn().mockRejectedValue(new Error('fallback')),
  },
}));

const wrapper = ({ children }: any) => (
  <BrowserRouter><AuthProvider><LanguageProvider>{children}</LanguageProvider></AuthProvider></BrowserRouter>
);

describe('NetworkPage', () => {
  test('renders heading and search input', () => {
    render(<NetworkPage />, { wrapper });
    expect(screen.getByRole('heading', { name: /Network/i })).toBeInTheDocument();
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });

  test('loads and displays network graph on search', async () => {
    render(<NetworkPage />, { wrapper });
    const inputs = screen.getAllByRole('textbox');
    const searchInput = inputs[0];
    fireEvent.change(searchInput, { target: { value: 'Ravi' } });
    fireEvent.keyDown(searchInput, { key: 'Enter' });
    await waitFor(() => {
      expect(screen.getByText(/Network Metrics/)).toBeInTheDocument();
    });
  });

  test('shows network metrics after loading data', async () => {
    render(<NetworkPage />, { wrapper });
    const inputs = screen.getAllByRole('textbox');
    fireEvent.change(inputs[0], { target: { value: 'Ravi' } });
    fireEvent.keyDown(inputs[0], { key: 'Enter' });
    await waitFor(() => {
      expect(screen.getByText(/Network Density/)).toBeInTheDocument();
      expect(screen.getByText(/Central Figures/)).toBeInTheDocument();
    });
  });

  test('renders NetworkAI panel', () => {
    render(<NetworkPage />, { wrapper });
    expect(screen.getByText(/NetworkAI/)).toBeInTheDocument();
  });
});