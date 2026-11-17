import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Vayudrishti-AI Runtime Error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#FAFAF8',
          fontFamily: 'Inter, system-ui, sans-serif',
          padding: '24px',
          color: '#202A35'
        }}>
          <div style={{
            maxWidth: '560px',
            width: '100%',
            backgroundColor: '#FFFFFF',
            border: '1px solid #E8EAE7',
            borderRadius: '12px',
            padding: '32px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '40px',
              height: '40px',
              borderRadius: '8px',
              backgroundColor: '#FEF2F2',
              border: '1px solid #FEE2E2',
              color: '#DC2626',
              marginBottom: '16px'
            }}>
              ⚠️
            </div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, margin: '0 0 8px 0', letterSpacing: '-0.01em' }}>
              Interface Initialization Error
            </h2>
            <p style={{ fontSize: '13px', color: '#737B83', lineHeight: 1.6, margin: '0 0 20px 0' }}>
              A client-side initialization exception occurred. The error details below can be used for diagnostics:
            </p>
            <div style={{
              backgroundColor: '#F8F9FA',
              border: '1px solid #E8EAE7',
              borderRadius: '6px',
              padding: '12px',
              fontSize: '12px',
              fontFamily: 'JetBrains Mono, monospace',
              color: '#DC2626',
              overflowX: 'auto',
              marginBottom: '20px'
            }}>
              {this.state.error?.toString()}
            </div>
            <button
              onClick={() => window.location.reload()}
              style={{
                backgroundColor: '#187D6B',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 18px',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer'
              }}
            >
              Reload Platform
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

