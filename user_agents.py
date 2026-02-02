"""
Random User Agent Generator.
Provides modern browser user agents for realistic requests.

Copyright © CTDOTEAM - Đỗ Thành #1110
This module is provided AS-IS without warranties.
Use only for authorized testing purposes.
The author is NOT responsible for misuse, legal consequences, or damages.
"""

import random
from typing import List


CHROME_VERSIONS = [
    "130.0.0.0", "131.0.0.0", "132.0.0.0", "133.0.0.0", 
    "134.0.0.0", "135.0.0.0", "136.0.0.0", "137.0.0.0",
    "138.0.0.0", "139.0.0.0", "140.0.0.0", "141.0.0.0",
    "142.0.0.0", "143.0.0.0"
]

EDGE_VERSIONS = [
    "130.0.0.0", "131.0.0.0", "132.0.0.0", "133.0.0.0",
    "134.0.0.0", "135.0.0.0", "136.0.0.0", "137.0.0.0",
    "138.0.0.0", "139.0.0.0", "140.0.0.0", "141.0.0.0",
    "142.0.0.0", "143.0.0.0"
]

SAFARI_VERSIONS = ["605.1.15", "604.1", "603.3.8"]

FIREFOX_VERSIONS = [
    "120.0", "121.0", "122.0", "123.0", "124.0", "125.0",
    "126.0", "127.0", "128.0", "129.0", "130.0", "131.0"
]

OS_VARIANTS = [
    "Windows NT 10.0; Win64; x64",
    "Windows NT 11.0; Win64; x64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "Macintosh; Intel Mac OS X 11_0_0",
    "Macintosh; Intel Mac OS X 12_0_0",
    "Macintosh; Intel Mac OS X 13_0_0",
    "Macintosh; Intel Mac OS X 14_0_0",
    "X11; Linux x86_64",
    "X11; Ubuntu; Linux x86_64",
]


def generate_chrome_ua() -> str:
    """Generate a Chrome user agent."""
    os_variant = random.choice(OS_VARIANTS)
    chrome_ver = random.choice(CHROME_VERSIONS)
    return f"Mozilla/5.0 ({os_variant}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36"


def generate_edge_ua() -> str:
    """Generate an Edge user agent."""
    os_variant = random.choice(OS_VARIANTS)
    chrome_ver = random.choice(CHROME_VERSIONS)
    edge_ver = random.choice(EDGE_VERSIONS)
    return f"Mozilla/5.0 ({os_variant}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_ver} Safari/537.36 Edg/{edge_ver}"


def generate_firefox_ua() -> str:
    """Generate a Firefox user agent."""
    os_variant = random.choice(OS_VARIANTS)
    firefox_ver = random.choice(FIREFOX_VERSIONS)
    return f"Mozilla/5.0 ({os_variant}; rv:{firefox_ver}) Gecko/20100101 Firefox/{firefox_ver}"


def generate_safari_ua() -> str:
    """Generate a Safari user agent (macOS only)."""
    macos_variants = [v for v in OS_VARIANTS if "Macintosh" in v]
    os_variant = random.choice(macos_variants)
    safari_ver = random.choice(SAFARI_VERSIONS)
    return f"Mozilla/5.0 ({os_variant}) AppleWebKit/{safari_ver} (KHTML, like Gecko) Version/17.0 Safari/{safari_ver}"


UA_GENERATORS = [
    (generate_chrome_ua, 50),
    (generate_edge_ua, 25),
    (generate_firefox_ua, 15),
    (generate_safari_ua, 10),
]


def get_random_user_agent() -> str:
    """Get a random user agent string."""
    generators, weights = zip(*UA_GENERATORS)
    generator = random.choices(generators, weights=weights, k=1)[0]
    return generator()


def get_user_agent_for_stripe() -> str:
    """Get user agent formatted for Stripe payment_user_agent."""
    return get_random_user_agent()


USER_AGENT_POOL: List[str] = [get_random_user_agent() for _ in range(100)]


def get_fast_random_ua() -> str:
    """Get a user agent quickly from pre-generated pool."""
    return random.choice(USER_AGENT_POOL)
