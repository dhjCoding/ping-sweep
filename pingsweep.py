"""
ping_sweep.py

A concurrent IPv4 ping sweep tool designed for network discovery.

This module provides functionality to scan a given IPv4 network range
(in CIDR notation) for active hosts by sending ICMP echo requests (pings).
It leverages Python's 'subprocess' for executing native ping commands
and 'concurrent.futures' for efficient, parallel scanning.
"""

import ipaddress
import subprocess
import platform
import concurrent.futures
from typing import List, Dict, Union, Optional

def _ping_host(host_ip: str, timeout_seconds: int = 1, count: int = 1) -> Dict[str, Union[str, bool]]:
    """
    Internal helper function to ping a single host and determine reachability.

    Args:
        host_ip (str): The IP address of the host to ping.
        timeout_seconds (int): The maximum time in seconds to wait for a reply.
        count (int): The number of ICMP echo requests to send.

    Returns:
        Dict[str, Union[str, bool]]: A dictionary containing:
            - 'ip': The IP address that was pinged.
            - 'reachable': True if the host replied, False otherwise.
            - 'error': Optional error message if an exception occurred.
    """
    # Determine the correct ping command based on the operating system
    system = platform.system()
    command: List[str] = []

    if system == "Windows":
        # -n: number of echo requests, -w: timeout in milliseconds
        command = ["ping", "-n", str(count), "-w", str(timeout_seconds * 1000), host_ip]
    elif system in ["Linux", "Darwin"]:  # Darwin is macOS
        # -c: number of echo requests, -W: timeout in seconds
        command = ["ping", "-c", str(count), "-W", str(timeout_seconds), host_ip]
    else:
        return {'ip': host_ip, 'reachable': False, 'error': f"Unsupported OS: {system}"}

    try:
        # Execute the ping command
        # capture_output=True captures stdout and stderr
        # text=True decodes output as text
        # check=False prevents subprocess.run from raising CalledProcessError for non-zero exit codes
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Check the return code. 0 typically means success.
        # On Windows, sometimes ping can return 0 even if no reply, but its stdout is more reliable.
        # On Linux/macOS, 0 means success.
        if result.returncode == 0:
            # Look for common success indicators in stdout.
            # "reply from" for Windows, "bytes from" for Linux/macOS
            if "reply from" in result.stdout.lower() or "bytes from" in result.stdout.lower():
                return {'ip': host_ip, 'reachable': True}
        
        # If return code is not 0 or success indicator not found
        return {'ip': host_ip, 'reachable': False}

    except FileNotFoundError:
        return {'ip': host_ip, 'reachable': False, 'error': "Ping command not found. Is it in your system's PATH?"}
    except Exception as e:
        return {'ip': host_ip, 'reachable': False, 'error': f"An unexpected error occurred: {e}"}


def ping_sweep(network_cidr: str, timeout_seconds: int = 1, max_workers: int = 20) -> List[str]:
    """
    Performs a concurrent ping sweep on the specified IPv4 network range.

    Args:
        network_cidr (str): The IPv4 network range in CIDR notation (e.g., "192.168.1.0/24").
        timeout_seconds (int): The timeout for each ping request in seconds.
                               Defaults to 1 second.
        max_workers (int): The maximum number of threads to use for concurrent pings.
                           Defaults to 20. Adjust based on system resources and network size.

    Returns:
        List[str]: A list of reachable IP addresses within the given network range.

    Raises:
        TypeError: If 'network_cidr' is not a string.
        ValueError: If 'network_cidr' is not a valid IPv4 network.
    """
    if not isinstance(network_cidr, str):
        raise TypeError("Input 'network_cidr' must be a string.")

    try:
        network = ipaddress.ip_network(network_cidr, strict=False)
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("Provided network is not a valid IPv4 network.")
    except ValueError as e:
        raise ValueError(f"Invalid IPv4 network format or CIDR: {e}")

    reachable_hosts: List[str] = []
    print(f"Starting ping sweep on network: {network_cidr} ({network.num_addresses} IPs)...")

    # Use ThreadPoolExecutor for concurrent pinging
    # Threads are suitable here because pings are I/O-bound operations (waiting for network responses)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Map _ping_host to all host IPs in the network
        # network.hosts() yields only usable host IPs (excludes network and broadcast)
        # If you want to include network and broadcast, iterate network.iter_hosts() or network.num_addresses
        future_to_ip = {executor.submit(_ping_host, str(ip), timeout_seconds): str(ip) for ip in network.hosts()}

        for future in concurrent.futures.as_completed(future_to_ip):
            host_ip = future_to_ip[future]
            try:
                result = future.result()
                if result['reachable']:
                    reachable_hosts.append(result['ip'])
                    print(f"  [+] {result['ip']} is ONLINE")
                # else:
                #     print(f"  [-] {result['ip']} is OFFLINE") # Optional: print offline hosts too
                # if result.get('error'):
                #     print(f"  [!] Error pinging {result['ip']}: {result['error']}")

            except Exception as exc:
                print(f"  [!] {host_ip} generated an exception: {exc}")

    reachable_hosts.sort(key=ipaddress.IPv4Address) # Sort results numerically
    print(f"\nPing sweep complete. Found {len(reachable_hosts)} reachable host(s).")
    return reachable_hosts

# --- Example Usage ---
if __name__ == "__main__":
    print("--- IPv4 Ping Sweep Tool ---")
    print("This section demonstrates the functionality of the ping_sweep function.\n")

    # --- Test Cases ---
    test_networks = [
        # Valid test cases
        ("127.0.0.0/24", True),  # Localhost network (should find 127.0.0.1)
        ("192.168.1.0/24", True), # Common home network (adjust if your network is different)
        # Add more real-world test cases for your environment if possible
        # e.g., an actual small subnet you control

        # Invalid test cases (expected to raise ValueError)
        ("192.168.1.0/33", False),       # Invalid CIDR prefix
        ("256.0.0.0/24", False),         # Invalid IP address
        ("192.168.1/24", False),         # Malformed IP
        ("invalid-network", False),      # Non-IP string
        ("192.168.1.0", False),          # Missing CIDR
    ]

    for network_str, expect_success in test_networks:
        print(f"\n===== Attempting to sweep: '{network_str}' =====")
        try:
            # Use a slightly longer timeout for robust testing
            online_hosts = ping_sweep(network_str, timeout_seconds=1, max_workers=20)
            if expect_success:
                print(f"Successfully swept '{network_str}'. Reachable hosts: {online_hosts}")
            else:
                print(f"Unexpected success for '{network_str}'. Reachable hosts: {online_hosts}")
                print("--- Expected failure, but succeeded! ---")
        except (TypeError, ValueError) as e:
            if not expect_success:
                print(f"Correctly caught expected error for '{network_str}': {e}")
            else:
                print(f"FAIL: Unexpected error for '{network_str}': {e}")
        except Exception as e:
            print(f"FAIL: An unexpected general error occurred for '{network_str}': {e}")
        print("=" * 40)

    print("\n--- Additional Type Error Tests (Non-string inputs) ---")
    non_string_inputs = [
        None,
        12345,
        ["192.168.1.0/24"],
    ]
    for invalid_input in non_string_inputs:
        try:
            print(f"\n===== Testing non-string input: '{invalid_input}' (Type: {type(invalid_input).__name__}) =====")
            ping_sweep(invalid_input)
            print(f"FAIL: Did not raise TypeError for '{invalid_input}'")
        except TypeError as e:
            print(f"PASS: Correctly raised TypeError for '{invalid_input}': {e}")
        except Exception as e:
            print(f"FAIL: Raised unexpected error for '{invalid_input}': {e}")
