import React from 'react'
import { useLocation } from 'react-router-dom'
import Header from './Header'
import BottomNavigation from './BottomNavigation'

const Layout = ({ children }) => {
  const location = useLocation()
  const isAuthPage = location.pathname === '/auth'

  if (isAuthPage) {
    return children
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      <main className="flex-1 safe-area-top safe-area-bottom pb-20">
        {children}
      </main>
      <BottomNavigation />
    </div>
  )
}

export default Layout