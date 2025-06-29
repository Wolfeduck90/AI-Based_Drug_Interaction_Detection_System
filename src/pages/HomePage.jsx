import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Camera, Pill, AlertTriangle, TrendingUp, Clock } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { useMedicationStore } from '../stores/medicationStore'
import LoadingSpinner from '../components/LoadingSpinner'

const HomePage = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { 
    medications, 
    interactions, 
    scanHistory, 
    isLoading,
    fetchMedications,
    checkInteractions,
    fetchScanHistory
  } = useMedicationStore()

  useEffect(() => {
    fetchMedications()
    fetchScanHistory()
  }, [])

  useEffect(() => {
    if (medications.length > 0) {
      checkInteractions()
    }
  }, [medications])

  const criticalInteractions = interactions.filter(i => i.severity === 'critical').length
  const totalInteractions = interactions.length
  const recentScans = scanHistory.slice(0, 3)

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Welcome section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          {getGreeting()}, {user?.name?.split(' ')[0] || 'there'}! 👋
        </h1>
        <p className="text-gray-600">
          Keep track of your medications and stay safe from interactions
        </p>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <Pill className="h-6 w-6 text-primary-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{medications.length}</div>
          <div className="text-sm text-gray-600">Medications</div>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-warning-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <AlertTriangle className="h-6 w-6 text-warning-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{totalInteractions}</div>
          <div className="text-sm text-gray-600">Interactions</div>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-danger-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <TrendingUp className="h-6 w-6 text-danger-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{criticalInteractions}</div>
          <div className="text-sm text-gray-600">Critical</div>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center mx-auto mb-3">
            <Camera className="h-6 w-6 text-success-600" />
          </div>
          <div className="text-2xl font-bold text-gray-900">{scanHistory.length}</div>
          <div className="text-sm text-gray-600">Scans</div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => navigate('/scan')}
            className="card hover:shadow-md transition-shadow text-left group"
          >
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center group-hover:bg-primary-200 transition-colors">
                <Camera className="h-6 w-6 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Scan Prescription</h3>
                <p className="text-sm text-gray-600">Take a photo to detect interactions</p>
              </div>
            </div>
          </button>

          <button
            onClick={() => navigate('/medications')}
            className="card hover:shadow-md transition-shadow text-left group"
          >
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-success-100 rounded-lg flex items-center justify-center group-hover:bg-success-200 transition-colors">
                <Pill className="h-6 w-6 text-success-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Manage Medications</h3>
                <p className="text-sm text-gray-600">Add or update your medications</p>
              </div>
            </div>
          </button>
        </div>
      </div>

      {/* Critical interactions alert */}
      {criticalInteractions > 0 && (
        <div className="mb-8">
          <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-6 w-6 text-danger-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-danger-800">
                  Critical Interactions Detected
                </h3>
                <p className="text-sm text-danger-700 mt-1">
                  You have {criticalInteractions} critical drug interaction{criticalInteractions > 1 ? 's' : ''}.
                  Please consult your healthcare provider immediately.
                </p>
                <button
                  onClick={() => navigate('/interactions')}
                  className="mt-2 text-sm font-medium text-danger-800 hover:text-danger-900"
                >
                  View Details →
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent activity */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Scans</h2>
          <button
            onClick={() => navigate('/history')}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View All
          </button>
        </div>

        {recentScans.length > 0 ? (
          <div className="space-y-3">
            {recentScans.map((scan, index) => (
              <div key={index} className="card">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Clock className="h-5 w-5 text-gray-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {scan.medications_detected || 'Prescription scan'}
                    </p>
                    <p className="text-xs text-gray-600">
                      {new Date(scan.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  {scan.interactions_found > 0 && (
                    <div className="text-xs text-warning-600 font-medium">
                      {scan.interactions_found} interaction{scan.interactions_found > 1 ? 's' : ''}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="card text-center py-8">
            <Camera className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-sm font-medium text-gray-900 mb-2">No scans yet</h3>
            <p className="text-sm text-gray-600 mb-4">
              Start by scanning your first prescription
            </p>
            <button
              onClick={() => navigate('/scan')}
              className="btn btn-primary"
            >
              Scan Now
            </button>
          </div>
        )}
      </div>

      {/* Health tip */}
      <div className="card bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200">
        <div className="flex items-start space-x-3">
          <div className="w-8 h-8 bg-primary-200 rounded-full flex items-center justify-center flex-shrink-0">
            <span className="text-primary-700 text-sm">💡</span>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-primary-900 mb-1">
              Health Tip
            </h3>
            <p className="text-sm text-primary-800">
              Always inform your healthcare providers about all medications, supplements, 
              and over-the-counter drugs you're taking to avoid dangerous interactions.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage