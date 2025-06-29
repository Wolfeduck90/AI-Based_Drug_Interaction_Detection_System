import React from 'react'
import { Pill, Calendar, Clock, MoreVertical, AlertTriangle } from 'lucide-react'
import { format } from 'date-fns'

const MedicationCard = ({ medication, onEdit, onDelete, interactions = [] }) => {
  const hasInteractions = interactions.length > 0
  const highestSeverity = interactions.reduce((max, interaction) => {
    const severityLevels = { minor: 1, moderate: 2, major: 3, critical: 4 }
    return Math.max(max, severityLevels[interaction.severity] || 0)
  }, 0)

  const getSeverityColor = (level) => {
    switch (level) {
      case 4: return 'text-danger-600'
      case 3: return 'text-warning-600'
      case 2: return 'text-yellow-600'
      case 1: return 'text-blue-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <div className="medication-card card relative">
      {/* Interaction indicator */}
      {hasInteractions && (
        <div className="absolute top-4 right-4">
          <AlertTriangle className={`h-5 w-5 ${getSeverityColor(highestSeverity)}`} />
        </div>
      )}

      <div className="flex items-start space-x-4">
        {/* Medication icon */}
        <div className="flex-shrink-0">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
            <Pill className="h-6 w-6 text-primary-600" />
          </div>
        </div>

        {/* Medication details */}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {medication.name}
          </h3>
          
          {medication.generic_name && medication.generic_name !== medication.name && (
            <p className="text-sm text-gray-500 mb-1">
              Generic: {medication.generic_name}
            </p>
          )}

          <div className="flex flex-wrap gap-2 text-sm text-gray-600">
            {medication.dosage && (
              <span className="inline-flex items-center">
                <Pill className="h-4 w-4 mr-1" />
                {medication.dosage}
              </span>
            )}
            
            {medication.frequency && (
              <span className="inline-flex items-center">
                <Clock className="h-4 w-4 mr-1" />
                {medication.frequency}
              </span>
            )}
          </div>

          {medication.start_date && (
            <div className="mt-2 text-xs text-gray-500">
              <Calendar className="h-3 w-3 inline mr-1" />
              Started: {format(new Date(medication.start_date), 'MMM d, yyyy')}
            </div>
          )}

          {/* Interaction summary */}
          {hasInteractions && (
            <div className="mt-2">
              <span className={`text-xs font-medium ${getSeverityColor(highestSeverity)}`}>
                {interactions.length} interaction{interactions.length > 1 ? 's' : ''} detected
              </span>
            </div>
          )}
        </div>

        {/* Actions menu */}
        <div className="flex-shrink-0">
          <button
            className="p-1 text-gray-400 hover:text-gray-600"
            onClick={() => {/* TODO: Implement dropdown menu */}}
          >
            <MoreVertical className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Quick actions */}
      <div className="mt-4 flex space-x-2">
        <button
          onClick={() => onEdit(medication)}
          className="btn btn-secondary text-xs"
        >
          Edit
        </button>
        <button
          onClick={() => onDelete(medication.id)}
          className="btn text-xs text-danger-600 hover:bg-danger-50"
        >
          Remove
        </button>
      </div>
    </div>
  )
}

export default MedicationCard