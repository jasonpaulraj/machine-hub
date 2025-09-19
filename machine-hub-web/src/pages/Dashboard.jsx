import React, { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import MachineCard from "../components/MachineCard";
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
  BarChart3,
  Bell,
  Home,
  Grid3X3,
  ChevronDown,
} from "lucide-react";
import axios from "axios";

function Dashboard() {
  const { user, logout } = useAuth();
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddMachine, setShowAddMachine] = useState(false);
  const [newMachine, setNewMachine] = useState({
    name: "",
    hostname: "",
    ip_address: "",
    mac_address: "",
    ha_entity_id: "",
    description: "",
    os_name: "",
    os_version: "",
  });
  const [addingMachine, setAddingMachine] = useState(false);
  const [showEditMachine, setShowEditMachine] = useState(false);
  const [editMachine, setEditMachine] = useState({
    id: null,
    name: "",
    hostname: "",
    ip_address: "",
    mac_address: "",
    ha_entity_id: "",
    description: "",
    os_name: "",
    os_version: "",
  });
  const [editingMachine, setEditingMachine] = useState(false);
  const [error, setError] = useState("");
  const [showUserMenu, setShowUserMenu] = useState(false);

  const fetchMachines = async () => {
    try {
      const response = await axios.get("/api/machines/with-snapshots");
      setMachines(response.data);
      setError("");
    } catch (error) {
      console.error("Failed to fetch machines:", error);
      setError("Failed to load machines");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchMachines();
  };

  const handleAddMachine = async (e) => {
    e.preventDefault();
    setAddingMachine(true);
    setError("");

    try {
      const response = await axios.post("/api/machines/", newMachine);
      setMachines([...machines, { ...response.data, latest_snapshot: null }]);
      setShowAddMachine(false);
      setNewMachine({
        name: "",
        hostname: "",
        ip_address: "",
        mac_address: "",
        ha_entity_id: "",
        description: "",
        os_name: "",
        os_version: "",
      });
    } catch (error) {
      console.error("Failed to add machine:", error);
      setError(error.response?.data?.detail || "Failed to add machine");
    } finally {
      setAddingMachine(false);
    }
  };

  const handleEditMachine = async (e) => {
    e.preventDefault();
    setEditingMachine(true);
    setError("");

    try {
      const { id, ...updateData } = editMachine;
      const response = await axios.put(`/api/machines/${id}`, updateData);
      setMachines(
        machines.map((m) => (m.id === id ? { ...m, ...response.data } : m))
      );
      setShowEditMachine(false);
      setEditMachine({
        id: null,
        name: "",
        hostname: "",
        ip_address: "",
        mac_address: "",
        ha_entity_id: "",
        description: "",
        os_name: "",
        os_version: "",
      });
    } catch (error) {
      console.error("Failed to update machine:", error);
      setError(error.response?.data?.detail || "Failed to update machine");
    } finally {
      setEditingMachine(false);
    }
  };

  const handleOpenEditModal = (machine) => {
    setEditMachine({
      id: machine.id,
      name: machine.name || "",
      hostname: machine.hostname || "",
      ip_address: machine.ip_address || "",
      mac_address: machine.mac_address || "",
      ha_entity_id: machine.ha_entity_id || "",
      description: machine.description || "",
      os_name: machine.os_name || "",
      os_version: machine.os_version || "",
    });
    setShowEditMachine(true);
  };

  const filteredMachines = machines.filter(
    (machine) =>
      machine.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      machine.hostname.toLowerCase().includes(searchTerm.toLowerCase()) ||
      machine.ip_address.includes(searchTerm)
  );

  // Calculate dashboard statistics
  const dashboardStats = {
    total: machines.length,
    online: machines.filter((m) => {
      if (!m.last_seen) return false;
      const diffMinutes = (new Date() - new Date(m.last_seen)) / (1000 * 60);
      return diffMinutes < 5; // Consider online if seen within 5 minutes
    }).length,
    offline: machines.filter((m) => {
      if (!m.last_seen) return true;
      const diffMinutes = (new Date() - new Date(m.last_seen)) / (1000 * 60);
      return diffMinutes >= 5;
    }).length,
    withSnapshots: machines.filter((m) => m.latest_snapshot).length,
  };

  useEffect(() => {
    fetchMachines();

    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchMachines, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showUserMenu && !event.target.closest(".user-menu")) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showUserMenu]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Modern Navigation Header */}
      <nav className="bg-white/80 backdrop-blur-md border-b border-white/20 shadow-lg shadow-black/5 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* Logo and Brand */}
            <div className="flex items-center space-x-4">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl blur opacity-75"></div>
                <div className="relative p-3 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl">
                  <Monitor className="h-7 w-7 text-white" />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                  Machine Hub
                </h1>
                <p className="text-sm text-gray-500 font-medium">
                  {machines.length} machines • {dashboardStats.online} online
                </p>
              </div>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-3">
              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                disabled={refreshing}
                className="relative p-2.5 bg-white/70 hover:bg-white border border-gray-200/50 rounded-xl transition-all hover:shadow-md group"
              >
                <RefreshCw
                  className={`h-4 w-4 text-gray-600 group-hover:text-gray-900 transition-colors ${
                    refreshing ? "animate-spin" : ""
                  }`}
                />
              </button>

              {/* User Menu */}
              <div className="relative user-menu">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center space-x-3 p-2 bg-white/70 hover:bg-white border border-gray-200/50 rounded-xl transition-all hover:shadow-md group"
                >
                  <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <div className="hidden sm:block text-left">
                    <p className="text-sm font-medium text-gray-900">
                      {user?.username}
                    </p>
                    <p className="text-xs text-gray-500">Administrator</p>
                  </div>
                  <ChevronDown
                    className={`h-4 w-4 text-gray-400 group-hover:text-gray-600 transition-all duration-200 ${
                      showUserMenu ? "rotate-180" : ""
                    }`}
                  />
                </button>

                {/* Dropdown Menu */}
                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-48 bg-white/90 backdrop-blur-md border border-gray-200/50 rounded-xl shadow-lg shadow-black/10 z-50">
                    <div className="p-2">
                      <div className="px-3 py-2 border-b border-gray-200/50">
                        <p className="text-sm font-medium text-gray-900">
                          {user?.username}
                        </p>
                        <p className="text-xs text-gray-500">Administrator</p>
                      </div>
                      <button
                        onClick={() => {
                          logout();
                          setShowUserMenu(false);
                        }}
                        className="w-full flex items-center space-x-2 px-3 py-2 mt-1 text-red-600 hover:bg-red-50 rounded-lg transition-all font-medium"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Logout</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8 mt-5">
        {/* Controls Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center space-y-4 sm:space-y-0 mb-8">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowAddMachine(true)}
              className="flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:-translate-y-0.5"
            >
              <Plus className="h-5 w-5" />
              <span>Add Machine</span>
            </button>
          </div>

          {/* Mobile Search */}
          <div className="relative sm:hidden w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search machines..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-3 w-full bg-white/70 border border-gray-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/30 transition-all placeholder-gray-400"
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50/80 backdrop-blur-sm border border-red-200/50 rounded-2xl p-6 mb-8 shadow-lg shadow-red-500/5">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <h3 className="font-medium text-red-900">Error</h3>
                <p className="text-red-700 text-sm mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Machines Grid */}
        {filteredMachines.length === 0 ? (
          <div className="text-center py-20">
            <div className="relative mb-8">
              <div className="absolute inset-0 bg-gradient-to-r from-gray-200 to-gray-300 rounded-full blur opacity-50"></div>
              <div className="relative p-6 bg-gradient-to-r from-gray-100 to-gray-200 rounded-full inline-block">
                <Monitor className="h-16 w-16 text-gray-400" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-3">
              {searchTerm ? "No machines found" : "Welcome to Machine Hub"}
            </h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
              {searchTerm
                ? "Try adjusting your search terms or check your spelling"
                : "Get started by adding your first machine to monitor and manage your infrastructure"}
            </p>
            {!searchTerm && (
              <button
                onClick={() => setShowAddMachine(true)}
                className="inline-flex items-center space-x-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/30 hover:-translate-y-0.5"
              >
                <Plus className="h-5 w-5" />
                <span>Add Your First Machine</span>
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
            {filteredMachines.map((machine) => (
              <MachineCard
                key={machine.id}
                machine={machine}
                onUpdate={fetchMachines}
                onEdit={handleOpenEditModal}
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
              <h2 className="text-xl font-semibold text-gray-900">
                Add New Machine
              </h2>
              <button
                onClick={() => setShowAddMachine(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <form onSubmit={handleAddMachine} className="space-y-6">
              {/* Basic Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Basic Information
                </h3>
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
                      onChange={(e) =>
                        setNewMachine({ ...newMachine, name: e.target.value })
                      }
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
                      onChange={(e) =>
                        setNewMachine({
                          ...newMachine,
                          hostname: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* Network Configuration */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Network Configuration
                </h3>
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
                      onChange={(e) =>
                        setNewMachine({
                          ...newMachine,
                          ip_address: e.target.value,
                        })
                      }
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
                      onChange={(e) =>
                        setNewMachine({
                          ...newMachine,
                          mac_address: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* System Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  System Information
                </h3>
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
                      onChange={(e) =>
                        setNewMachine({
                          ...newMachine,
                          os_name: e.target.value,
                        })
                      }
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
                      onChange={(e) =>
                        setNewMachine({
                          ...newMachine,
                          os_version: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* Integration */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Home Assistant Integration
                </h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity ID
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g., switch.gaming_pc_plug"
                    value={newMachine.ha_entity_id}
                    onChange={(e) =>
                      setNewMachine({
                        ...newMachine,
                        ha_entity_id: e.target.value,
                      })
                    }
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Optional: Home Assistant entity for power control
                  </p>
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
                  onChange={(e) =>
                    setNewMachine({
                      ...newMachine,
                      description: e.target.value,
                    })
                  }
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

      {/* Edit Machine Modal */}
      {showEditMachine && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900">
                Edit Machine
              </h2>
              <button
                onClick={() => setShowEditMachine(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <form onSubmit={handleEditMachine} className="space-y-6">
              {/* Basic Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Basic Information
                </h3>
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
                      value={editMachine.name}
                      onChange={(e) =>
                        setEditMachine({ ...editMachine, name: e.target.value })
                      }
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
                      placeholder="e.g., gaming-pc"
                      value={editMachine.hostname}
                      onChange={(e) =>
                        setEditMachine({
                          ...editMachine,
                          hostname: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      IP Address *
                    </label>
                    <input
                      type="text"
                      required
                      className="input"
                      placeholder="e.g., 192.168.1.100"
                      value={editMachine.ip_address}
                      onChange={(e) =>
                        setEditMachine({
                          ...editMachine,
                          ip_address: e.target.value,
                        })
                      }
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      MAC Address
                    </label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., AA:BB:CC:DD:EE:FF"
                      value={editMachine.mac_address}
                      onChange={(e) =>
                        setEditMachine({
                          ...editMachine,
                          mac_address: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* System Information */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  System Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Operating System
                    </label>
                    <input
                      type="text"
                      className="input"
                      placeholder="e.g., Windows 11"
                      value={editMachine.os_name}
                      onChange={(e) =>
                        setEditMachine({
                          ...editMachine,
                          os_name: e.target.value,
                        })
                      }
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
                      value={editMachine.os_version}
                      onChange={(e) =>
                        setEditMachine({
                          ...editMachine,
                          os_version: e.target.value,
                        })
                      }
                    />
                  </div>
                </div>
              </div>

              {/* Integration */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Home Assistant Integration
                </h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Entity ID
                  </label>
                  <input
                    type="text"
                    className="input"
                    placeholder="e.g., switch.gaming_pc_plug"
                    value={editMachine.ha_entity_id}
                    onChange={(e) =>
                      setEditMachine({
                        ...editMachine,
                        ha_entity_id: e.target.value,
                      })
                    }
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Optional: Home Assistant entity for power control
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  className="input"
                  rows={3}
                  placeholder="Optional description or notes about this machine..."
                  value={editMachine.description}
                  onChange={(e) =>
                    setEditMachine({
                      ...editMachine,
                      description: e.target.value,
                    })
                  }
                />
              </div>

              <div className="flex space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => setShowEditMachine(false)}
                  className="btn btn-secondary flex-1"
                  disabled={editingMachine}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary flex-1 flex items-center justify-center space-x-2"
                  disabled={editingMachine}
                >
                  {editingMachine ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      <span>Saving Changes...</span>
                    </>
                  ) : (
                    <>
                      <span>Save Changes</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
