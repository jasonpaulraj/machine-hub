import socket
import struct
import logging

logger = logging.getLogger(__name__)


def send_magic_packet(mac_address: str, ip_address: str = None, port: int = 9) -> dict:
    """
    Send a Wake-on-LAN magic packet to wake up a machine.

    Args:
        mac_address: MAC address in format 'XX:XX:XX:XX:XX:XX' or 'XX-XX-XX-XX-XX-XX'
        ip_address: Target IP address (optional, defaults to broadcast)
        port: UDP port to send to (default 9)

    Returns:
        dict: {'success': bool, 'message': str}
    """
    try:
        # Clean and validate MAC address
        original_mac = mac_address
        mac_address = mac_address.replace(':', '').replace('-', '').upper()
        if len(mac_address) != 12:
            return {
                'success': False,
                'message': f'Invalid MAC address format: {original_mac} (expected 12 hex digits, got {len(mac_address)}). Please ensure MAC address is complete (e.g., AA:BB:CC:DD:EE:FF)'
            }

        # Convert MAC address to bytes
        try:
            mac_bytes = bytes.fromhex(mac_address)
        except ValueError:
            return {
                'success': False,
                'message': f'Invalid MAC address: {mac_address}'
            }

        # Create magic packet
        # Magic packet = 6 bytes of 0xFF + 16 repetitions of MAC address
        magic_packet = b'\xFF' * 6 + mac_bytes * 16

        # Determine target address
        if ip_address:
            target_address = ip_address
        else:
            # Use broadcast address
            target_address = '255.255.255.255'

        # Send the magic packet
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Enable broadcast if using broadcast address
            if target_address == '255.255.255.255':
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            sock.sendto(magic_packet, (target_address, port))

        logger.info(
            f"Wake-on-LAN magic packet sent to {mac_address} at {target_address}:{port}")

        return {
            'success': True,
            'message': f'Wake-on-LAN packet sent to {mac_address}'
        }

    except socket.error as e:
        error_msg = f'Socket error sending Wake-on-LAN packet: {e}'
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }
    except Exception as e:
        error_msg = f'Error sending Wake-on-LAN packet: {e}'
        logger.error(error_msg)
        return {
            'success': False,
            'message': error_msg
        }


def wake_machine(machine) -> dict:
    """
    Wake up a machine using Wake-on-LAN.

    Args:
        machine: Machine model instance with mac_address and ip_address

    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not machine.mac_address:
        return {
            'success': False,
            'message': f'No MAC address configured for machine {machine.name}'
        }

    result = send_magic_packet(
        mac_address=machine.mac_address,
        ip_address=machine.ip_address
    )

    if result['success']:
        result['message'] = f'Wake-on-LAN packet sent to {machine.name} ({machine.mac_address})'

    return result
