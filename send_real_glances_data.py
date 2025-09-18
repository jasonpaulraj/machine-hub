#!/usr/bin/env python3
"""
Real Glances Data Sender
Sends actual system metrics from Glances to the webhook endpoint
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime


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


def send_to_webhook(data):
    """Send data to the webhook endpoint"""
    webhook_url = 'http://localhost:3009/webhook/glances'
    headers = {
        'Content-Type': 'application/json',
        'X-Secret': 'optional_secret_for_webhook'
    }

    # Add client IPs to the data
    external_ip, local_ip = get_client_ips()
    data['external_ip'] = external_ip
    data['local_ip'] = local_ip

    try:
        response = requests.post(
            webhook_url, json=data, headers=headers, timeout=10)
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return None, str(e)


def main():
    print("🚀 Starting Real Glances Data Sender")
    print("📊 Collecting and sending real system metrics...")
    print("Press Ctrl+C to stop\n")

    interval = 5  # Send data every 5 seconds

    try:
        while True:
            # Get real system data
            glances_data = get_real_glances_data()

            if glances_data:
                # Send to webhook
                status_code, response = send_to_webhook(glances_data)

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
