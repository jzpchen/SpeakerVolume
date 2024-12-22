"""
This is a setup.py script generated for your macOS application.
"""
import os
import sys
from setuptools import setup
import py2app
import glob

# Get the pyssc package directory
import pyssc
pyssc_dir = os.path.dirname(pyssc.__file__)
pyssc_files = []
for root, dirs, files in os.walk(pyssc_dir):
    for file in files:
        if file.endswith('.py'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, pyssc_dir)
            dest_dir = os.path.join('pyssc', os.path.dirname(rel_path))
            pyssc_files.append((dest_dir, [full_path]))

APP = ['speaker_control.py']
DATA_FILES = [
    'icon.png',
    'Speaker.icns'
]

OPTIONS = {
    'argv_emulation': False,
    'packages': [
        'PyQt6',
        'zeroconf',
        'netifaces',
        'ifaddr',
        'async_timeout',
        'pyssc',
        'asyncio',
        'logging',
        'typing',
        'importlib'
    ],
    'includes': [
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'zeroconf._exceptions',
        'json',
        'time',
        'argparse',
        'subprocess',
        'os',
        'sys',
        'logging',
        'traceback',
        'asyncio.base_events',
        'asyncio.coroutines',
        'asyncio.events',
        'asyncio.exceptions',
        'asyncio.futures',
        'asyncio.locks',
        'asyncio.protocols',
        'asyncio.queues',
        'asyncio.runners',
        'asyncio.streams',
        'asyncio.subprocess',
        'asyncio.tasks',
        'asyncio.transports',
        'asyncio.unix_events',
        'importlib._bootstrap',
        'importlib._bootstrap_external',
        'importlib.machinery',
        'importlib.util'
    ],
    'excludes': ['tkinter'],
    'iconfile': 'Speaker.icns',
    'plist': {
        'CFBundleName': 'Speaker Control',
        'CFBundleDisplayName': 'Speaker Control',
        'CFBundleGetInfoString': "Control Neumann speakers",
        'CFBundleIdentifier': "com.jzpchen.speakercontrol",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': u"Copyright 2024, Jeff Chen, All Rights Reserved",
        'NSHighResolutionCapable': True,
        'LSEnvironment': {
            'DYLD_LIBRARY_PATH': '@executable_path/../Frameworks'
        }
    },
    'site_packages': True,  # Include site-packages
    'strip': False,  # Don't strip debug and local symbols
    'optimize': 0,  # Don't optimize the bytecode
    'semi_standalone': True,  # Use the system Python framework
}

setup(
    name='Speaker Control',
    app=APP,
    data_files=DATA_FILES + pyssc_files,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
