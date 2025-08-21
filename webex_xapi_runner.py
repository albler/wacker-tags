#!/usr/bin/env python3
"""
Webex xAPI Command Runner
Executes xAPI commands on Webex devices filtered by tag
"""

import argparse
import json
import sys
from typing import List, Dict, Any
import requests
from urllib.parse import quote


class WebexXAPIRunner:
    def __init__(self, access_token: str):
        """
        Initialize the Webex xAPI Runner
        
        Args:
            access_token: Webex API access token
        """
        self.access_token = access_token
        self.base_url = "https://webexapis.com/v1"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """
        Retrieve all devices from Webex
        
        Returns:
            List of device dictionaries
        """
        url = f"{self.base_url}/devices"
        devices = []
        
        while url:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            devices.extend(data.get("items", []))
            
            # Handle pagination
            url = response.links.get("next", {}).get("url")
        
        return devices
    
    def filter_devices_by_tag(self, devices: List[Dict[str, Any]], tag: str) -> List[Dict[str, Any]]:
        """
        Filter devices by tag
        
        Args:
            devices: List of device dictionaries
            tag: Tag to filter by
            
        Returns:
            Filtered list of devices
        """
        filtered_devices = []
        
        for device in devices:
            # Check if device has tags
            tags = device.get("tags", [])
            if tag in tags:
                filtered_devices.append(device)
        
        return filtered_devices
    
    def execute_xapi_command(self, device_id: str, command: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an xAPI command on a specific device
        
        Args:
            device_id: Device ID
            command: xAPI command to execute (e.g., "SystemUnit.Boot")
            arguments: Optional command arguments
            
        Returns:
            Command execution result
        """
        # URL format: POST https://webexapis.com/v1/xapi/command/{command}
        url = f"{self.base_url}/xapi/command/{command}"
        
        payload = {
            "deviceId": device_id
        }
        
        if arguments:
            payload["arguments"] = arguments
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Command failed with status {response.status_code}",
                "details": response.text
            }
    
    def run_command_on_tagged_devices(self, tag: str, command: str, arguments: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run xAPI command on all devices matching a tag
        
        Args:
            tag: Tag to filter devices
            command: xAPI command to execute
            arguments: Optional command arguments
            
        Returns:
            Dictionary with successful and failed executions
        """
        print(f"Fetching devices...")
        devices = self.get_devices()
        
        print(f"Filtering devices with tag '{tag}'...")
        filtered_devices = self.filter_devices_by_tag(devices, tag)
        
        if not filtered_devices:
            print(f"No devices found with tag '{tag}'")
            return {"successful": [], "failed": []}
        
        print(f"Found {len(filtered_devices)} device(s) with tag '{tag}'")
        
        results = {
            "successful": [],
            "failed": []
        }
        
        for device in filtered_devices:
            device_id = device.get("id")
            device_name = device.get("displayName", "Unknown")
            
            print(f"\nExecuting command on device: {device_name} ({device_id})")
            
            try:
                result = self.execute_xapi_command(device_id, command, arguments)
                
                if "error" in result:
                    print(f"  ❌ Failed: {result['error']}")
                    results["failed"].append({
                        "device": device_name,
                        "device_id": device_id,
                        "error": result
                    })
                else:
                    print(f"  ✅ Success")
                    results["successful"].append({
                        "device": device_name,
                        "device_id": device_id,
                        "result": result
                    })
            except Exception as e:
                print(f"  ❌ Exception: {str(e)}")
                results["failed"].append({
                    "device": device_name,
                    "device_id": device_id,
                    "error": str(e)
                })
        
        return results


def parse_xapi_command(command_string: str) -> tuple:
    """
    Parse xAPI command string into command name and arguments
    
    Args:
        command_string: Command string (e.g., "Audio.Volume.Set Level:50" or "SystemUnit.Boot")
        
    Returns:
        Tuple of (command_name, arguments_dict)
    """
    # Split command and arguments by first space
    parts = command_string.split(None, 1)
    command_name = parts[0]
    
    arguments = {}
    if len(parts) > 1:
        # Parse arguments - can be key:value pairs or JSON-like format
        arg_string = parts[1].strip()
        
        # Try to parse as JSON first
        try:
            import json
            arguments = json.loads(arg_string)
        except (json.JSONDecodeError, ValueError):
            # Parse as key:value pairs
            for arg in arg_string.split():
                if ":" in arg:
                    key, value = arg.split(":", 1)
                    # Try to convert to appropriate type
                    try:
                        # Try integer
                        arguments[key] = int(value)
                    except ValueError:
                        try:
                            # Try float
                            arguments[key] = float(value)
                        except ValueError:
                            # Try boolean
                            if value.lower() in ('true', 'false'):
                                arguments[key] = value.lower() == 'true'
                            else:
                                # Keep as string
                                arguments[key] = value
    
    return command_name, arguments


def main():
    parser = argparse.ArgumentParser(
        description="Execute xAPI commands on Webex devices filtered by tag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Set volume to 50 on all devices tagged "conference-room"
  python webex_xapi_runner.py --tag conference-room --command "Audio.Volume.Set Level:50"
  
  # Boot system on devices tagged "production"
  python webex_xapi_runner.py --tag production --command "SystemUnit.Boot"
  
  # Get system unit state on devices tagged "meeting-room"
  python webex_xapi_runner.py --tag meeting-room --command "SystemUnit.State.Get"
  
  # Using environment variable for token
  export WEBEX_ACCESS_TOKEN="your-token-here"
  python webex_xapi_runner.py --tag meeting-room --command "Standby.Deactivate"
  
  # With JSON arguments
  python webex_xapi_runner.py --tag conference --command 'Audio.Volume.Set {"Level": 50}'
        """
    )
    
    parser.add_argument(
        "--tag",
        required=True,
        help="Tag to filter devices"
    )
    
    parser.add_argument(
        "--command",
        required=True,
        help='xAPI command to execute (e.g., "Audio.Volume.Set Level:50")'
    )
    
    parser.add_argument(
        "--token",
        help="Webex API access token (can also use WEBEX_ACCESS_TOKEN env variable)"
    )
    
    parser.add_argument(
        "--output",
        choices=["summary", "detailed", "json"],
        default="summary",
        help="Output format (default: summary)"
    )
    
    args = parser.parse_args()
    
    # Get access token
    import os
    access_token = args.token or os.environ.get("WEBEX_ACCESS_TOKEN")
    
    if not access_token:
        print("Error: No access token provided. Use --token or set WEBEX_ACCESS_TOKEN environment variable")
        sys.exit(1)
    
    # Parse command
    command_name, command_args = parse_xapi_command(args.command)
    
    print(f"Command: {command_name}")
    if command_args:
        print(f"Arguments: {command_args}")
    print(f"Tag filter: {args.tag}")
    print("-" * 50)
    
    # Initialize runner and execute
    runner = WebexXAPIRunner(access_token)
    
    try:
        results = runner.run_command_on_tagged_devices(
            tag=args.tag,
            command=command_name,
            arguments=command_args if command_args else None
        )
        
        # Output results
        print("\n" + "=" * 50)
        print("EXECUTION SUMMARY")
        print("=" * 50)
        
        if args.output == "json":
            print(json.dumps(results, indent=2))
        else:
            print(f"\n✅ Successful: {len(results['successful'])} device(s)")
            if args.output == "detailed" and results['successful']:
                for item in results['successful']:
                    print(f"  - {item['device']}: {json.dumps(item['result'], indent=4)}")
            
            print(f"\n❌ Failed: {len(results['failed'])} device(s)")
            if results['failed']:
                for item in results['failed']:
                    print(f"  - {item['device']}: {item['error']}")
        
        # Exit with error code if any failures
        sys.exit(1 if results['failed'] else 0)
        
    except requests.exceptions.RequestException as e:
        print(f"\nError communicating with Webex API: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()