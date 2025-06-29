import React, { useEffect, useState } from 'react'
import { AlertTriangle, Filter, Download, RefreshCw } from 'lucide-react'
import { useMedicationStore } from '../stores/medicationStore'
import InteractionAlert from '../components/InteractionAlert'
import LoadingSpinner from '../components/LoadingSpinner'

const InteractionsPage = () => {
  const [severityFilter, setSeverityFilter] = useState('all')
  const [sortBy, setSortBy] = useState('severity')
  
  const {
    interactions,
    medications,
    isLoading,
    checkInteractions,
    fetchMedications
  } = useMedicationStore()

  useEffect(() => {
    fetchMedications()
  }, [])

  useEffect(() => {
    if (medications.length > 0) {
      checkInteractions()
    }
  }, [medications])

  const filteredInteractions = interactions
    .filter(interaction => {
      if (severityFilter === 'all') return true
      return interaction.severity === severityFilter
    })
    .sort((a, b) => {
      if (sortBy === 'severity') {
        const severityOrder = { critical: 4, major: 3, moderate: 2, minor: 1 }
        return severityOrder[b.severity] - severityOrder[a.severity]
      }
      if (sortBy === 'confidence') {
        return b.confidence - a.confidence
      }
      if (sortBy === 'alphabetical') {
        return `${a.drug1} ${a.drug2}`.localeCompare(`${b.drug1} ${b.drug2}`)
      }
      return 0
    })

  const severityCounts = interactions.reduce((acc, interaction) => {
    acc[interaction.severity] = (acc[interaction.severity] || 0) + 1
    return acc
  }, {})

  const handleRefresh = () => {
    if (medications.length > 0) {
      checkInteractions()
    }
  }

  const exportInteractions = () => {
    const data = filteredInteractions.map(interaction => ({
      'Drug 1': interaction.drug1,
      'Drug 2': interaction.drug2,
      'Severity': interaction.severity,
      'Description': interaction.description,
      'Clinical Effects': interaction.clinical_effects,
      'Management': interaction.management,
      'Confidence': `${(interaction.confidence * 100).toFixed(0)}%`
    }))

    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).map(value => `"${value}"`).join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `drug-interactions-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Drug Interactions</h1>
          <p className="text-gray-600">
            Review potential interactions between your medications
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="btn btn-secondary"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {filteredInteractions.length > 0 && (
            <button
              onClick={exportInteractions}
              className="btn btn-secondary"
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
          )}
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="card text-center">
          <div className="text-2xl font-bold text-gray-900">{interactions.length}</div>
          <div className="text-sm text-gray-600">Total Interactions</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-danger-600">{severityCounts.critical || 0}</div>
          <div className="text-sm text-gray-600">Critical</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-warning-600">{severityCounts.major || 0}</div>
          <div className="text-sm text-gray-600">Major</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-yellow-600">{severityCounts.moderate || 0}</div>
          <div className="text-sm text-gray-600">Moderate</div>
        </div>
      </div>

      {/* Filters and sorting */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-gray-400" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Severities</option>
              <option value="critical">Critical</option>
              <option value="major">Major</option>
              <option value="moderate">Moderate</option>
              <option value="minor">Minor</option>
            </select>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="input"
            >
              <option value="severity">Severity</option>
              <option value="confidence">Confidence</option>
              <option value="alphabetical">Alphabetical</option>
            </select>
          </div>
        </div>
      </div>

      {/* Interactions list */}
      {filteredInteractions.length > 0 ? (
        <div className="space-y-4">
          {filteredInteractions.map((interaction, index) => (
            <InteractionAlert key={index} interaction={interaction} />
          ))}
        </div>
      ) : interactions.length === 0 ? (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-success-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="h-8 w-8 text-success-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Interactions Detected
          </h3>
          <p className="text-gray-600 mb-4">
            {medications.length === 0 
              ? 'Add medications to your profile to check for interactions'
              : 'Your current medications don\'t have any known interactions'
            }
          </p>
          {medications.length === 0 && (
            <button
              onClick={() => window.location.href = '/medications'}
              className="btn btn-primary"
            >
              Add Medications
            </button>
          )}
        </div>
      ) : (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Filter className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            No Interactions Match Filter
          </h3>
          <p className="text-gray-600 mb-4">
            Try adjusting your filter criteria to see more results
          </p>
          <button
            onClick={() => setSeverityFilter('all')}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      )}

      {/* Critical interactions warning */}
      {severityCounts.critical > 0 && (
        <div className="mt-8 bg-danger-50 border border-danger-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-6 w-6 text-danger-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-lg font-semibold text-danger-800 mb-2">
                Critical Interactions Detected
              </h3>
              <p className="text-danger-700 mb-4">
                You have {severityCounts.critical} critical drug interaction{severityCounts.critical > 1 ? 's' : ''} 
                that require immediate medical attention. These combinations may cause serious adverse effects.
              </p>
              <div className="space-y-2 text-sm text-danger-700">
                <p><strong>Immediate Actions:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Contact your healthcare provider immediately</li>
                  <li>Do not stop taking medications without medical supervision</li>
                  <li>Bring this interaction report to your next appointment</li>
                  <li>Consider emergency care if experiencing adverse symptoms</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-8 card bg-gray-50">
        <div className="text-sm text-gray-700">
          <h4 className="font-semibold mb-2">Important Disclaimer</h4>
          <p>
            This interaction checker is for informational purposes only and should not replace 
            professional medical advice. Always consult with your healthcare provider before 
            making any changes to your medications. If you experience any adverse effects, 
            seek immediate medical attention.
          </p>
        </div>
      </div>
    </div>
  )
}

export default InteractionsPage