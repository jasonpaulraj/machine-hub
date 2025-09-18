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
  Server,
} from "lucide-react";
import axios from "axios";

function MachineCard({ machine, onUpdate }) {
  const [loading, setLoading] = useState(false);
  const [powerAction, setPowerAction] = useState("");

  const formatBytes = (bytes) => {
    if (!bytes) return "N/A";
    const gb = bytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(2)} GB`;
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
    if (!lastSeen) return "status-unknown";

    const now = new Date();
    // Add 'Z' to treat as UTC if no timezone info is present
    const lastSeenDate = new Date(lastSeen.includes('Z') || lastSeen.includes('+') ? lastSeen : lastSeen + 'Z');
    const diffMinutes = (now - lastSeenDate) / (1000 * 60);

    if (diffMinutes < 5) return "status-online";
    if (diffMinutes < 30) return "status-warning";
    return "status-offline";
  };

  const getStatusText = (lastSeen) => {
    if (!lastSeen) return "Unknown";

    const now = new Date();
    // Add 'Z' to treat as UTC if no timezone info is present
    const lastSeenDate = new Date(lastSeen.includes('Z') || lastSeen.includes('+') ? lastSeen : lastSeen + 'Z');
    const diffMinutes = (now - lastSeenDate) / (1000 * 60);

    if (diffMinutes < 5) return "Online";
    if (diffMinutes < 30) return "Warning";
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

  const snapshot = machine.latest_snapshot;
  const statusColor = getStatusColor(machine.last_seen);
  const statusText = getStatusText(machine.last_seen);

  return (
    <div className="card hover:shadow-md transition-shadow duration-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-brand/10 rounded-lg">
            <Monitor className="h-6 w-6 text-brand" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {machine.name}
            </h3>
            <p className="text-sm text-gray-500">{machine.hostname}</p>
          </div>
        </div>
        <div className={`status-indicator ${statusColor}`}>
          {statusText === "Online" && <CheckCircle className="h-3 w-3 mr-1" />}
          {statusText === "Warning" && (
            <AlertTriangle className="h-3 w-3 mr-1" />
          )}
          {statusText === "Offline" && <XCircle className="h-3 w-3 mr-1" />}
          {statusText}
        </div>
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
              ? new Date(machine.last_seen + 'Z').toLocaleString()
              : "Never"}
          </p>
        </div>
      </div>

      {/* Power Controls */}
      <div className="mb-4">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Power Controls</h4>
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

          {/* On/Off - depends on status */}
          {statusText === "Offline" ? (
            <button
              onClick={() => handlePowerAction("on")}
              disabled={loading}
              className="flex items-center px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading && powerAction === "on" ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-700 mr-2"></div>
              ) : (
                <Power className="h-4 w-4 mr-2" />
              )}
              Turn On
            </button>
          ) : (
            <button
              onClick={() => handlePowerAction("off")}
              disabled={loading}
              className="flex items-center px-3 py-2 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading && powerAction === "off" ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-700 mr-2"></div>
              ) : (
                <PowerOff className="h-4 w-4 mr-2" />
              )}
              Turn Off
            </button>
          )}

          {/* Restart - only if online */}
          {statusText !== "Offline" && (
            <button
              onClick={() => handlePowerAction("restart")}
              disabled={loading}
              className="flex items-center px-3 py-2 text-sm bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading && powerAction === "restart" ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-700 mr-2"></div>
              ) : (
                <RotateCcw className="h-4 w-4 mr-2" />
              )}
              Restart
            </button>
          )}
        </div>
      </div>

      {/* System Metrics */}
      {snapshot && (
        <div className="border-t border-gray-200 pt-4 mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">
            System Metrics
          </h4>
          <div className="grid grid-cols-2 gap-4">
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
              </div>
            </div>

            {/* Storage (from fs_data) */}
            <div className="flex items-center space-x-2">
              <HardDrive className="h-4 w-4 text-purple-500" />
              <div className="flex-1">
                <div className="flex justify-between text-xs">
                  <span>Storage</span>
                  <span>
                    {snapshot.fs_data && snapshot.fs_data.length > 0
                      ? `${(
                          (snapshot.fs_data[0].used /
                            snapshot.fs_data[0].size) *
                          100
                        ).toFixed(1)}%`
                      : "N/A"}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                  <div
                    className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                    style={{
                      width: `${
                        snapshot.fs_data && snapshot.fs_data.length > 0
                          ? (snapshot.fs_data[0].used /
                              snapshot.fs_data[0].size) *
                            100
                          : 0
                      }%`,
                    }}
                  ></div>
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

          {/* Additional metrics */}
          <div className="mt-3 pt-3 border-t border-gray-100">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="text-gray-500">Memory:</span>
                <span className="ml-1 font-medium">
                  {formatBytes(snapshot.memory_used)} /{" "}
                  {formatBytes(snapshot.memory_total)}
                </span>
              </div>
              <div>
                <span className="text-gray-500">Primary Storage:</span>
                <span className="ml-1 font-medium">
                  {snapshot.fs_data && snapshot.fs_data.length > 0
                    ? `${formatBytes(snapshot.fs_data[0].used)} / ${formatBytes(
                        snapshot.fs_data[0].size
                      )}`
                    : "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Enhanced Metrics */}
          <div className="space-y-3">
            {/* System Information */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Server className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">System Info</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
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
                <div>
                  <span className="text-gray-500">Cores:</span>
                  <span className="ml-1 font-medium">
                    {snapshot.cpu_count || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">Load:</span>
                  <span className="ml-1 font-medium">
                    {snapshot.load_avg
                      ? `${snapshot.load_avg.toFixed(2)}`
                      : "N/A"}
                  </span>
                </div>
              </div>
            </div>

            {/* Network Information */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Wifi className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">Network</span>
              </div>
              <div className="space-y-1 text-xs">
                {snapshot.network_data && snapshot.network_data.length > 0 ? (
                  snapshot.network_data.slice(0, 2).map((net, idx) => (
                    <div key={idx} className="flex justify-between">
                      <span className="text-gray-500">
                        {net.interface_name}:
                      </span>
                      <span className="font-medium">
                        ↓{formatBytes(net.bytes_recv)} ↑
                        {formatBytes(net.bytes_sent)}
                      </span>
                    </div>
                  ))
                ) : (
                  <span className="text-gray-500">No network data</span>
                )}
              </div>
            </div>

            {/* Storage Details */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Database className="h-4 w-4 text-purple-500" />
                <span className="text-sm font-medium">Storage Details</span>
              </div>
              <div className="space-y-1 text-xs">
                {snapshot.fs_data && snapshot.fs_data.length > 0 ? (
                  snapshot.fs_data.slice(0, 3).map((fs, idx) => (
                    <div key={idx} className="flex justify-between">
                      <span className="text-gray-500">{fs.mnt_point}:</span>
                      <span className="font-medium">
                        {formatBytes(fs.used)} / {formatBytes(fs.size)}
                      </span>
                    </div>
                  ))
                ) : (
                  <span className="text-gray-500">No storage data</span>
                )}
              </div>
            </div>

            {/* Sensors & Alerts */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="h-4 w-4 text-orange-500" />
                <span className="text-sm font-medium">Sensors & Status</span>
              </div>
              <div className="space-y-1 text-xs">
                {snapshot.sensors_data ? (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Temperature:</span>
                    <span className="font-medium">
                      {snapshot.sensors_data.cpu_temp
                        ? `${snapshot.sensors_data.cpu_temp}°C`
                        : "N/A"}
                    </span>
                  </div>
                ) : null}
                {snapshot.alert_data && snapshot.alert_data.length > 0 ? (
                  <div className="flex items-center space-x-1">
                    <AlertTriangle className="h-3 w-3 text-yellow-500" />
                    <span className="text-yellow-600">
                      {snapshot.alert_data.length} alerts
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    <span className="text-green-600">All systems normal</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}



      {/* Description */}
      {machine.description && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600">{machine.description}</p>
        </div>
      )}
    </div>
  );
}

export default MachineCard;
