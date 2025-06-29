import React, { useEffect, useState } from 'react'
import { Calendar, Search, Download, Eye, Trash2 } from 'lucide-react'
import { format } from 'date-fns'
import { useMedicationStore } from '../stores/medicationStore'
import LoadingSpinner from '../components/LoadingSpinner'

const HistoryPage = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [dateFilter, setDateFilter] = useState('all')
  const [selectedScan, setSelectedScan] = useState(null)
  
  const { scanHistory, isLoading, fetchScanHistory } = useMedicationStore()

  useEffect(() => {
    fetchScanHistory()
  }, [])

  const filteredHistory = scanHistory.filter(scan => {
    const matchesSearch = scan.medications_detected?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         scan.extracted_text?.toLowerCase().includes(searchTerm.toLowerCase())
    
    if (dateFilter === 'all') return matchesSearch
    
    const scanDate = new Date(scan.created_at)
    const now = new Date()
    
    if (dateFilter === 'today') {
      return matchesSearch && scanDate.toDateString() === now.toDateString()
    }
    if (dateFilter === 'week') {
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      return matchesSearch && scanDate >= weekAgo
    }
    if (dateFilter === 'month') {
      const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      return matchesSearch && scanDate >= monthAgo
    }
    
    return matchesSearch
  })

  const exportHistory = () => {
    const data = filteredHistory.map(scan => ({
      'Date': format(new Date(scan.created_at), 'yyyy-MM-dd HH:mm'),
      'Medications Detected': scan.medications_detected || 'N/A',
      'Interactions Found': scan.interactions_found || 0,
      'Risk Level': scan.risk_level || 'Unknown',
      'Confidence': scan.confidence ? `${(scan.confidence * 100).toFixed(0)}%` : 'N/A'
    }))

    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).map(value => `"${value}"`).join(','))
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `scan-history-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel?.toLowerCase()) {
      case 'high':
      case 'critical':
        return 'text-danger-600 bg-danger-100'
      case 'moderate':
      case 'medium':
        return 'text-warning-600 bg-warning-100'
      case 'low':
      case 'minimal':
        return 'text-success-600 bg-success-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Scan History</h1>
          <p className="text-gray-600">
            Review your previous prescription scans and results
          </p>
        </div>
        {filteredHistory.length > 0 && (
          <button
            onClick={exportHistory}
            className="btn btn-secondary"
          >
            <Download className="h-4 w-4 mr-2" />
            Export
          </button>
        )}
      </div>

      {/* Search and filters */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search scans..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-gray-400" />
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
            </select>
          </div>
        </div>
      </div>

      {/* History list */}
      {filteredHistory.length > 0 ? (
        <div className="space-y-4">
          {filteredHistory.map((scan, index) => (
            <div key={index} className="card hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {scan.medications_detected || 'Prescription Scan'}
                    </h3>
                    {scan.risk_level && (
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getRiskLevelColor(scan.risk_level)}`}>
                        {scan.risk_level}
                      </span>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-gray-600 mb-3">
                    <div>
                      <span className="font-medium">Date:</span>{' '}
                      {format(new Date(scan.created_at), 'MMM d, yyyy HH:mm')}
                    </div>
                    <div>
                      <span className="font-medium">Interactions:</span>{' '}
                      {scan.interactions_found || 0}
                    </div>
                    <div>
                      <span className="font-medium">Confidence:</span>{' '}
                      {scan.confidence ? `${(scan.confidence * 100).toFixed(0)}%` : 'N/A'}
                    </div>
                  </div>

                  {scan.extracted_text && (
                    <p className="text-sm text-gray-700 line-clamp-2">
                      {scan.extracted_text.substring(0, 150)}
                      {scan.extracted_text.length > 150 ? '...' : ''}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => setSelectedScan(scan)}
                    className="p-2 text-gray-400 hover:text-gray-600"
                    title="View details"
                  >
                    <Eye className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => {/* TODO: Implement delete */}}
                    className="p-2 text-gray-400 hover:text-danger-600"
                    title="Delete scan"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Calendar className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm || dateFilter !== 'all' ? 'No scans found' : 'No scan history yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || dateFilter !== 'all'
              ? 'Try adjusting your search or filter criteria'
              : 'Start by scanning your first prescription to build your history'
            }
          </p>
          {!searchTerm && dateFilter === 'all' && (
            <button
              onClick={() => window.location.href = '/scan'}
              className="btn btn-primary"
            >
              Scan Prescription
            </button>
          )}
        </div>
      )}

      {/* Scan detail modal */}
      {selectedScan && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Scan Details</h3>
                <button
                  onClick={() => setSelectedScan(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Scan Information</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Date:</span>
                      <p className="font-medium">{format(new Date(selectedScan.created_at), 'PPpp')}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Risk Level:</span>
                      <p className={`font-medium ${getRiskLevelColor(selectedScan.risk_level).split(' ')[0]}`}>
                        {selectedScan.risk_level || 'Unknown'}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-600">Interactions Found:</span>
                      <p className="font-medium">{selectedScan.interactions_found || 0}</p>
                    </div>
                    <div>
                      <span className="text-gray-600">Confidence:</span>
                      <p className="font-medium">
                        {selectedScan.confidence ? `${(selectedScan.confidence * 100).toFixed(0)}%` : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>

                {selectedScan.medications_detected && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Medications Detected</h4>
                    <p className="text-sm text-gray-700">{selectedScan.medications_detected}</p>
                  </div>
                )}

                {selectedScan.extracted_text && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Extracted Text</h4>
                    <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 max-h-40 overflow-y-auto">
                      {selectedScan.extracted_text}
                    </div>
                  </div>
                )}

                {selectedScan.interactions && selectedScan.interactions.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Interactions</h4>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {selectedScan.interactions.map((interaction, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-3 text-sm">
                          <div className="font-medium text-gray-900">
                            {interaction.drug1} + {interaction.drug2}
                          </div>
                          <div className="text-gray-600">{interaction.description}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedScan(null)}
                  className="btn btn-secondary"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary stats */}
      {scanHistory.length > 0 && (
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">{scanHistory.length}</div>
            <div className="text-sm text-gray-600">Total Scans</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">
              {scanHistory.reduce((sum, scan) => sum + (scan.interactions_found || 0), 0)}
            </div>
            <div className="text-sm text-gray-600">Total Interactions</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">
              {scanHistory.filter(scan => scan.risk_level === 'high' || scan.risk_level === 'critical').length}
            </div>
            <div className="text-sm text-gray-600">High Risk Scans</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">
              {scanHistory.length > 0 ? 
                Math.round(scanHistory.reduce((sum, scan) => sum + (scan.confidence || 0), 0) / scanHistory.length * 100) : 0}%
            </div>
            <div className="text-sm text-gray-600">Avg Confidence</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default HistoryPage