import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import MachineCard from '../components/MachineCard'
import { 
  Monitor, 
  Plus, 
  RefreshCw, 
  LogOut, 
  User, 
  Settings,
  Search,
  Filter,
  Activity,
  Server,
  Zap,
  AlertCircle,
  TrendingUp,
  BarChart3
} from 'lucide-react'
import axios from 'axios'

function Dashboard() {
  const { user, logout } = useAuth()
  const [machines, setMachines] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [showAddMachine, setShowAddMachine] = useState(false)
  const [newMachine, setNewMachine] = useState({
    name: '',
    hostname: '',
    ip_address: '',
    mac_address: '',
    ha_entity_id: '',
    description: '',
    os_name: '',
    os_version: ''
  })
  const [addingMachine, setAddingMachine] = useState(false)
  const [error, setError] = useState('')

  const fetchMachines = async () => {
    try {
      const response = await axios.get('/api/machines/with-snapshots')
      setMachines(response.data)
      setError('')
    } catch (error) {
      console.error('Failed to fetch machines:', error)
      setError('Failed to load machines')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchMachines()
  }

  const handleAddMachine = async (e) => {
    e.preventDefault()
    setAddingMachine(true)
    setError('')

    try {
      const response = await axios.post('/api/machines/', newMachine)
      setMachines([...machines, { ...response.data, latest_snapshot: null }])
      setShowAddMachine(false)
      setNewMachine({
        name: '',
        hostname: '',
        ip_address: '',
        mac_address: '',
        ha_entity_id: '',
        description: '',
        os_name: '',
        os_version: ''
      })
    } catch (error) {
      console.error('Failed to add machine:', error)
      setError(error.response?.data?.detail || 'Failed to add machine')
    } finally {
      setAddingMachine(false)
    }
  }

  const filteredMachines = machines.filter(machine =>
    machine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    machine.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
    machine.ip_address.includes(searchTerm)
  )

  // Calculate dashboard statistics
  const dashboardStats = {
    total: machines.length,
    online: machines.filter(m => {
      if (!m.last_seen) return false
      const diffMinutes = (new Date() - new Date(m.last_seen)) / (1000 * 60)
      return diffMinutes < 5
    }).length,
    warning: machines.filter(m => {
      if (!m.last_seen) return false
      const diffMinutes = (new Date() - new Date(m.last_seen)) / (1000 * 60)
      return diffMinutes >= 5 && diffMinutes < 30
    }).length,
    offline: machines.filter(m => {
      if (!m.last_seen) return true
      const diffMinutes = (new Date() - new Date(m.last_seen)) / (1000 * 60)
      return diffMinutes >= 30
    }).length,
    withSnapshots: machines.filter(m => m.latest_snapshot).length
  }

  useEffect(() => {
    fetchMachines()
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchMachines, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-brand rounded-lg">
                <Monitor className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Machine Hub</h1>
                <p className="text-sm text-gray-500">{machines.length} machines</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
              
              <div className="flex items-center space-x-2 text-sm text-gray-700">
                <User className="h-4 w-4" />
                <span>{user?.username}</span>
              </div>
              
              <button
                onClick={logout}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0 mb-8">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search machines..."
                className="input pl-10 w-64"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          
          <button
            onClick={() => setShowAddMachine(true)}
            className="btn btn-primary flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Add Machine</span>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Machines Grid */}
        {filteredMachines.length === 0 ? (
          <div className="text-center py-12">
            <Monitor className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm ? 'No machines found' : 'No machines configured'}
            </h3>
            <p className="text-gray-500 mb-4">
              {searchTerm 
                ? 'Try adjusting your search terms'
                : 'Add your first machine to get started'
              }
            </p>
            {!searchTerm && (
              <button
                onClick={() => setShowAddMachine(true)}
                className="btn btn-primary"
              >
                Add Machine
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredMachines.map((machine) => (
              <MachineCard
                key={machine.id}
                machine={machine}
                onUpdate={fetchMachines}
              />
            ))}
          </div>
        )}
      </main>

      {/* Add Machine Modal */}
      {showAddMachine && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">Add New Machine</h2>
              <button
                onClick={() => setShowAddMachine(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <form onSubmit={handleAddMachine} className="space-y-6">
              {/* Basic Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Basic Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Machine Name *
                    </label>
                    <input
                      type="text"
                      required
                      className="input"
                      placeholder="e.g., Gaming PC"
                      value={newMachine.name}
                      onChange={(e) => setNewMachine({...newMachine, name: e.target.value})}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Hostname *
                    </label>
                    <input
                      type="text"
                      required
                      className="input"
                      placeholder="e.g., DESKTOP-ABC123"
                      value={newMachine.hostname}
                      onChange={(e) => setNewMachine({...newMachine, hostname: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* Network Configuration */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Network Configuration</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      IP Address *
                    </label>
                    <input
                      type="text"
                      required
                      className="input"
                      placeholder="e.g., 192.168.1.100"
                      value={newMachine.ip_address}
                      onChange={(e) => setNewMachine({...newMachine, ip_address: e.target.value})}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MAC Address (for Wake-on-LAN)
                    </label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., AA:BB:CC:DD:EE:FF"
                      value={newMachine.mac_address}
                      onChange={(e) => setNewMachine({...newMachine, mac_address: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* System Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">System Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Operating System
                    </label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., Windows 11"
                      value={newMachine.os_name}
                      onChange={(e) => setNewMachine({...newMachine, os_name: e.target.value})}
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      OS Version
                    </label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., 22H2"
                      value={newMachine.os_version}
                      onChange={(e) => setNewMachine({...newMachine, os_version: e.target.value})}
                    />
                  </div>
                </div>
              </div>

              {/* Integration */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Home Assistant Integration</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity ID
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g., switch.gaming_pc_plug"
                    value={newMachine.ha_entity_id}
                    onChange={(e) => setNewMachine({...newMachine, ha_entity_id: e.target.value})}
                  />
                  <p className="text-xs text-gray-500 mt-1">Optional: Home Assistant entity for power control</p>
                </div>
              </div>
              
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Optional description or notes about this machine..."
                  value={newMachine.description}
                  onChange={(e) => setNewMachine({...newMachine, description: e.target.value})}
                />
              </div>
              
              <div className="flex space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowAddMachine(false)}
                  className="btn btn-secondary flex-1"
                  disabled={addingMachine}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary flex-1 flex items-center justify-center space-x-2"
                  disabled={addingMachine}
                >
                  {addingMachine ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Adding Machine...</span>
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4" />
                      <span>Add Machine</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard