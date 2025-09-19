#!/usr/bin/env python3
"""
Real Glances Data Sender
Sends actual system metrics from Glances to the webhook endpoint
"""

import subprocess
import json
import requests
import time
import os
import sys
import argparse
from datetime import datetime

# Check if we're in production environment from command line or env


def get_environment():
    # Check command line arguments first
    for i, arg in enumerate(sys.argv):
        if arg == '--env' and i + 1 < len(sys.argv):
            return sys.argv[i + 1].lower() == 'production'
    # Fall back to environment variable
    return os.getenv('ENV', '').lower() == 'production'


IS_PRODUCTION = get_environment()


def get_real_glances_data():
    """Get real system data from Glances REST API"""
    try:
        # Get data from Glances REST API running on port 61208
        glances_api_url = 'http://192.168.100.72:61208/api/4/all'
        response = requests.get(glances_api_url, timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            print(
                f"Error getting data from Glances API: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to Glances API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Glances API: {e}")
        return None
    except Exception as e:
        print(f"Error getting Glances data: {e}")
        return None


def get_temperature_data(system_password=None):
    """Get temperature data based on operating system"""
    import platform
    system = platform.system().lower()
    temperature_sensors = []

    try:
        if system == 'linux':
            # Try to read from thermal zones
            try:
                import glob
                thermal_zones = glob.glob(
                    '/sys/class/thermal/thermal_zone*/temp')
                for i, zone_file in enumerate(thermal_zones):
                    try:
                        with open(zone_file, 'r') as f:
                            temp_millicelsius = int(f.read().strip())
                            temp_celsius = temp_millicelsius / 1000.0
                            temperature_sensors.append({
                                "label": f"CPU Thermal Zone {i}",
                                "value": round(temp_celsius, 1),
                                "unit": "°C",
                                "status": "Normal" if temp_celsius < 80 else "Hot",
                                "type": "temperature",
                                "key": "label"
                            })
                    except (IOError, ValueError):
                        continue
            except ImportError:
                pass

            # Fallback: try sensors command
            if not temperature_sensors:
                try:
                    result = subprocess.run(
                        ['sensors'], capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if '°C' in line and ('Core' in line or 'CPU' in line or 'temp' in line.lower()):
                                parts = line.split()
                                for part in parts:
                                    if '°C' in part:
                                        try:
                                            temp_str = part.replace(
                                                '°C', '').replace('+', '')
                                            temp_value = float(temp_str)
                                            label = line.split(':')[0].strip(
                                            ) if ':' in line else 'CPU Temperature'
                                            temperature_sensors.append({
                                                "label": label,
                                                "value": round(temp_value, 1),
                                                "unit": "°C",
                                                "status": "Normal" if temp_value < 80 else "Hot",
                                                "type": "temperature",
                                                "key": "label"
                                            })
                                            break
                                        except ValueError:
                                            continue
                except (subprocess.SubprocessError, FileNotFoundError):
                    pass

        elif system == 'darwin':  # macOS
            # Try powermetrics with sudo for accurate temperature readings
            if system_password:
                if not IS_PRODUCTION:
                    print("[DEBUG] Attempting powermetrics with sudo...")
                try:
                    # Use powermetrics with sudo to get CPU, thermal, and GPU sensor data
                    cmd = ['sudo', '-S', 'powermetrics', '--samplers',
                           'cpu_power,thermal,gpu_power', '-n', '1']
                    if not IS_PRODUCTION:
                        print(f"[DEBUG] Running command: {' '.join(cmd)}")

                    process = subprocess.Popen(
                        cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    stdout, stderr = process.communicate(
                        input=system_password + '\n', timeout=15)

                    if process.returncode == 0:
                        lines = stdout.split('\n')
                        if not IS_PRODUCTION:
                            print(
                                f"[DEBUG] Processing {len(lines)} lines of output")

                        # Parse comprehensive powermetrics data
                        sensors_found = False
                        current_section = None

                        for i, line in enumerate(lines):
                            line_stripped = line.strip()
                            line_lower = line_stripped.lower()
                            # Parse CPU Power (appears directly without section header)
                            if 'cpu power:' in line_lower:
                                try:
                                    power_match = line_stripped.split(
                                        'CPU Power:')[-1].strip()
                                    if 'mW' in power_match:
                                        power_value_mw = float(
                                            power_match.replace('mW', '').strip())
                                        power_value_w = power_value_mw / 1000.0  # Convert mW to W
                                        temperature_sensors.append({
                                            "label": "CPU Power",
                                            "value": power_value_w,
                                            "unit": "W",
                                            "status": "Normal" if power_value_w < 5.0 else "High",
                                            "type": "power",
                                            "key": "label"
                                        })
                                        sensors_found = True
                                        if not IS_PRODUCTION:
                                            print(
                                                f"[DEBUG] Found CPU Power: {power_value_w} W")
                                except (ValueError, IndexError):
                                    continue

                            # Parse GPU Power (appears directly and also in GPU usage section)
                            elif 'gpu power:' in line_lower:
                                try:
                                    gpu_power_match = line_stripped.split(
                                        'GPU Power:')[-1].strip()
                                    if 'mW' in gpu_power_match:
                                        gpu_power_value_mw = float(
                                            gpu_power_match.replace('mW', '').strip())
                                        gpu_power_value_w = gpu_power_value_mw / 1000.0  # Convert mW to W
                                        temperature_sensors.append({
                                            "label": "GPU Power",
                                            "value": gpu_power_value_w,
                                            "unit": "W",
                                            "status": "Normal" if gpu_power_value_w < 10.0 else "High",
                                            "type": "power",
                                            "key": "label"
                                        })
                                        sensors_found = True
                                        if not IS_PRODUCTION:
                                            print(
                                                f"[DEBUG] Found GPU Power: {gpu_power_value_w} W")
                                except (ValueError, IndexError):
                                    continue

                            # Parse Combined Power
                            elif 'combined power' in line_lower and 'mw' in line_lower:
                                try:
                                    combined_match = line_stripped.split(
                                        '):')[-1].strip()
                                    if 'mW' in combined_match:
                                        combined_value_mw = float(
                                            combined_match.replace('mW', '').strip())
                                        combined_value_w = combined_value_mw / 1000.0  # Convert mW to W
                                        temperature_sensors.append({
                                            "label": "Combined Power",
                                            "value": combined_value_w,
                                            "unit": "W",
                                            "status": "Normal" if combined_value_w < 15.0 else "High",
                                            "type": "power",
                                            "key": "label"
                                        })
                                        sensors_found = True
                                        if not IS_PRODUCTION:
                                            print(
                                                f"[DEBUG] Found Combined Power: {combined_value_w} W")
                                except (ValueError, IndexError):
                                    continue

                            # Parse CPU cluster information (in processor usage section)
                            elif current_section == 'processor usage':
                                # Individual CPU core frequencies (CPU 0-7)
                                if line_lower.startswith('cpu ') and 'frequency:' in line_lower:
                                    try:
                                        cpu_num = line_stripped.split()[1]
                                        freq_match = line_stripped.split(
                                            'frequency:')[-1].strip()
                                        if 'MHz' in freq_match:
                                            freq_value = float(
                                                freq_match.replace('MHz', '').strip())
                                            temperature_sensors.append({
                                                "label": f"CPU {cpu_num} Frequency",
                                                "value": freq_value,
                                                "unit": "MHz",
                                                "status": "High" if freq_value > 2000 else "Normal",
                                                "type": "frequency",
                                                "key": "label"
                                            })
                                            sensors_found = True
                                            if not IS_PRODUCTION:
                                                print(
                                                    f"[DEBUG] Found CPU {cpu_num} Frequency: {freq_value} MHz")
                                    except (ValueError, IndexError):
                                        continue

                            # Parse Thermal pressure (in thermal pressure section)
                            elif current_section == 'thermal pressure' and 'current pressure level:' in line_lower:
                                try:
                                    pressure_match = line_stripped.split(
                                        'Current pressure level:')[-1].strip()
                                    if not IS_PRODUCTION:
                                        print(
                                            f"[DEBUG] Thermal pressure level: {pressure_match}")

                                    # Convert pressure level to estimated temperature
                                    pressure_to_temp = {
                                        'Nominal': 45.0,
                                        'Fair': 65.0,
                                        'Serious': 80.0,
                                        'Critical': 95.0
                                    }

                                    estimated_temp = pressure_to_temp.get(
                                        pressure_match, 50.0)
                                    temperature_sensors.append({
                                        "label": "CPU Temperature",
                                        "value": estimated_temp,
                                        "unit": "°C",
                                        "status": pressure_match,
                                        "type": "temperature",
                                        "key": "label"
                                    })
                                    sensors_found = True
                                except (ValueError, IndexError):
                                    continue

                            # Parse GPU metrics (in GPU usage section)
                            elif current_section == 'gpu usage':
                                if 'gpu hw active frequency:' in line_lower:
                                    try:
                                        freq_match = line_stripped.split(
                                            'GPU HW active frequency:')[-1].strip()
                                        if 'MHz' in freq_match:
                                            freq_value = float(
                                                freq_match.replace('MHz', '').strip())
                                            temperature_sensors.append({
                                                "label": "GPU Frequency",
                                                "value": freq_value,
                                                "unit": "MHz",
                                                "status": "Active" if freq_value > 400 else "Idle",
                                                "type": "frequency",
                                                "key": "label"
                                            })
                                            sensors_found = True
                                            if not IS_PRODUCTION:
                                                print(
                                                    f"[DEBUG] Found GPU Frequency: {freq_value} MHz")
                                    except (ValueError, IndexError):
                                        continue

                        if not sensors_found and not IS_PRODUCTION:
                            print(
                                "[DEBUG] No temperature data found in powermetrics output")
                    else:
                        if not IS_PRODUCTION:
                            print(
                                f"[DEBUG] powermetrics failed with return code {process.returncode}")

                except subprocess.TimeoutExpired:
                    if not IS_PRODUCTION:
                        print("[DEBUG] powermetrics command timed out")
                except FileNotFoundError:
                    if not IS_PRODUCTION:
                        print("[DEBUG] powermetrics command not found")
                except Exception as e:
                    if not IS_PRODUCTION:
                        print(
                            f"[DEBUG] Unexpected error with powermetrics: {e}")
            else:
                if not IS_PRODUCTION:
                    print(
                        "[DEBUG] No system password provided for macOS temperature reading")
        elif system == 'windows':
            try:
                # Try wmic for CPU temperature
                result = subprocess.run(['wmic', '/namespace:\\\\root\\wmi', 'PATH', 'MSAcpi_ThermalZoneTemperature',
                                         'get', 'CurrentTemperature'], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.isdigit():
                            try:
                                # Convert from tenths of Kelvin to Celsius
                                temp_kelvin = int(line) / 10.0
                                temp_celsius = temp_kelvin - 273.15
                                temperature_sensors.append({
                                    "label": "CPU Temperature",
                                    "value": round(temp_celsius, 1),
                                    "unit": "°C",
                                    "status": "Normal" if temp_celsius < 80 else "Hot",
                                    "type": "temperature",
                                    "key": "label"
                                })
                                break
                            except ValueError:
                                continue
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

    except Exception as e:
        # If all methods fail, add a placeholder
        pass

    # If no temperature data found, add a placeholder
    if not temperature_sensors:
        temperature_sensors.append({
            "label": "CPU Temperature",
            "value": None,
            "unit": "°C",
            "status": "Unavailable",
            "type": "temperature",
            "key": "label"
        })

    return temperature_sensors


def get_client_ips():
    """Get both external and local IP addresses"""
    external_ip = None
    local_ip = None

    # Get external IP from service
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        if response.status_code == 200:
            external_ip = response.text.strip()
    except:
        pass

    # Get local IP using platform-specific commands
    try:
        import platform
        system = platform.system().lower()

        if system == 'windows':
            # Use ipconfig on Windows
            result = subprocess.run(
                ['ipconfig'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'IPv4 Address' in line or 'IP Address' in line:
                        # Extract IP from lines like "   IPv4 Address. . . . . . . . . . . : 192.168.1.100"
                        if ':' in line:
                            ip = line.split(':')[-1].strip()
                            if ip and ip != '127.0.0.1' and not ip.startswith('169.254'):
                                local_ip = ip
                                break
        else:
            # Use ifconfig on Linux/macOS
            result = subprocess.run(
                ['ifconfig'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'inet ' in line and '127.0.0.1' not in line and 'inet 169.254' not in line:
                        # Extract IP address from line like "inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255"
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            local_ip = parts[1]
                            break
    except:
        local_ip = "127.0.0.1"

    return external_ip, local_ip


def send_to_webhook(data, webhook_url=None, api_secret=None, environment=None, system_password=None):
    """Send data to webhook endpoint"""
    # Use command line arguments or environment variables
    env = environment or os.getenv('ENV', 'development')

    if not webhook_url:
        # Use environment-based URL selection
        # Development: Use proxy through web service (port 3009)
        # Production: Use direct API access (port 8009)
        if env.lower() == 'production':
            webhook_url = os.getenv('GLANCES_WEBHOOK_URL_PROD')
        else:
            webhook_url = os.getenv('GLANCES_WEBHOOK_URL_DEV')

    secret = api_secret or os.getenv('GLANCES_SECRET')

    headers = {
        'Content-Type': 'application/json',
        'X-Secret': secret
    }
    if not webhook_url or not secret:
        print("❌ Webhook URL or API key not configured")
        return None, "Webhook URL or API key not configured"

    # Add client IPs to the data
    external_ip, local_ip = get_client_ips()
    data['external_ip'] = external_ip
    data['local_ip'] = local_ip

    # Add temperature data to sensors
    temperature_data = get_temperature_data(system_password)
    if 'sensors' not in data:
        data['sensors'] = []

    # Append temperature sensors to existing sensors
    data['sensors'].extend(temperature_data)

    try:
        response = requests.post(
            webhook_url, json=data, headers=headers, timeout=10)
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return None, str(e)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Send real Glances data to webhook endpoint')
    parser.add_argument('--webhook-url', '-u', type=str,
                        help='Webhook URL (overrides environment variable)')
    parser.add_argument('--api-secret', '-s', type=str,
                        help='API secret key (overrides environment variable)')
    parser.add_argument('--environment', '-e', type=str, choices=[
                        'development', 'production'], help='Environment (development/production)')
    parser.add_argument('--interval', '-i', type=int, default=5,
                        help='Interval between sends in seconds (default: 5)')
    parser.add_argument('--system-password', type=str,
                        help='System password for sudo operations (macOS only)')
    return parser.parse_args()


def main():
    args = parse_arguments()

    print("🚀 Starting Real Glances Data Sender")
    print("📊 Collecting and sending real system metrics...")
    if args.webhook_url:
        print(f"🔗 Using webhook URL: {args.webhook_url}")
    if args.environment:
        print(f"🌍 Environment: {args.environment}")
    if args.interval:
        print(f"⏱️ Interval: {args.interval} seconds")
    print("Press Ctrl+C to stop\n")

    interval = args.interval

    try:
        while True:
            # Get real system data
            glances_data = get_real_glances_data()

            if glances_data:
                # Send to webhook
                status_code, response = send_to_webhook(
                    glances_data,
                    webhook_url=args.webhook_url,
                    api_secret=args.api_secret,
                    environment=args.environment,
                    system_password=args.system_password
                )

                timestamp = datetime.now().strftime('%H:%M:%S')

                if status_code == 200:
                    # Extract key metrics for display
                    cpu_percent = glances_data.get(
                        'cpu', {}).get('total', 'N/A')
                    mem_percent = glances_data.get(
                        'mem', {}).get('percent', 'N/A')
                    hostname = glances_data.get(
                        'system', {}).get('hostname', 'unknown')

                    print(f"✅ [{timestamp}] Data sent successfully")
                    print(
                        f"   Host: {hostname} | CPU: {cpu_percent}% | Memory: {mem_percent}%")

                    if isinstance(response, dict) and 'snapshot_id' in response:
                        print(f"   Snapshot ID: {response['snapshot_id']}")
                else:
                    print(
                        f"❌ [{timestamp}] Failed to send data: {status_code} - {response}")
            else:
                print(
                    f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Failed to get Glances data")

            print()  # Empty line for readability
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
