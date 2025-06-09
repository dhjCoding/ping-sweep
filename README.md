# ping-sweep# Python IPv4 Ping Sweep Tool

A fast and efficient IPv4 ping sweep tool written in Python. This utility allows you to quickly discover active hosts within a specified network range by performing concurrent ICMP echo requests (pings). It's built to be cross-platform and utilizes Python's standard library features for robust network scanning.

## 🌟 Features

* **Concurrent Scanning:** Leverages `concurrent.futures.ThreadPoolExecutor` to send pings to multiple hosts simultaneously, drastically reducing scan time for large networks.
* **Cross-Platform Compatibility:** Automatically adapts `ping` command syntax for Windows, Linux, and macOS.
* **CIDR Support:** Accepts network ranges in standard CIDR notation (e.g., `192.168.1.0/24`).
* **Robust IP/Network Handling:** Uses Python's built-in `ipaddress` module for accurate network parsing and host iteration.
* **Clear Output:** Provides real-time updates of reachable hosts and a summary at the end.
* **Error Handling:** Catches and reports invalid network inputs or issues with the `ping` command itself.
* **Configurable:** Allows setting timeout for individual pings and the number of concurrent workers.

## ⚠️ Important Considerations

* **System `ping` Utility:** This tool relies on your operating system's native `ping` command being available in your system's PATH.
* **Firewalls:** Host-based firewalls (e.g., Windows Firewall, `ufw` on Linux) or network firewalls may block ICMP traffic, leading to hosts appearing "offline" even if they are active.
* **Permissions:** While running `ping` usually doesn't require root/administrator privileges, some highly restricted environments might behave differently.

## 🚀 Installation

No special installation is needed beyond a standard Python 3 environment. All dependencies are part of Python's standard library.

Simply download the `ping_sweep.py` file and place it in your desired project directory.

## 🛠️ Usage

### 1. Import the function

```python
from ping_sweep import ping_sweep
