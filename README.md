# SSC Speaker Control

A simple GUI application to control Sennheiser SSC speakers with a clean, modern interface.

## Features

- Real-time level display with dB readings
- Precise volume control with 0.1dB resolution
- Elegant circular +/- buttons for easy adjustment
- Safety limits (0-90 dB)
- Non-blocking speaker discovery
- Real-time status updates
- Multi-speaker synchronization
- Compact window design

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the GUI application:
```bash
cd SpeakerControl
python speaker_control.py [--interface INTERFACE]
```

For example:
```bash
python speaker_control.py              # Uses default interface (en0)
python speaker_control.py -i en1       # Uses en1 interface
```

The application will:
1. Start immediately with a responsive interface
2. Show scanning status while discovering speakers
3. Automatically connect when speakers are found
4. Display the current level in dB
5. Allow precise adjustment via + and - buttons
6. Keep all speakers synchronized
7. Update readings every 2 seconds

## Requirements

- Python 3.9+
- PyQt6 ≥ 6.8.0
- zeroconf ≥ 0.131.0
- pyssc ≥ 0.0.2.dev7
- Network interface with SSC speakers (default: en0)

## Files

- `speaker_control.py`: Main GUI application
- `scan_devices.py`: Standalone speaker discovery utility
- `requirements.txt`: Python package dependencies
- `README.md`: This documentation file
