import { Component, ErrorInfo, ReactNode } from 'react';

interface Props { children: ReactNode; }
interface State { hasError: boolean; error: Error | null; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) { return { hasError: true, error }; }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info);
  }

  handleRetry = () => this.setState({ hasError: false, error: null });

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 48, textAlign: 'center' }}>
          <h2>Something went wrong</h2>
          <p style={{ color: '#666', margin: '12px 0' }}>{this.state.error?.message || 'Service temporarily unavailable'}</p>
          <button className="btn btn-primary" onClick={this.handleRetry}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}
