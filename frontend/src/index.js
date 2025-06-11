/**
 * Entry point for the Drug Interaction Detection System React frontend
 * 
 * This file initializes the React application and renders the main App component.
 * It includes error boundaries and global providers for state management.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import App from './App';

// Import necessary React components and hooks
import { StrictMode } from 'react';

// Error Boundary Component for handling React errors gracefully
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details for debugging
    console.error('React Error Boundary caught an error:', error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI when an error occurs
      return (
        <div style={{
          padding: '20px',
          textAlign: 'center',
          backgroundColor: '#f8f9fa',
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <h1 style={{ color: '#dc3545', marginBottom: '20px' }}>
            🚨 Something went wrong
          </h1>
          <p style={{ color: '#6c757d', marginBottom: '20px' }}>
            We're sorry, but there was an error loading the application.
          </p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            Reload Page
          </button>
          {process.env.NODE_ENV === 'development' && (
            <details style={{ marginTop: '20px', textAlign: 'left' }}>
              <summary style={{ cursor: 'pointer', color: '#007bff' }}>
                View Error Details (Development Mode)
              </summary>
              <pre style={{ 
                backgroundColor: '#f8f9fa', 
                padding: '10px', 
                borderRadius: '5px',
                fontSize: '12px',
                overflow: 'auto',
                maxWidth: '800px',
                marginTop: '10px'
              }}>
                {this.state.error && this.state.error.toString()}
                <br />
                {this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

// Authentication Context Provider (for managing user authentication state)
const AuthProvider = ({ children }) => {
  const [user, setUser] = React.useState(null);
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const [loading, setLoading] = React.useState(true);

  // Check for existing authentication on app load
  React.useEffect(() => {
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // Verify token with backend (simplified for this example)
          const response = await fetch('/api/auth/verify', {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
            setIsAuthenticated(true);
          } else {
            // Remove invalid token
            localStorage.removeItem('auth_token');
          }
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        localStorage.removeItem('auth_token');
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Authentication context value
  const authValue = {
    user,
    isAuthenticated,
    loading,
    login: (userData, token) => {
      setUser(userData);
      setIsAuthenticated(true);
      localStorage.setItem('auth_token', token);
    },
    logout: () => {
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem('auth_token');
    }
  };

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Create Auth Context
const AuthContext = React.createContext();

// Custom hook for using auth context
export const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Notification Provider for managing app-wide notifications
const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = React.useState([]);

  const addNotification = (message, type = 'info', duration = 5000) => {
    const id = Date.now() + Math.random();
    const notification = { id, message, type, duration };
    
    setNotifications(prev => [...prev, notification]);

    // Auto-remove notification after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }
  };

  const removeNotification = (id) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const notificationValue = {
    notifications,
    addNotification,
    removeNotification,
    // Convenience methods
    showSuccess: (message) => addNotification(message, 'success'),
    showError: (message) => addNotification(message, 'error', 0), // Don't auto-hide errors
    showWarning: (message) => addNotification(message, 'warning'),
    showInfo: (message) => addNotification(message, 'info')
  };

  return (
    <NotificationContext.Provider value={notificationValue}>
      {children}
      {/* Render notifications */}
      <div style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 9999,
        maxWidth: '400px'
      }}>
        {notifications.map(notification => (
          <div
            key={notification.id}
            style={{
              padding: '12px 16px',
              marginBottom: '10px',
              borderRadius: '6px',
              backgroundColor: getNotificationColor(notification.type),
              color: 'white',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              animation: 'slideIn 0.3s ease-out',
              cursor: 'pointer'
            }}
            onClick={() => removeNotification(notification.id)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>{notification.message}</span>
              <span style={{ marginLeft: '10px', opacity: 0.7 }}>×</span>
            </div>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
};

// Helper function for notification colors
const getNotificationColor = (type) => {
  const colors = {
    success: '#28a745',
    error: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8'
  };
  return colors[type] || colors.info;
};

// Create Notification Context
const NotificationContext = React.createContext();

// Custom hook for using notification context
export const useNotification = () => {
  const context = React.useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

// Performance monitoring (optional)
const reportWebVitals = (metric) => {
  // Log web vitals for performance monitoring
  if (process.env.NODE_ENV === 'development') {
    console.log('Web Vital:', metric);
  }
  
  // In production, you might want to send this to an analytics service
  // analytics.track('Web Vital', metric);
};

// Main render function
const renderApp = () => {
  const root = ReactDOM.createRoot(document.getElementById('root'));
  
  root.render(
    <StrictMode>
      <ErrorBoundary>
        <AuthProvider>
          <NotificationProvider>
            <App />
          </NotificationProvider>
        </AuthProvider>
      </ErrorBoundary>
    </StrictMode>
  );
};

// Service Worker registration (for PWA capabilities)
const registerServiceWorker = () => {
  if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    });
  }
};

// Initialize the application
const initializeApp = () => {
  // Add global styles for animations
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
    
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    
    /* Loading spinner styles */
    .loading-spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid #007bff;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      animation: spin 1s linear infinite;
      margin: 20px auto;
    }
    
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    
    /* Responsive design helpers */
    @media (max-width: 768px) {
      .notification-container {
        left: 10px;
        right: 10px;
        top: 10px;
        max-width: none;
      }
    }
  `;
  document.head.appendChild(style);

  // Set up global error handling
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
    // Prevent the default browser error handling
    event.preventDefault();
  });

  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
  });

  // Initialize the React app
  renderApp();
  
  // Register service worker for PWA functionality
  registerServiceWorker();
  
  // Report web vitals for performance monitoring
  if (typeof reportWebVitals === 'function') {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(reportWebVitals);
      getFID(reportWebVitals);
      getFCP(reportWebVitals);
      getLCP(reportWebVitals);
      getTTFB(reportWebVitals);
    }).catch(() => {
      // web-vitals not available, continue without it
    });
  }
};

// Application loading indicator
const showLoadingIndicator = () => {
  const loadingDiv = document.createElement('div');
  loadingDiv.id = 'initial-loading';
  loadingDiv.innerHTML = `
    <div style="
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(255, 255, 255, 0.9);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 10000;
    ">
      <div style="text-align: center;">
        <div class="loading-spinner"></div>
        <p style="margin-top: 20px; color: #666; font-family: Arial, sans-serif;">
          Loading Drug Interaction Detection System...
        </p>
      </div>
    </div>
  `;
  document.body.appendChild(loadingDiv);
  
  // Remove loading indicator after app loads
  setTimeout(() => {
    const loading = document.getElementById('initial-loading');
    if (loading) {
      loading.remove();
    }
  }, 2000);
};

// Environment-specific configurations
const setupEnvironment = () => {
  if (process.env.NODE_ENV === 'development') {
    // Development-specific setup
    console.log('🚀 Drug Interaction Detection System - Development Mode');
    
    // Enable React DevTools integration
    if (window.__REACT_DEVTOOLS_GLOBAL_HOOK__) {
      console.log('React DevTools detected');
    }
  } else {
    // Production-specific setup
    console.log('%c🏥 Drug Interaction Detection System', 'color: #007bff; font-weight: bold; font-size: 16px;');
    
    // Disable console logs in production
    if (process.env.NODE_ENV === 'production') {
      console.log = () => {};
      console.warn = () => {};
    }
  }
};

// Check browser compatibility
const checkBrowserCompatibility = () => {
  const requiredFeatures = [
    'fetch',
    'Promise',
    'localStorage',
    'FileReader',
    'FormData'
  ];
  
  const unsupportedFeatures = requiredFeatures.filter(feature => !(feature in window));
  
  if (unsupportedFeatures.length > 0) {
    const message = `Your browser doesn't support required features: ${unsupportedFeatures.join(', ')}. Please update your browser for the best experience.`;
    alert(message);
    console.error('Browser compatibility check failed:', unsupportedFeatures);
  }
};

// Initialize everything when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    setupEnvironment();
    checkBrowserCompatibility();
    showLoadingIndicator();
    initializeApp();
  });
} else {
  // DOM already loaded
  setupEnvironment();
  checkBrowserCompatibility();
  showLoadingIndicator();
  initializeApp();
}

// Export contexts for use in other components
export { AuthContext, NotificationContext };
