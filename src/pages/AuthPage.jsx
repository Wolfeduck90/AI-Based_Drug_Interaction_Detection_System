import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Eye, EyeOff, Loader2 } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import toast from 'react-hot-toast'

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true)
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { login, register: registerUser } = useAuthStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch
  } = useForm()

  const password = watch('password')

  const onSubmit = async (data) => {
    setIsLoading(true)
    
    try {
      let result
      if (isLogin) {
        result = await login({
          email: data.email,
          password: data.password
        })
      } else {
        result = await registerUser({
          name: data.name,
          email: data.email,
          password: data.password,
          date_of_birth: data.dateOfBirth,
          allergies: data.allergies?.split(',').map(a => a.trim()).filter(Boolean) || []
        })
      }

      if (result.success) {
        toast.success(isLogin ? 'Welcome back!' : 'Account created successfully!')
        reset()
      } else {
        toast.error(result.error)
      }
    } catch (error) {
      toast.error('An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleMode = () => {
    setIsLogin(!isLogin)
    reset()
    setShowPassword(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Logo and title */}
        <div className="text-center mb-8">
          <div className="text-6xl mb-4">💊</div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            DrugDetector
          </h1>
          <p className="text-gray-600">
            AI-powered drug interaction detection
          </p>
        </div>

        {/* Auth form */}
        <div className="card">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900 text-center">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </h2>
            <p className="text-gray-600 text-center mt-2">
              {isLogin 
                ? 'Sign in to your account' 
                : 'Join us to start detecting drug interactions'
              }
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Name field (register only) */}
            {!isLogin && (
              <div>
                <label className="label">Full Name</label>
                <input
                  type="text"
                  className="input"
                  placeholder="Enter your full name"
                  {...register('name', {
                    required: 'Name is required',
                    minLength: {
                      value: 2,
                      message: 'Name must be at least 2 characters'
                    }
                  })}
                />
                {errors.name && (
                  <p className="text-danger-600 text-sm mt-1">{errors.name.message}</p>
                )}
              </div>
            )}

            {/* Email field */}
            <div>
              <label className="label">Email Address</label>
              <input
                type="email"
                className="input"
                placeholder="Enter your email"
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

            {/* Password field */}
            <div>
              <label className="label">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input pr-10"
                  placeholder="Enter your password"
                  {...register('password', {
                    required: 'Password is required',
                    minLength: {
                      value: 6,
                      message: 'Password must be at least 6 characters'
                    }
                  })}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-danger-600 text-sm mt-1">{errors.password.message}</p>
              )}
            </div>

            {/* Confirm password (register only) */}
            {!isLogin && (
              <div>
                <label className="label">Confirm Password</label>
                <input
                  type="password"
                  className="input"
                  placeholder="Confirm your password"
                  {...register('confirmPassword', {
                    required: 'Please confirm your password',
                    validate: value =>
                      value === password || 'Passwords do not match'
                  })}
                />
                {errors.confirmPassword && (
                  <p className="text-danger-600 text-sm mt-1">{errors.confirmPassword.message}</p>
                )}
              </div>
            )}

            {/* Date of birth (register only) */}
            {!isLogin && (
              <div>
                <label className="label">Date of Birth</label>
                <input
                  type="date"
                  className="input"
                  {...register('dateOfBirth', {
                    required: 'Date of birth is required'
                  })}
                />
                {errors.dateOfBirth && (
                  <p className="text-danger-600 text-sm mt-1">{errors.dateOfBirth.message}</p>
                )}
              </div>
            )}

            {/* Allergies (register only) */}
            {!isLogin && (
              <div>
                <label className="label">Known Allergies (Optional)</label>
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
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary w-full mobile-button"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  {isLogin ? 'Signing In...' : 'Creating Account...'}
                </>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>

          {/* Toggle mode */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              {isLogin ? "Don't have an account?" : 'Already have an account?'}
              {' '}
              <button
                type="button"
                onClick={toggleMode}
                className="text-primary-600 hover:text-primary-500 font-medium"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>

        {/* Disclaimer */}
        <div className="mt-6 text-center text-xs text-gray-500">
          <p>
            This app is for informational purposes only and should not replace
            professional medical advice.
          </p>
        </div>
      </div>
    </div>
  )
}

export default AuthPage