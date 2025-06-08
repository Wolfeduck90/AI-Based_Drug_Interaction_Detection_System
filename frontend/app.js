/**
 * React Frontend for Drug Interaction Detection System
 * Main application component with routing and state management
 */

import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';

// Create authentication context
const AuthContext = createContext();

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Authentication Context Provider
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Check authentication status on app load
  useEffect(() => {
    if (token) {
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/user/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        // Token is invalid
        logout();
      }
    } catch (error) {
      console.error('Error fetching user profile:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await fetch(`${API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error occurred' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await fetch(`${API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(userData)
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error occurred' };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use authentication context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

// Login Component
function LoginForm({ onSwitchToRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="auth-form">
      <h2>Login to Drug Interaction Detector</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username:</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
          />
        </div>
        {error && <div className="error-message">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
      <p>
        Don't have an account?{' '}
        <button 
          type="button" 
          className="link-button"
          onClick={onSwitchToRegister}
        >
          Register here
        </button>
      </p>
    </div>
  );
}

// Registration Component
function RegisterForm({ onSwitchToLogin }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    date_of_birth: '',
    medical_conditions: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    const result = await register({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      date_of_birth: formData.date_of_birth,
      medical_conditions: formData.medical_conditions
    });
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="auth-form">
      <h2>Register for Drug Interaction Detector</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Username:</label>
          <input
            type="text"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Password:</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Confirm Password:</label>
          <input
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Date of Birth:</label>
          <input
            type="date"
            name="date_of_birth"
            value={formData.date_of_birth}
            onChange={handleChange}
            required
            disabled={loading}
          />
        </div>
        <div className="form-group">
          <label>Medical Conditions (Optional):</label>
          <textarea
            name="medical_conditions"
            value={formData.medical_conditions}
            onChange={handleChange}
            rows="3"
            disabled={loading}
            placeholder="List any relevant medical conditions..."
          />
        </div>
        {error && <div className="error-message">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? 'Registering...' : 'Register'}
        </button>
      </form>
      <p>
        Already have an account?{' '}
        <button 
          type="button" 
          className="link-button"
          onClick={onSwitchToLogin}
        >
          Login here
        </button>
      </p>
    </div>
  );
}

// Medication Scanner Component
function MedicationScanner() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please select a valid image file');
        return;
      }
      
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      setSelectedFile(file);
      setError('');
      setScanResult(null);
    }
  };

  const handleScan = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    setScanning(true);
    setError('');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(`${API_BASE_URL}/scan-medication`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        setScanResult(result);
      } else {
        const error = await response.json();
        setError(error.detail || 'Scan failed');
      }
    } catch (error) {
      setError('Network error occurred during scan');
    } finally {
      setScanning(false);
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical': return '#dc3545';
      case 'high': return '#fd7e14';
      case 'moderate': return '#ffc107';
      case 'low': return '#28a745';
      default: return '#6c757d';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return '🚨';
      case 'major': return '⚠️';
      case 'moderate': return '⚡';
      case 'minor': return 'ℹ️';
      default: return '❓';
    }
  };

  return (
    <div className="scanner-container">
      <h2>📱 Scan Medication Label</h2>
      
      <div className="upload-section">
        <div className="file-input-wrapper">
          <input
            type="file"
            id="medication-image"
            accept="image/*"
            onChange={handleFileSelect}
            disabled={scanning}
          />
          <label htmlFor="medication-image" className="file-input-label">
            {selectedFile ? selectedFile.name : 'Choose medication image...'}
          </label>
        </div>
        
        {selectedFile && (
          <button 
            onClick={handleScan} 
            disabled={scanning}
            className="scan-button"
          >
            {scanning ? '🔍 Scanning...' : '🔍 Scan for Interactions'}
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      {scanResult && (
        <div className="scan-results">
          <h3>Scan Results</h3>
          
          {/* Risk Level Overview */}
          <div 
            className="risk-level-badge"
            style={{ backgroundColor: getRiskLevelColor(scanResult.risk_level) }}
          >
            Risk Level: {scanResult.risk_level.toUpperCase()}
          </div>

          {/* Extracted Drugs */}
          <div className="section">
            <h4>🔍 Extracted Medications</h4>
            {scanResult.extracted_drugs.length > 0 ? (
              <ul className="drug-list">
                {scanResult.extracted_drugs.map((drug, index) => (
                  <li key={index} className="drug-item">
                    <strong>{drug.matched_drug}</strong>
                    <span className="confidence">
                      (Confidence: {(drug.confidence * 100).toFixed(1)}%)
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No medications detected in the image.</p>
            )}
          </div>

          {/* Interaction Alerts */}
          {scanResult.alerts.length > 0 && (
            <div className="section">
              <h4>⚠️ Interaction Alerts</h4>
              {scanResult.alerts.map((alert, index) => (
                <div 
                  key={index} 
                  className={`alert alert-${alert.severity.toLowerCase()}`}
                >
                  <div className="alert-header">
                    <span className="severity-icon">
                      {getSeverityIcon(alert.severity)}
                    </span>
                    <span className="alert-message">{alert.message}</span>
                  </div>
                  <div className="alert-description">
                    {alert.description}
                  </div>
                  <div className="alert-recommendation">
                    <strong>Recommendation:</strong> {alert.recommendation}
                  </div>
                </div>
              ))}
            </div>
          )}

          {scanResult.alerts.length === 0 && (
            <div className="section">
              <div className="no-interactions">
                ✅ No drug interactions detected with your current medications.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// User Medications Component
function UserMedications() {
  const [medications, setMedications] = useState([]);
  const [newMedication, setNewMedication] = useState({
    drug_name: '',
    dosage: '',
    frequency: ''
  });
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');
  const { token } = useAuth();

  useEffect(() => {
    fetchMedications();
  }, []);

  const fetchMedications = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/user/medications`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMedications(data.medications);
      } else {
        setError('Failed to fetch medications');
      }
    } catch (error) {
      setError('Network error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleAddMedication = async (e) => {
    e.preventDefault();
    setAdding(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/user/medications`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newMedication)
      });

      if (response.ok) {
        setNewMedication({ drug_name: '', dosage: '', frequency: '' });
        fetchMedications(); // Refresh the list
      } else {
        const error = await response.json();
        setError(error.detail || 'Failed to add medication');
      }
    } catch (error) {
      setError('Network error occurred');
    } finally {
      setAdding(false);
    }
  };

  const handleRemoveMedication = async (medicationId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/user/medications/${medicationId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        fetchMedications(); // Refresh the list
      } else {
        setError('Failed to remove medication');
      }
    } catch (error) {
      setError('Network error occurred');
    }
  };

  if (loading) {
    return <div className="loading">Loading medications...</div>;
  }

  return (
    <div className="medications-container">
      <h2>💊 My Medications</h2>

      {/* Add New Medication Form */}
      <div className="add-medication-section">
        <h3>Add New Medication</h3>
        <form onSubmit={handleAddMedication} className="medication-form">
          <div className="form-row">
            <input
              type="text"
              placeholder="Medication name"
              value={newMedication.drug_name}
              onChange={(e) => setNewMedication({
                ...newMedication,
                drug_name: e.target.value
              })}
              required
              disabled={adding}
            />
            <input
              type="text"
              placeholder="Dosage (e.g., 10mg)"
              value={newMedication.dosage}
              onChange={(e) => setNewMedication({
                ...newMedication,
                dosage: e.target.value
              })}
              disabled={adding}
            />
            <input
              type="text"
              placeholder="Frequency (e.g., twice daily)"
              value={newMedication.frequency}
              onChange={(e) => setNewMedication({
                ...newMedication,
                frequency: e.target.value
              })}
              disabled={adding}
            />
            <button type="submit" disabled={adding}>
              {adding ? 'Adding...' : 'Add'}
            </button>
          </div>
        </form>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Current Medications List */}
      <div className="current-medications">
        <h3>Current Medications</h3>
        {medications.length > 0 ? (
          <div className="medications-grid">
            {medications.map((medication) => (
              <div key={medication.id} className="medication-card">
                <div className="medication-header">
                  <h4>{medication.drug_name}</h4>
                  <button
                    onClick={() => handleRemoveMedication(medication.id)}
                    className="remove-button"
                    title="Remove medication"
                  >
                    ×
                  </button>
                </div>
                {medication.dosage && (
                  <p><strong>Dosage:</strong> {medication.dosage}</p>
                )}
                {medication.frequency && (
                  <p><strong>Frequency:</strong> {medication.frequency}</p>
                )}
                <p className="added-date">
                  Added: {new Date(medication.added_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-medications">
            No medications added yet. Add your first medication above.
          </p>
        )}
      </div>
    </div>
  );
}

// Navigation Component
function Navigation({ currentPage, setCurrentPage }) {
  const { user, logout } = useAuth();

  return (
    <nav className="navigation">
      <div className="nav-brand">
        <h1>🏥 Drug Interaction Detector</h1>
      </div>
      <div className="nav-links">
        <button
          className={currentPage === 'scanner' ? 'active' : ''}
          onClick={() => setCurrentPage('scanner')}
        >
          📱 Scan Medication
        </button>
        <button
          className={currentPage === 'medications' ? 'active' : ''}
          onClick={() => setCurrentPage('medications')}
        >
          💊 My Medications
        </button>
      </div>
      <div className="nav-user">
        <span>Welcome, {user?.username}</span>
        <button onClick={logout} className="logout-button">
          Logout
        </button>
      </div>
    </nav>
  );
}

// Main Dashboard Component
function Dashboard() {
  const [currentPage, setCurrentPage] = useState('scanner');

  return (
    <div className="dashboard">
      <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />
      <main className="main-content">
        {currentPage === 'scanner' && <MedicationScanner />}
        {currentPage === 'medications' && <UserMedications />}
      </main>
    </div>
  );
}

// Main App Component
function App() {
  const [showRegister, setShowRegister] = useState(false);

  return (
    <AuthProvider>
      <div className="App">
        <AuthContent 
          showRegister={showRegister}
          setShowRegister={setShowRegister}
        />
      </div>
    </AuthProvider>
  );
}

// Authentication Content Component
function AuthContent({ showRegister, setShowRegister }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Dashboard />;
  }

  return (
    <div className="auth-container">
      {showRegister ? (
        <RegisterForm onSwitchToLogin={() => setShowRegister(false)} />
      ) : (
        <LoginForm onSwitchToRegister={() => setShowRegister(true)} />
      )}
    </div>
  );
}

export default App;
