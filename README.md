# SSC Speaker Control

A simple GUI application to control Sennheiser SSC speakers.

## Features

- Real-time level display
- Increment/decrement volume by 1dB steps
- Safety limits (0-90 dB)
- Automatic device discovery
- Multi-speaker synchronization

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the GUI application:
```bash
cd pyssc
python speaker_control.py
```

The application will:
1. Automatically discover SSC devices on your network
2. Display the current level
3. Allow adjustment via + and - buttons
4. Keep all speakers synchronized

## Requirements

- Python 3.9+
- PyQt6
- Network interface with SSC speakers (default: en0)
