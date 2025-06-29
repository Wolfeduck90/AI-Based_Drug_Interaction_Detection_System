import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, User, Menu } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'

const Header = () => {
  const navigate = useNavigate()
  const { user } = useAuthStore()

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-primary-600">
                💊 DrugDetector
              </h1>
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button
              className="p-2 text-gray-400 hover:text-gray-500 relative"
              onClick={() => navigate('/notifications')}
            >
              <Bell className="h-6 w-6" />
              {/* Notification badge */}
              <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-danger-400 ring-2 ring-white" />
            </button>

            {/* Profile */}
            <button
              className="flex items-center space-x-2 p-2 text-gray-700 hover:text-gray-900"
              onClick={() => navigate('/profile')}
            >
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                <User className="h-5 w-5 text-primary-600" />
              </div>
              <span className="hidden sm:block text-sm font-medium">
                {user?.name || 'User'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header