import ipaddress
import socket
import urllib.parse
from typing import Dict, Any
import requests
from modules.tools.base import Tool

# SSRF Protection: Private and Link-Local IPv4/IPv6 networks to block
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),          # Loopback
    ipaddress.ip_network("10.0.0.0/8"),           # Private
    ipaddress.ip_network("172.16.0.0/12"),        # Private
    ipaddress.ip_network("192.168.0.0/16"),       # Private
    ipaddress.ip_network("169.254.0.0/16"),       # Link-local & Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("0.0.0.0/8"),            # Current network
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),             # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),            # IPv6 Link-Local
]


def _is_ssrf_safe_url(url: str) -> tuple[bool, str]:
    """Validate that the URL scheme and target IP are safe from SSRF exploits."""
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"Blocked scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed."
        
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing hostname in URL."
        
        if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal"):
            return False, f"Access to internal host '{hostname}' is blocked for security."

        # Resolve hostname to IP addresses
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked_net in _BLOCKED_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"Access to private/internal IP '{ip_str}' is blocked."
        return True, "OK"
    except Exception as e:
        return False, f"URL validation error: {e}"


class BrowserTool(Tool):
    name = "BrowserTool"
    description = (
        "Request HTML data from public documentation pages or web APIs safely."
    )
    risk_level = "SAFE"
    latency_weight = 1.0
    cost_weight = 0.2
    base_confidence = 0.99

    permissions = ["network"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 800

    def execute(self, params: Dict[str, Any]) -> str:
        url = params.get("url")
        if not url:
            return "Error: 'url' argument is required."

        is_safe, reason = _is_ssrf_safe_url(url)
        if not is_safe:
            return f"Blocked SSRF attempt: {reason}"

        try:
            resp = requests.get(url, timeout=10, allow_redirects=False)
            content = resp.text[:1200]
            return f"HTTP Status: {resp.status_code}\nContent Preview:\n{content}..."
        except Exception as e:
            return f"Headless connection lookup failure: {e}"
