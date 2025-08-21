# Webex xAPI Tag Runner

Execute xAPI commands on Webex devices filtered by tags.

## Features

- Filter Webex devices by tag
- Execute any xAPI command on filtered devices
- Batch operations on multiple devices
- Detailed execution reporting
- Support for command arguments

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set your Webex access token as an environment variable:

```bash
export WEBEX_ACCESS_TOKEN="your-token-here"
```

Or provide it via command line argument `--token`.

## Usage

### Basic Usage

```bash
python webex_xapi_runner.py --tag <tag-name> --command "<xAPI-command>"
```

### Examples

Set volume to 50 on all conference room devices:
```bash
python webex_xapi_runner.py --tag conference-room --command "Audio.Volume.Set Level:50"
```

Get system state on production devices:
```bash
python webex_xapi_runner.py --tag production --command "SystemUnit.State.Get"
```

Deactivate standby on meeting room devices:
```bash
python webex_xapi_runner.py --tag meeting-room --command "Standby.Deactivate"
```

### Output Formats

- `--output summary` (default): Shows count of successful/failed executions
- `--output detailed`: Shows detailed results for each device
- `--output json`: Returns raw JSON output

## Command Line Options

- `--tag`: Tag to filter devices (required)
- `--command`: xAPI command to execute (required)
- `--token`: Webex API access token (optional, can use env variable)
- `--output`: Output format - summary, detailed, or json (optional)

## Exit Codes

- `0`: All commands executed successfully
- `1`: One or more commands failed

## Requirements

- Python 3.6+
- `requests` library
- Valid Webex API access token with device management permissions