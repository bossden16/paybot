import { Component, ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import '@/lib/api';
import App from './App';
import './index.css';

interface ErrorBoundaryState { error: Error | null }

class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div style={{ fontFamily: 'monospace', padding: '2rem', background: '#0a0f1e', color: '#f87171', minHeight: '100vh' }}>
          <h1 style={{ color: '#ef4444', marginBottom: '1rem' }}>Application Error</h1>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', color: '#fca5a5' }}>
            {this.state.error.message}
            {'\n\n'}
            {this.state.error.stack}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}

// Dismiss the pre-React HTML loader once React has painted its first frame.
function removeLoader() {
  const htmlLoader = document.getElementById('html-loader');
  if (htmlLoader) {
    htmlLoader.style.transition = 'opacity 0.25s ease';
    htmlLoader.style.opacity = '0';
    setTimeout(() => htmlLoader.remove(), 280);
  }
}

// Ensure loader is removed even if React fails to mount
setTimeout(removeLoader, 3000);

try {
  createRoot(document.getElementById('root')!).render(
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  );
  requestAnimationFrame(() => requestAnimationFrame(removeLoader));
} catch (e) {
  console.error('Failed to mount React:', e);
  removeLoader();
}
