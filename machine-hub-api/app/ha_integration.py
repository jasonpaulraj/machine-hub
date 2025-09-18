import requests
import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging
from wakeonlan import send_magic_packet

load_dotenv()

logger = logging.getLogger(__name__)

class HomeAssistantClient:
    def __init__(self):
        self.base_url = os.getenv("HOME_ASSISTANT_URL")
        self.token = os.getenv("HOME_ASSISTANT_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if Home Assistant is properly configured"""
        return bool(self.base_url and self.token)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Make a request to Home Assistant API"""
        if not self.is_configured():
            logger.warning("Home Assistant not configured")
            return None
        
        url = f"{self.base_url.rstrip('/')}/api/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return response.json() if response.content else {"success": True}
        except requests.exceptions.RequestException as e:
            logger.error(f"Home Assistant API request failed: {e}")
            return None
    
    def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get the state of a Home Assistant entity"""
        return self._make_request("GET", f"states/{entity_id}")
    
    def call_service(self, domain: str, service: str, entity_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Call a Home Assistant service"""
        data = {
            "entity_id": entity_id,
            **kwargs
        }
        return self._make_request("POST", f"services/{domain}/{service}", data)
    
    def turn_on_switch(self, entity_id: str) -> bool:
        """Turn on a switch entity"""
        result = self.call_service("switch", "turn_on", entity_id)
        return result is not None
    
    def turn_off_switch(self, entity_id: str) -> bool:
        """Turn off a switch entity"""
        result = self.call_service("switch", "turn_off", entity_id)
        return result is not None
    
    def get_switch_state(self, entity_id: str) -> Optional[str]:
        """Get the state of a switch (on/off)"""
        state_data = self.get_entity_state(entity_id)
        if state_data:
            return state_data.get("state")
        return None
    
    def is_switch_on(self, entity_id: str) -> bool:
        """Check if a switch is currently on"""
        state = self.get_switch_state(entity_id)
        return state == "on"

# Global Home Assistant client instance
ha_client = HomeAssistantClient()

def power_on_machine(machine) -> Dict[str, Any]:
    """Power on a machine using Home Assistant smart plug or Wake-on-LAN"""
    result = {"success": False, "message": "Unknown error", "method": None}
    
    # Try Home Assistant smart plug first
    if machine.ha_entity_id and ha_client.is_configured():
        try:
            success = ha_client.turn_on_switch(machine.ha_entity_id)
            if success:
                result.update({
                    "success": True,
                    "message": f"Successfully turned on smart plug for {machine.name}",
                    "method": "home_assistant"
                })
                return result
            else:
                result["message"] = "Failed to turn on smart plug via Home Assistant"
        except Exception as e:
            logger.error(f"Home Assistant power on failed: {e}")
            result["message"] = f"Home Assistant error: {str(e)}"
    
    # Fallback to Wake-on-LAN if MAC address is available
    if machine.mac_address:
        try:
            send_magic_packet(machine.mac_address)
            result.update({
                "success": True,
                "message": f"Wake-on-LAN packet sent to {machine.name} ({machine.mac_address})",
                "method": "wake_on_lan"
            })
            return result
        except Exception as e:
            logger.error(f"Wake-on-LAN failed: {e}")
            result["message"] = f"Wake-on-LAN error: {str(e)}"
    
    # No method available
    if not machine.ha_entity_id and not machine.mac_address:
        result["message"] = "No power control method configured (no HA entity or MAC address)"
    
    return result

def power_off_machine(machine) -> Dict[str, Any]:
    """Power off a machine using Home Assistant smart plug"""
    result = {"success": False, "message": "Unknown error", "method": None}
    
    # Only Home Assistant smart plug can power off
    if machine.ha_entity_id and ha_client.is_configured():
        try:
            success = ha_client.turn_off_switch(machine.ha_entity_id)
            if success:
                result.update({
                    "success": True,
                    "message": f"Successfully turned off smart plug for {machine.name}",
                    "method": "home_assistant"
                })
            else:
                result["message"] = "Failed to turn off smart plug via Home Assistant"
        except Exception as e:
            logger.error(f"Home Assistant power off failed: {e}")
            result["message"] = f"Home Assistant error: {str(e)}"
    else:
        result["message"] = "No Home Assistant entity configured for power off"
    
    return result

def get_machine_power_state(machine) -> Dict[str, Any]:
    """Get the current power state of a machine via Home Assistant"""
    result = {"success": False, "state": "unknown", "message": "Unknown error"}
    
    if machine.ha_entity_id and ha_client.is_configured():
        try:
            state = ha_client.get_switch_state(machine.ha_entity_id)
            if state:
                result.update({
                    "success": True,
                    "state": state,
                    "message": f"Smart plug state for {machine.name}: {state}"
                })
            else:
                result["message"] = "Failed to get smart plug state from Home Assistant"
        except Exception as e:
            logger.error(f"Home Assistant state check failed: {e}")
            result["message"] = f"Home Assistant error: {str(e)}"
    else:
        result["message"] = "No Home Assistant entity configured"
    
    return result