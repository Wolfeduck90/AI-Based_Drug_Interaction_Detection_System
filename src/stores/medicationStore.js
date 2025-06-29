import { create } from 'zustand'
import api from '../services/api'

export const useMedicationStore = create((set, get) => ({
  medications: [],
  interactions: [],
  scanHistory: [],
  isLoading: false,
  error: null,

  // Fetch user medications
  fetchMedications: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.get('/medications')
      set({ medications: response.data, isLoading: false })
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch medications',
        isLoading: false 
      })
    }
  },

  // Add new medication
  addMedication: async (medicationData) => {
    try {
      const response = await api.post('/medications', medicationData)
      set((state) => ({
        medications: [...state.medications, response.data]
      }))
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to add medication'
      }
    }
  },

  // Update medication
  updateMedication: async (id, medicationData) => {
    try {
      const response = await api.put(`/medications/${id}`, medicationData)
      set((state) => ({
        medications: state.medications.map(med => 
          med.id === id ? response.data : med
        )
      }))
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to update medication'
      }
    }
  },

  // Remove medication
  removeMedication: async (id) => {
    try {
      await api.delete(`/medications/${id}`)
      set((state) => ({
        medications: state.medications.filter(med => med.id !== id)
      }))
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to remove medication'
      }
    }
  },

  // Check interactions
  checkInteractions: async (medicationIds = null) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/interactions/check', {
        medication_ids: medicationIds || get().medications.map(m => m.id)
      })
      set({ interactions: response.data, isLoading: false })
      return response.data
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to check interactions',
        isLoading: false 
      })
      return []
    }
  },

  // Scan prescription
  scanPrescription: async (imageFile) => {
    set({ isLoading: true, error: null })
    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      
      const response = await api.post('/scan/prescription', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      set({ isLoading: false })
      return { success: true, data: response.data }
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to scan prescription',
        isLoading: false 
      })
      return {
        success: false,
        error: error.response?.data?.message || 'Failed to scan prescription'
      }
    }
  },

  // Fetch scan history
  fetchScanHistory: async () => {
    try {
      const response = await api.get('/scan/history')
      set({ scanHistory: response.data })
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Failed to fetch scan history'
      })
    }
  },

  // Clear error
  clearError: () => set({ error: null })
}))