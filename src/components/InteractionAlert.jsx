import React from 'react'
import { AlertTriangle, Info, AlertCircle, XCircle } from 'lucide-react'

const InteractionAlert = ({ interaction, className = '' }) => {
  const getSeverityIcon = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <XCircle className="h-5 w-5 text-danger-600" />
      case 'major':
        return <AlertTriangle className="h-5 w-5 text-warning-600" />
      case 'moderate':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      case 'minor':
        return <Info className="h-5 w-5 text-blue-600" />
      default:
        return <Info className="h-5 w-5 text-gray-600" />
    }
  }

  const getSeverityClass = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'severity-critical'
      case 'major':
        return 'severity-major'
      case 'moderate':
        return 'severity-moderate'
      case 'minor':
        return 'severity-minor'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  return (
    <div className={`interaction-alert ${interaction.severity.toLowerCase()} ${className}`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">
          {getSeverityIcon(interaction.severity)}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-2">
            <h4 className="text-sm font-semibold text-gray-900">
              {interaction.drug1} + {interaction.drug2}
            </h4>
            <span className={`px-2 py-1 text-xs font-medium rounded-full border ${getSeverityClass(interaction.severity)}`}>
              {interaction.severity}
            </span>
          </div>
          
          <p className="text-sm text-gray-700 mb-2">
            {interaction.description}
          </p>
          
          {interaction.clinical_effects && (
            <div className="mb-2">
              <h5 className="text-xs font-medium text-gray-900 mb-1">Clinical Effects:</h5>
              <p className="text-xs text-gray-600">{interaction.clinical_effects}</p>
            </div>
          )}
          
          {interaction.management && (
            <div className="mb-2">
              <h5 className="text-xs font-medium text-gray-900 mb-1">Management:</h5>
              <p className="text-xs text-gray-600">{interaction.management}</p>
            </div>
          )}
          
          {interaction.confidence && (
            <div className="text-xs text-gray-500">
              Confidence: {(interaction.confidence * 100).toFixed(0)}%
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default InteractionAlert