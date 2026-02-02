"""
BIN Lookup module for card information.
Fetches bank, country, and card type from BIN number.
Contains comprehensive country lists.

Copyright © CTDOTEAM - Đỗ Thành #1110
This module is provided AS-IS without warranties.
Use only for authorized testing purposes.
The author is NOT responsible for misuse or legal consequences.
"""

import aiohttp
import asyncio
from typing import Dict, Optional




async def lookup_bin_system_api(session: aiohttp.ClientSession, bin_clean: str) -> Optional[Dict]:
    """Try system-api.pro API.
    
    Returns API response directly or None if failed.
    """
    try:
        async with session.get(
            f"https://system-api.pro/bin/{bin_clean}",
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            if response.status == 200:
                data = await response.json()
                return {
                    "brand": data.get("brand"),
                    "type": data.get("type"),
                    "level": data.get("level"),
                    "bank": data.get("bank"),
                    "country_code": data.get("country"),
                    "country_name": data.get("country_name"),
                    "country_flag": data.get("country_flag"),
                    "prepaid": data.get("prepaid"),
                }
    except Exception:
        pass
    return None




async def lookup_bin_noxter(session: aiohttp.ClientSession, bin_clean: str) -> Optional[Dict]:
    """Try noxter.dev API.
    
    Returns API response directly or None if failed.
    """
    try:
        async with session.get(
            f"https://noxter.dev/gate/bin?bin={bin_clean}",
            timeout=aiohttp.ClientTimeout(total=5),
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get("status") == False:
                    return None
                
                return {
                    "brand": data.get("brand"),
                    "type": data.get("type"),
                    "level": data.get("level"),
                    "bank": data.get("bank"),
                    "country_code": data.get("country_code"),
                    "country_name": data.get("country"),
                    "country_flag": data.get("emoji"),
                    "prepaid": data.get("prepaid"),
                }
    except Exception:
        pass
    return None


def is_valid_bin_info(info: Optional[Dict]) -> bool:
    """Check if BIN info has valid data."""
    if not info:
        return False
    
    bank = info.get("bank")
    country = info.get("country_name")
    
    return bool(bank and country)


def merge_bin_info(base: Optional[Dict], fallback: Optional[Dict]) -> Optional[Dict]:
    """Merge BIN info from two API responses."""
    if not base:
        return fallback
    if not fallback:
        return base
    
    result = base.copy()
    
    for key in ["brand", "type", "level", "bank", "country_code", "country_name", "country_flag"]:
        if not result.get(key):
            result[key] = fallback.get(key)
    
    return result


_api_rotation_counter = 0

BIN_API_FUNCTIONS = [
    ("system-api", lookup_bin_system_api),
    ("noxter", lookup_bin_noxter),
]


async def lookup_bin(bin_number: str) -> Dict:
    """
    Lookup BIN information from multiple APIs with round-robin rotation.
    
    Each request starts from a different API to distribute load.
    Tries at least 2 APIs to ensure complete data (especially for 'level' field).
    If an API fails or returns incomplete data, try the next one.
    Returns None if all APIs fail or return invalid data.
    
    Args:
        bin_number: First 6-8 digits of card number
        
    Returns:
        Dict with bank, country, brand, type info, or None if lookup fails
    """
    global _api_rotation_counter
    
    bin_clean = bin_number[:6]
    num_apis = len(BIN_API_FUNCTIONS)
    
    start_index = _api_rotation_counter % num_apis
    _api_rotation_counter += 1
    
    result = None
    apis_tried = 0
    
    async with aiohttp.ClientSession() as session:
        for i in range(num_apis):
            api_index = (start_index + i) % num_apis
            api_name, api_func = BIN_API_FUNCTIONS[api_index]
            
            try:
                api_result = await api_func(session, bin_clean)
                
                if api_result:
                    apis_tried += 1
                    result = merge_bin_info(result, api_result)
                    
                    has_valid_basic = is_valid_bin_info(result)
                    has_good_level = result.get("level") and result.get("level") not in ["", None, "UNKNOWN"]
                    
                    if has_valid_basic and has_good_level and apis_tried >= 1:
                        return result
                    
                    if has_valid_basic and apis_tried >= 2:
                        return result
                        
            except Exception:
                continue
        
        return result


def finalize_bin_info(info: Dict, bin_clean: str) -> Dict:
    """Finalize BIN info - returns data from APIs or None if all fail."""
    return info if info else None


def get_default_bin_info(bin_number: str) -> Optional[Dict]:
    """Return None when lookup fails - no fallback to defaults."""
    return None


def format_bin_info(bin_info: Optional[Dict]) -> Optional[str]:
    """Format BIN info for display."""
    if not bin_info:
        return None
    
    parts = []
    if bin_info.get("brand"):
        parts.append(bin_info["brand"])
    if bin_info.get("type"):
        parts.append(bin_info["type"])
    if bin_info.get("level"):
        parts.append(bin_info["level"])
    
    return " - ".join(parts) if parts else None
