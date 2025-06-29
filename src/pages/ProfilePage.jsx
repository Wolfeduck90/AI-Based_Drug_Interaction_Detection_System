import React, { useState } from 'react'
import { User, Mail, Calendar, Shield, Bell, Download, LogOut, Edit2, Save, X } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

const ProfilePage = () => {
  const [isEditing, setIsEditing] = useState(false)
  const [activeTab, setActiveTab] = useState('profile')
  const { user, logout, updateUser } = useAuthStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue
  } = useForm({
    defaultValues: {
      name: user?.name || '',
      email: user?.email || '',
      phone: user?.phone || '',
      date_of_birth: user?.date_of_birth || '',
      allergies: user?.allergies?.join(', ') || '',
      emergency_contact: user?.emergency_contact || '',
      medical_conditions: user?.medical_conditions?.join(', ') || ''
    }
  })

  const onSubmit = async (data) => {
    try {
      const updatedData = {
        ...data,
        allergies: data.allergies.split(',').map(a => a.trim()).filter(Boolean),
        medical_conditions: data.medical_conditions.split(',').map(c => c.trim()).filter(Boolean)
      }
      
      updateUser(updatedData)
      setIsEditing(false)
      toast.success('Profile updated successfully')
    } catch (error) {
      toast.error('Failed to update profile')
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
    // Reset form with current user data
    setValue('name', user?.name || '')
    setValue('email', user?.email || '')
    setValue('phone', user?.phone || '')
    setValue('date_of_birth', user?.date_of_birth || '')
    setValue('allergies', user?.allergies?.join(', ') || '')
    setValue('emergency_contact', user?.emergency_contact || '')
    setValue('medical_conditions', user?.medical_conditions?.join(', ') || '')
  }

  const handleCancel = () => {
    setIsEditing(false)
    reset()
  }

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to log out?')) {
      logout()
      toast.success('Logged out successfully')
    }
  }

  const exportData = () => {
    const data = {
      profile: user,
      exported_at: new Date().toISOString()
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `profile-data-${new Date().toISOString().split('T')[0]}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell }
  ]

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
          <p className="text-gray-600">
            Manage your account information and preferences
          </p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={exportData}
            className="btn btn-secondary"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Data
          </button>
          <button
            onClick={handleLogout}
            className="btn btn-danger"
          >
            <LogOut className="h-4 w-4 mr-2" />
            Logout
          </button>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="card mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeTab === id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Profile tab */}
      {activeTab === 'profile' && (
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Personal Information</h3>
            {!isEditing && (
              <button
                onClick={handleEdit}
                className="btn btn-secondary"
              >
                <Edit2 className="h-4 w-4 mr-2" />
                Edit
              </button>
            )}
          </div>

          {isEditing ? (
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Full Name *</label>
                  <input
                    type="text"
                    className="input"
                    {...register('name', { required: 'Name is required' })}
                  />
                  {errors.name && (
                    <p className="text-danger-600 text-sm mt-1">{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Email Address *</label>
                  <input
                    type="email"
                    className="input"
                    {...register('email', { 
                      required: 'Email is required',
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: 'Invalid email address'
                      }
                    })}
                  />
                  {errors.email && (
                    <p className="text-danger-600 text-sm mt-1">{errors.email.message}</p>
                  )}
                </div>

                <div>
                  <label className="label">Phone Number</label>
                  
                  <input
                    type="tel"
                    className="input"
                    {...register('phone')}
                  />
                </div>

                <div>
                  <label className="label">Date of Birth</label>
                  <input
                    type="date"
                    className="input"
                    {...register('date_of_birth')}
                  />
                </div>
              </div>

              <div>
                <label className="label">Emergency Contact</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Name and phone number"
                  {...register('emergency_contact')}
                />
              </div>

              <div>
                <label className="label">Known Allergies</label>
                <input
                  type="text"
                  className="input"
                  placeholder="e.g., Penicillin, Aspirin (comma-separated)"
                  {...register('allergies')}
                />
                <p className="text-gray-500 text-xs mt-1">
                  Separate multiple allergies with commas
                </p>
              </div>

              <div>
                <label className="label">Medical Conditions</label>
                <textarea
                  className="input"
                  rows="3"
                  placeholder="e.g., Diabetes, Hypertension (comma-separated)"
                  {...register('medical_conditions')}
                />
                <p className="text-gray-500 text-xs mt-1">
                  Separate multiple conditions with commas
                </p>
              </div>

              <div className="flex space-x-3">
                <button type="submit" className="btn btn-primary">
                  <Save className="h-4 w-4 mr-2" />
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={handleCancel}
                  className="btn btn-secondary"
                >
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-gray-500">Full Name</label>
                  <p className="mt-1 text-gray-900">{user?.name || 'Not provided'}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-500">Email Address</label>
                  <p className="mt-1 text-gray-900">{user?.email || 'Not provided'}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-500">Phone Number</label>
                  <p className="mt-1 text-gray-900">{user?.phone || 'Not provided'}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-500">Date of Birth</label>
                  <p className="mt-1 text-gray-900">
                    {user?.date_of_birth ? new Date(user.date_of_birth).toLocaleDateString() : 'Not provided'}
                  </p>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Emergency Contact</label>
                <p className="mt-1 text-gray-900">{user?.emergency_contact || 'Not provided'}</p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Known Allergies</label>
                <p className="mt-1 text-gray-900">
                  {user?.allergies && user.allergies.length > 0 
                    ? user.allergies.join(', ') 
                    : 'None reported'
                  }
                </p>
              </div>

              <div>
                <label className="text-sm font-medium text-gray-500">Medical Conditions</label>
                <p className="mt-1 text-gray-900">
                  {user?.medical_conditions && user.medical_conditions.length > 0 
                    ? user.medical_conditions.join(', ') 
                    : 'None reported'
                  }
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Security tab */}
      {activeTab === 'security' && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Password</h3>
            <p className="text-gray-600 mb-4">
              Change your password to keep your account secure
            </p>
            <button className="btn btn-primary">
              Change Password
            </button>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Two-Factor Authentication</h3>
            <p className="text-gray-600 mb-4">
              Add an extra layer of security to your account
            </p>
            <button className="btn btn-secondary">
              Enable 2FA
            </button>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Sessions</h3>
            <p className="text-gray-600 mb-4">
              Manage your active sessions across devices
            </p>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="font-medium text-gray-900">Current Session</p>
                  <p className="text-sm text-gray-600">Chrome on Windows • Active now</p>
                </div>
                <span className="text-xs text-success-600 font-medium">Current</span>
              </div>
            </div>
          </div>

          <div className="card bg-danger-50 border-danger-200">
            <h3 className="text-lg font-semibold text-danger-800 mb-4">Danger Zone</h3>
            <p className="text-danger-700 mb-4">
              Permanently delete your account and all associated data
            </p>
            <button className="btn btn-danger">
              Delete Account
            </button>
          </div>
        </div>
      )}

      {/* Notifications tab */}
      {activeTab === 'notifications' && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Notification Preferences</h3>
          
          <div className="space-y-6">
            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">Interaction Alerts</h4>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                  <span className="ml-3 text-sm text-gray-700">Critical interactions</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                  <span className="ml-3 text-sm text-gray-700">Major interactions</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-3 text-sm text-gray-700">Moderate interactions</span>
                </label>
              </div>
            </div>

            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">Email Notifications</h4>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                  <span className="ml-3 text-sm text-gray-700">Weekly summary reports</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-3 text-sm text-gray-700">New feature announcements</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-3 text-sm text-gray-700">Security alerts</span>
                </label>
              </div>
            </div>

            <div>
              <h4 className="text-md font-medium text-gray-900 mb-3">Push Notifications</h4>
              <div className="space-y-3">
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                  <span className="ml-3 text-sm text-gray-700">Medication reminders</span>
                </label>
                <label className="flex items-center">
                  <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <span className="ml-3 text-sm text-gray-700">Scan result notifications</span>
                </label>
              </div>
            </div>

            <div className="pt-4">
              <button className="btn btn-primary">
                Save Preferences
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProfilePage