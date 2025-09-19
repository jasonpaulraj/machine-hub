import React, { useState } from "react";
import {
  Monitor,
  Power,
  PowerOff,
  RotateCcw,
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Clock,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Activity,
  Thermometer,
  Battery,
  Users,
  Zap,
  Wifi,
  Database,
  Info,
  TrendingUp,
  TrendingDown,
  Server,
  Edit,
  Trash2,
  ChevronRight,
  Plug,
} from "lucide-react";
import axios from "axios";

function MachineCard({ machine, onUpdate, onEdit, onDelete }) {
  const [loading, setLoading] = useState(false);
  const [powerAction, setPowerAction] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [showAllAlerts, setShowAllAlerts] = useState(false);
  const [showAlertsModal, setShowAlertsModal] = useState(false);

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatUptime = (seconds) => {
    if (!seconds) return "N/A";
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getStatusColor = (lastSeen) => {
    if (!lastSeen) return "status-offline";

    const now = new Date();
    // Add 'Z' to treat as UTC if no timezone info is present
    const lastSeenDate = new Date(
      lastSeen.includes("Z") || lastSeen.includes("+")
        ? lastSeen
        : lastSeen + "Z"
    );
    const diffMinutes = (now - lastSeenDate) / (1000 * 60);

    if (diffMinutes < 5) return "status-online";
    return "status-offline";
  };

  const getStatusText = (lastSeen) => {
    if (!lastSeen) return "Offline";

    const now = new Date();
    // Add 'Z' to treat as UTC if no timezone info is present
    const lastSeenDate = new Date(
      lastSeen.includes("Z") || lastSeen.includes("+")
        ? lastSeen
        : lastSeen + "Z"
    );
    const diffMinutes = (now - lastSeenDate) / (1000 * 60);

    if (diffMinutes < 5) return "Online";
    return "Offline";
  };

  const handlePowerAction = async (action) => {
    setLoading(true);
    setPowerAction(action);

    try {
      const response = await axios.post(`/api/machines/${machine.id}/power`, {
        action: action,
      });

      if (response.data.success) {
        // Show success message or update UI
        console.log(`Power ${action} successful:`, response.data.message);
        if (onUpdate) {
          onUpdate();
        }
      } else {
        console.error(`Power ${action} failed:`, response.data.message);
      }
    } catch (error) {
      console.error(
        `Power ${action} error:`,
        error.response?.data?.detail || error.message
      );
    } finally {
      setLoading(false);
      setPowerAction("");
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(machine);
    }
  };

  const handleDelete = async () => {
    if (
      window.confirm(
        `Are you sure you want to delete machine "${machine.name}"? This action cannot be undone.`
      )
    ) {
      setActionLoading(true);
      try {
        const response = await axios.delete(`/api/machines/${machine.id}`);

        if (response.data.success || response.status === 200) {
          console.log("Machine deleted successfully");
          if (onDelete) {
            onDelete(machine.id);
          }
          if (onUpdate) {
            onUpdate();
          }
        } else {
          console.error("Delete failed:", response.data.message);
          alert("Failed to delete machine. Please try again.");
        }
      } catch (error) {
        console.error(
          "Delete error:",
          error.response?.data?.detail || error.message
        );
        alert("Failed to delete machine. Please try again.");
      } finally {
        setActionLoading(false);
      }
    }
  };

  const snapshot = machine.latest_snapshot;
  const statusColor = getStatusColor(machine.last_seen);
  const statusText = getStatusText(machine.last_seen);

  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      {/* Header */}
      <div className="mb-4">
        {/* Main Header Row */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <div className="p-2 bg-brand/10 rounded-lg flex-shrink-0">
              <Monitor className="h-6 w-6 text-brand" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {machine.name}
              </h3>
              <p className="text-sm text-gray-500 truncate">
                {machine.hostname}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-1 flex-shrink-0">
            <button
              onClick={handleEdit}
              disabled={actionLoading}
              className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Edit machine"
            >
              <Edit className="h-4 w-4" />
            </button>
            <button
              onClick={handleDelete}
              disabled={actionLoading}
              className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Delete machine"
            >
              {actionLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600"></div>
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Status and Battery Row */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          {/* Status Indicator */}
          <div className={`status-indicator ${statusColor}`}>
            {statusText === "Online" && (
              <CheckCircle className="h-3 w-3 mr-1" />
            )}
            {statusText === "Warning" && (
              <AlertTriangle className="h-3 w-3 mr-1" />
            )}
            {statusText === "Offline" && <XCircle className="h-3 w-3 mr-1" />}
            {statusText}
          </div>

          {/* Battery Status - Far Right */}
          {snapshot && snapshot.battery_status !== null && (
            <div className="flex items-center space-x-2">
              {/* Battery Status Indicator */}
              {snapshot.battery_status && (
                <>
                  {snapshot.battery_status.toLowerCase() === "charging" && (
                    <Zap className="h-3 w-3 text-green-500" title="Charging" />
                  )}
                  {snapshot.battery_status.toLowerCase() === "discharging" && (
                    <TrendingDown
                      className="h-3 w-3 text-orange-500"
                      title="Discharging"
                    />
                  )}
                </>
              )}

              <div className="flex items-center space-x-1">
                <div className="relative">
                  <div className="w-6 h-3 border border-gray-400 rounded-sm bg-white relative overflow-hidden">
                    <div
                      className={`h-full transition-all duration-300 ${
                        snapshot.battery_percent > 20
                          ? snapshot.battery_percent > 50
                            ? "bg-green-500"
                            : "bg-yellow-500"
                          : "bg-red-500"
                      }`}
                      style={{
                        width: `${Math.max(
                          0,
                          Math.min(100, snapshot.battery_percent)
                        )}%`,
                      }}
                    ></div>
                  </div>
                  <div className="absolute -right-0.5 top-0.5 w-0.5 h-2 bg-gray-400 rounded-r-sm"></div>
                </div>
                <span className="text-xs font-medium text-gray-600">
                  {snapshot.battery_percent}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        {machine.description && (
          <div className="grid grid-cols-1 gap-4 mb-4 text-sm mt-5">
            <div>
              <span className="text-gray-500">Description:</span>
              <p className="font-medium">{machine.description}</p>
            </div>
          </div>
        )}
      </div>

      {/* Machine Info */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-gray-500">IP Address:</span>
          <p className="font-medium">{machine.ip_address}</p>
        </div>
        <div>
          <span className="text-gray-500">Last Seen:</span>
          <p className="font-medium">
            {machine.last_seen
              ? new Date(machine.last_seen + "Z").toLocaleString()
              : "Never"}
          </p>
        </div>
      </div>

      {/* Power Controls - Only show if device is offline */}
      {statusText === "Offline" && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">
            Power Controls
          </h4>
          <div className="flex space-x-2">
            {/* Wake Up - Always available */}
            <button
              onClick={() => handlePowerAction("wake")}
              disabled={loading}
              className="flex items-center px-3 py-2 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading && powerAction === "wake" ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-700 mr-2"></div>
              ) : (
                <Zap className="h-4 w-4 mr-2" />
              )}
              Wake Up
            </button>
          </div>
        </div>
      )}

      {/* System Metrics */}
      {snapshot && (
        <div className="border-t border-gray-200 pt-4 mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            System Metrics
          </h4>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {/* CPU */}
            <div className="flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-blue-500" />
              <div className="flex-1">
                <div className="flex justify-between text-xs">
                  <span>CPU</span>
                  <span>
                    {snapshot.cpu_percent
                      ? `${snapshot.cpu_percent.toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                  <div
                    className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${snapshot.cpu_percent || 0}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {snapshot.cpu_count ? `${snapshot.cpu_count} cores` : "N/A"} •
                  {snapshot.load_avg
                    ? `${snapshot.load_avg.toFixed(2)} load`
                    : "N/A"}
                </div>
              </div>
            </div>

            {/* Memory */}
            <div className="flex items-center space-x-2">
              <MemoryStick className="h-4 w-4 text-green-500" />
              <div className="flex-1">
                <div className="flex justify-between text-xs">
                  <span>Memory</span>
                  <span>
                    {snapshot.memory_percent
                      ? `${snapshot.memory_percent.toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                  <div
                    className="bg-green-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${snapshot.memory_percent || 0}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {typeof snapshot.memory_used === "number" &&
                  snapshot.memory_used < 1000
                    ? `${snapshot.memory_used.toFixed(
                        2
                      )} GB / ${snapshot.memory_total.toFixed(2)} GB`
                    : `${formatBytes(snapshot.memory_used)} / ${formatBytes(
                        snapshot.memory_total
                      )}`}
                </div>
              </div>
            </div>

            {/* System Information */}
            <div className="flex items-center space-x-2">
              <Server className="h-4 w-4 text-blue-500" />
              <div className="flex-1">
                <div className="text-xs text-gray-500 mb-1">System Info</div>
                <div className="text-xs space-y-0.5">
                  <div>
                    <span className="text-gray-500">OS:</span>
                    <span className="ml-1 font-medium">
                      {machine.os_name || "N/A"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-500">Version:</span>
                    <span className="ml-1 font-medium">
                      {machine.os_version || "N/A"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Uptime */}
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-orange-500" />
              <div className="flex-1">
                <div className="text-xs text-gray-500">Uptime</div>
                <div className="text-xs font-medium">
                  {formatUptime(snapshot.uptime)}
                </div>
              </div>
            </div>
          </div>

          {/* Full Width Sections */}
          <div className="space-y-3">
            {/* Network Information */}
            <div className="flex items-center space-x-2">
              <Wifi className="h-4 w-4 text-green-500" />
              <div className="flex-1">
                <div className="text-xs text-gray-500 mb-1">Network</div>
                <div className="space-y-2">
                  {snapshot.network_data && snapshot.network_data.length > 0 ? (
                    snapshot.network_data
                      .filter(
                        (net) =>
                          net.bytes_recv_gauge > 0 || net.bytes_sent_gauge > 0
                      )
                      .slice(0, 2)
                      .map((net, idx) => {
                        const maxBytes = Math.max(
                          net.bytes_recv_gauge,
                          net.bytes_sent_gauge
                        );
                        const recvPercent =
                          maxBytes > 0
                            ? (net.bytes_recv_gauge / maxBytes) * 100
                            : 0;
                        const sentPercent =
                          maxBytes > 0
                            ? (net.bytes_sent_gauge / maxBytes) * 100
                            : 0;
                        return (
                          <div key={idx} className="space-y-1">
                            <div className="text-xs text-gray-500 font-medium">
                              {net.interface_name}
                            </div>
                            {/* Receive Bar */}
                            <div className="space-y-0.5">
                              <div className="flex justify-between text-xs">
                                <span className="text-gray-500">↓ Receive</span>
                                <span className="font-medium">
                                  {formatBytes(net.bytes_recv_gauge)}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1">
                                <div
                                  className="bg-green-500 h-1 rounded-full transition-all duration-300"
                                  style={{ width: `${recvPercent}%` }}
                                ></div>
                              </div>
                            </div>
                            {/* Send Bar */}
                            <div className="space-y-0.5">
                              <div className="flex justify-between text-xs">
                                <span className="text-gray-500">↑ Send</span>
                                <span className="font-medium">
                                  {formatBytes(net.bytes_sent_gauge)}
                                </span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1">
                                <div
                                  className="bg-red-500 h-1 rounded-full transition-all duration-300"
                                  style={{ width: `${sentPercent}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        );
                      })
                  ) : (
                    <span className="text-gray-500 text-xs">
                      No network data
                    </span>
                  )}
                </div>
              </div>
            </div>
            {/* Storage Details */}
            <div className="flex items-start space-x-2">
              <Database className="h-4 w-4 text-purple-500 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs text-gray-500 mb-2">
                  Storage Details
                </div>
                <div className="space-y-1">
                  {snapshot.fs_data && snapshot.fs_data.length > 0 ? (
                    (() => {
                      // Only combine for non-Windows/Linux systems (like macOS)
                      if (
                        machine.os_name &&
                        !machine.os_name.toLowerCase().includes("windows") &&
                        !machine.os_name.toLowerCase().includes("linux")
                      ) {
                        const totalUsed = snapshot.fs_data.reduce(
                          (sum, fs) => sum + fs.used,
                          0
                        );
                        // Use the first storage entry for size and calculate percentage with totalUsed
                        const mainStorage = snapshot.fs_data[0];
                        const fsPercent = mainStorage.size > 0 ? (totalUsed / mainStorage.size) * 100 : 0;
                        return (
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs">
                              <span className="text-gray-500">
                                System
                              </span>
                              <span className="font-medium">
                                {fsPercent.toFixed(1)}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-1.5">
                              <div
                                className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                                style={{ width: `${fsPercent}%` }}
                              ></div>
                            </div>
                            <div className="text-xs text-gray-400">
                              {formatBytes(totalUsed)} /{" "}
                              {formatBytes(mainStorage.size)}
                            </div>
                          </div>
                        );
                      } else {
                        // Show individual storage for Windows/Linux
                        return (
                          <div className="grid grid-cols-1 gap-1">
                            {snapshot.fs_data.slice(0, 10).map((fs, index) => {
                              const fsPercent =
                                fs.size > 0 ? (fs.used / fs.size) * 100 : 0;
                              return (
                                <div key={index} className="space-y-1">
                                  <div className="flex justify-between text-xs">
                                    <span
                                      className="text-gray-500 truncate"
                                      title={fs.device_name || "Storage"}
                                    >
                                      {fs.mountpoint && fs.mountpoint.length > 8
                                        ? `${fs.mountpoint.substring(0, 8)}...`
                                        : fs.device_name || "Storage"}
                                    </span>
                                    <span className="font-medium">
                                      {fsPercent.toFixed(1)}%
                                    </span>
                                  </div>
                                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                                    <div
                                      className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                                      style={{ width: `${fsPercent}%` }}
                                    ></div>
                                  </div>
                                  <div className="text-xs text-gray-400">
                                    {formatBytes(fs.used)} /{" "}
                                    {formatBytes(fs.size)}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        );
                      }
                    })()
                  ) : (
                    <span className="text-gray-500 text-xs">
                      No storage data
                    </span>
                  )}
                </div>
              </div>
            </div>
            {/* Sensors & Alerts */}
            <div className="flex items-start space-x-2">
              <TrendingUp className="h-4 w-4 text-orange-500 mt-0.5" />
              <div className="flex-1">
                <div className="text-xs text-gray-500 mb-2">
                  Sensors & Status
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {snapshot.sensors_data ? (
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">
                        Temperature:
                      </span>
                      <span className="text-xs font-medium">
                        {snapshot.sensors_data.cpu_temp
                          ? `${snapshot.sensors_data.cpu_temp}°C`
                          : "N/A"}
                      </span>
                    </div>
                  ) : null}
                  {snapshot.alert_data ? (
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-500">Alerts:</span>
                      {snapshot.alert_data && snapshot.alert_data.length > 0 ? (
                        <button
                          onClick={() => setShowAlertsModal(true)}
                          className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-white bg-blue-500 hover:bg-blue-600 rounded transition-colors"
                        >
                          <AlertTriangle className="h-3 w-3" />
                          {snapshot.alert_data.length}
                        </button>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-gray-600 bg-green-100 rounded">
                          <CheckCircle className="h-3 w-3 text-green-600" />0
                        </span>
                      )}
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts Modal */}
      {showAlertsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full max-h-[80vh] overflow-hidden shadow-xl animate-in fade-in-0 zoom-in-95 duration-200">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-orange-500" />
                <h3 className="text-base font-medium text-gray-900">
                  Alerts ({snapshot.alert_data?.length || 0})
                </h3>
              </div>
              <button
                onClick={() => setShowAlertsModal(false)}
                className="p-1 text-gray-400 hover:text-gray-600 rounded transition-colors"
              >
                <svg
                  className="w-4 h-4"
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

            {/* Content */}
            <div className="p-4 overflow-y-auto max-h-[calc(80vh-80px)]">
              {snapshot.alert_data && snapshot.alert_data.length > 0 ? (
                <div className="space-y-2">
                  {snapshot.alert_data
                    .slice(0, showAllAlerts ? snapshot.alert_data.length : 10)
                    .map((alert, index) => {
                      const getAlertColor = (state) => {
                        switch (state) {
                          case "OK":
                            return "border-green-300 bg-green-50";
                          case "WARNING":
                            return "border-yellow-300 bg-yellow-50";
                          case "CRITICAL":
                            return "border-red-300 bg-red-50";
                          default:
                            return "border-gray-300 bg-gray-50";
                        }
                      };

                      const getStateColor = (state) => {
                        switch (state) {
                          case "OK":
                            return "bg-green-100 text-green-700";
                          case "WARNING":
                            return "bg-yellow-100 text-yellow-700";
                          case "CRITICAL":
                            return "bg-red-100 text-red-700";
                          default:
                            return "bg-gray-100 text-gray-700";
                        }
                      };

                      return (
                        <div
                          key={index}
                          className={`rounded-lg border ${getAlertColor(
                            alert.state
                          )} p-3`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <AlertTriangle
                                className={`h-3 w-3 ${
                                  alert.state === "CRITICAL"
                                    ? "text-red-600"
                                    : alert.state === "WARNING"
                                    ? "text-yellow-600"
                                    : "text-green-600"
                                }`}
                              />
                              <span
                                className={`px-2 py-1 rounded text-xs font-medium ${getStateColor(
                                  alert.state
                                )}`}
                              >
                                {alert.state || "Unknown"}
                              </span>
                              <span className="text-sm font-medium text-gray-900">
                                {alert.type || "Alert"}
                              </span>
                            </div>
                            <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {alert.sort || "?"}
                            </span>
                          </div>
                          {alert.global_message && (
                            <div className="mt-2 pt-2 border-t border-gray-200">
                              <p className="text-xs text-gray-600">
                                {alert.global_message}
                              </p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  {snapshot.alert_data.length > 10 && (
                    <div className="mt-3">
                      <button
                        onClick={() => setShowAllAlerts(!showAllAlerts)}
                        className="w-full flex items-center justify-center gap-1 py-2 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
                      >
                        {showAllAlerts ? (
                          <>
                            <ChevronRight className="h-3 w-3 rotate-90" />
                            Show less
                          </>
                        ) : (
                          <>
                            <ChevronRight className="h-3 w-3" />
                            Show all ({snapshot.alert_data.length})
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8">
                  <CheckCircle className="h-6 w-6 text-green-600 mb-2" />
                  <p className="text-sm text-gray-600 text-center">
                    No alerts - system running normally
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MachineCard;
