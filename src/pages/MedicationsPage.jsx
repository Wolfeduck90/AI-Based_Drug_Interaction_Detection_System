import React, { useState, useEffect } from 'react'
import { Plus, Search, Filter, Edit2, Trash2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { useMedicationStore } from '../stores/medicationStore'
import MedicationCard from '../components/MedicationCard'
import LoadingSpinner from '../components/LoadingSpinner'
import toast from 'react-hot-toast'

const MedicationsPage = () => {
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingMedication, setEditingMedication] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterType, setFilterType] = useState('all')
  
  const {
    medications,
    interactions,
    isLoading,
    fetchMedications,
    addMedication,
    updateMedication,
    removeMedication,
    checkInteractions
  } = useMedicationStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue
  } = useForm()

  useEffect(() => {
    fetchMedications()
  }, [])

  useEffect(() => {
    if (medications.length > 0) {
      checkInteractions()
    }
  }, [medications])

  const filteredMedications = medications.filter(medication => {
    const matchesSearch = medication.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (medication.generic_name && medication.generic_name.toLowerCase().includes(searchTerm.toLowerCase()))
    
    if (filterType === 'all') return matchesSearch
    if (filterType === 'active') return matchesSearch && medication.is_active
    if (filterType === 'interactions') {
      const hasInteractions = interactions.some(interaction => 
        interaction.drug1 === medication.name || interaction.drug2 === medication.name
      )
      return matchesSearch && hasInteractions
    }
    
    return matchesSearch
  })

  const onSubmit = async (data) => {
    try {
      let result
      if (editingMedication) {
        result = await updateMedication(editingMedication.id, data)
      } else {
        result = await addMedication(data)
      }

      if (result.success) {
        toast.success(editingMedication ? 'Medication updated' : 'Medication added')
        reset()
        setShowAddForm(false)
        setEditingMedication(null)
      } else {
        toast.error(result.error)
      }
    } catch (error) {
      toast.error('An error occurred')
    }
  }

  const handleEdit = (medication) => {
    setEditingMedication(medication)
    setValue('name', medication.name)
    setValue('generic_name', medication.generic_name || '')
    setValue('dosage', medication.dosage || '')
    setValue('frequency', medication.frequency || '')
    setValue('prescriber', medication.prescriber || '')
    setValue('pharmacy', medication.pharmacy || '')
    setValue('notes', medication.notes || '')
    setShowAddForm(true)
  }

  const handleDelete = async (medicationId) => {
    if (window.confirm('Are you sure you want to remove this medication?')) {
      const result = await removeMedication(medicationId)
      if (result.success) {
        toast.success('Medication removed')
      } else {
        toast.error(result.error)
      }
    }
  }

  const cancelForm = () => {
    reset()
    setShowAddForm(false)
    setEditingMedication(null)
  }

  const getMedicationInteractions = (medicationName) => {
    return interactions.filter(interaction => 
      interaction.drug1 === medicationName || interaction.drug2 === medicationName
    )
  }

  if (isLoading && medications.length === 0) {
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
          <h1 className="text-2xl font-bold text-gray-900">My Medications</h1>
          <p className="text-gray-600">
            Manage your current medications and track interactions
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="btn btn-primary"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Medication
        </button>
      </div>

      {/* Search and filters */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search medications..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input pl-10"
              />
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input"
            >
              <option value="all">All Medications</option>
              <option value="active">Active Only</option>
              <option value="interactions">With Interactions</option>
            </select>
          </div>
        </div>
      </div>

      {/* Add/Edit medication form */}
      {showAddForm && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {editingMedication ? 'Edit Medication' : 'Add New Medication'}
            </h3>
            <button
              onClick={cancelForm}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Medication Name *</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Lisinopril"
                  {...register('name', { required: 'Medication name is required' })}
                />
                {errors.name && (
                  <p className="text-danger-600 text-sm mt-1">{errors.name.message}</p>
                )}
              </div>

              <div>
                <label className="label">Generic Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., lisinopril"
                  {...register('generic_name')}
                />
              </div>

              <div>
                <label className="label">Dosage</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., 10mg tablet"
                  {...register('dosage')}
                />
              </div>

              <div>
                <label className="label">Frequency</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Once daily"
                  {...register('frequency')}
                />
              </div>

              <div>
                <label className="label">Prescribing Doctor</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Dr. Smith"
                  {...register('prescriber')}
                />
              </div>

              <div>
                <label className="label">Pharmacy</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., CVS Pharmacy"
                  {...register('pharmacy')}
                />
              </div>
            </div>

            <div>
              <label className="label">Notes</label>
              <textarea
                className="input"
                rows="3"
                placeholder="Additional notes about this medication..."
                {...register('notes')}
              />
            </div>

            <div className="flex space-x-3">
              <button type="submit" className="btn btn-primary">
                {editingMedication ? 'Update Medication' : 'Add Medication'}
              </button>
              <button
                type="button"
                onClick={cancelForm}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Medications list */}
      {filteredMedications.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredMedications.map((medication) => (
            <MedicationCard
              key={medication.id}
              medication={medication}
              interactions={getMedicationInteractions(medication.name)}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <Plus className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {searchTerm || filterType !== 'all' ? 'No medications found' : 'No medications yet'}
          </h3>
          <p className="text-gray-600 mb-4">
            {searchTerm || filterType !== 'all' 
              ? 'Try adjusting your search or filter criteria'
              : 'Start by adding your first medication to track interactions'
            }
          </p>
          {!searchTerm && filterType === 'all' && (
            <button
              onClick={() => setShowAddForm(true)}
              className="btn btn-primary"
            >
              Add Your First Medication
            </button>
          )}
        </div>
      )}

      {/* Summary stats */}
      {medications.length > 0 && (
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">{medications.length}</div>
            <div className="text-sm text-gray-600">Total Medications</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">{interactions.length}</div>
            <div className="text-sm text-gray-600">Interactions Found</div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-gray-900">
              {medications.filter(m => m.is_active).length}
            </div>
            <div className="text-sm text-gray-600">Active Medications</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MedicationsPage