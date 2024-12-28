#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/speaker_control_debug.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

try:
    import time
    import argparse
    import netifaces
    import subprocess
    import json
    from PyQt6 import QtWidgets, QtCore, QtGui
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QLabel, QPushButton, QHBoxLayout, QComboBox)
    from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QIcon, QFont
    from pyssc import tracker, ssc_device, ssc_device_setup
    from pyssc.tracker import Tracker
    from pyssc.ssc_device import Ssc_device
    from pyssc.ssc_device_setup import Ssc_device_setup
    import zeroconf._exceptions
except Exception as e:
    logger.error(f"Import error: {str(e)}")
    logger.error(traceback.format_exc())
    sys.exit(1)

class TrackerThread(QThread):
    finished = pyqtSignal(object)
    status_update = pyqtSignal(str)
    speakers_lost = pyqtSignal()  # New signal for when speakers are disconnected
    
    def __init__(self, interface):
        super().__init__()
        self.interface = interface
        self.running = True
        self.logger = logging.getLogger(__name__)
        self.tracker = tracker.Tracker()
        
    def run(self):
        def on_devices_changed(setup):
            if not self.running:
                return
                
            if not setup or not setup.ssc_devices:
                self.logger.info("No devices found")
                self.status_update.emit("Searching...")
                self.speakers_lost.emit()
                return
                
            num_devices = len(setup.ssc_devices)
            if num_devices == 2:
                try:
                    self.logger.info("Attempting to connect to all devices...")
                    # Connect all devices with the correct interface
                    setup.connect_all(interface=self.interface)
                    self.logger.info("Successfully connected to all devices")
                    self.finished.emit(setup)
                except Exception as e:
                    self.logger.error(f"Connection error: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    self.status_update.emit(f"Connection failed, retrying...")
                    self.speakers_lost.emit()
            else:
                self.logger.info(f"Found {num_devices} speaker{'s' if num_devices != 1 else ''}")
                self.status_update.emit(f"Found {num_devices} speaker{'s' if num_devices != 1 else ''}...")
                self.speakers_lost.emit()
        
        try:
            self.logger.info(f"Starting tracker with interface: {self.interface}")
            self.tracker.register_callback(on_devices_changed)
            self.tracker.start()
            
            # Keep thread running until stopped
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Tracker error: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.status_update.emit("Error occurred")
            
    def stop(self):
        self.running = False
        if hasattr(self, 'tracker'):
            self.tracker.stop()
    
def get_interface_friendly_name(interface):
    """Get friendly name for network interface on macOS"""
    try:
        # Get all network services
        result = subprocess.run(['networksetup', '-listallhardwareports'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            current_name = None
            for line in lines:
                if line.startswith('Hardware Port:'):
                    current_name = line.split(': ')[1].strip()
                elif line.startswith('Device:') and line.split(': ')[1].strip() == interface:
                    return current_name
    except Exception as e:
        logger.error(f"Error getting friendly name: {e}")
    return interface

def get_network_interfaces():
    """Get list of network interfaces that might have SSC speakers"""
    interfaces = []
    interface_names = {}  # Map of interface to friendly name
    
    for iface in netifaces.interfaces():
        # Skip loopback and non-physical interfaces
        if iface == 'lo0' or iface.startswith(('utun', 'llw', 'awdl', 'bridge')):
            continue
        
        addrs = netifaces.ifaddresses(iface)
        # Check if interface has IPv6 address and is active
        if netifaces.AF_INET6 in addrs:
            for addr in addrs[netifaces.AF_INET6]:
                # Look for self-assigned IPv6 addresses
                if addr['addr'].startswith('fe80::'):
                    friendly_name = get_interface_friendly_name(iface)
                    interface_names[friendly_name] = iface
                    interfaces.append(friendly_name)
                    break
    
    return interfaces or ['Ethernet'], interface_names or {'Ethernet': 'en0'}

class SpeakerControlWindow(QMainWindow):
    def __init__(self, interface='%en0'):
        super().__init__()
        self.interface = interface
        self.interface_names = {}  # Will store mapping of friendly names to interfaces
        self.setWindowTitle("Speaker Control")
        self.setFixedSize(240, 180)
        
        # Set up the window icon
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icon.png')
        logger.info(f"Looking for icon at: {icon_path}")
        if os.path.exists(icon_path):
            logger.info(f"Icon found, setting window icon")
            app_icon = QIcon(icon_path)
            self.setWindowIcon(app_icon)
            # Also set the application icon
            QApplication.instance().setWindowIcon(app_icon)
        else:
            logger.warning(f"Icon not found at {icon_path}")
        
        self.setup = None
        self.init_ui()
        self.start_scanning()
    
    def init_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(0)  # Remove default spacing
        layout.setContentsMargins(10, 0, 10, 5)  # Reduced bottom margin to 5px
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Create level display
        self.level_label = QLabel("--")
        fixed_font = QFont("Menlo")  
        fixed_font.setStyleHint(QFont.StyleHint.Monospace)  
        self.level_label.setFont(fixed_font)
        self.level_label.setMinimumWidth(50)  
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  
        self.level_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            margin: 10px;
        """)
        layout.addWidget(self.level_label)
        
        # Create buttons layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        
        # Button style
        button_style = """
            QPushButton {
                font-size: 30px;
                border-radius: 17px;
                color: black;
                background-color: #f0f0f0;
                border: none;
                padding: 0 0 3px 1px;
                text-align: center;
                line-height: 32px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                color: #a0a0a0;
                border-color: #e0e0e0;
            }
        """
        
        # Create decrease button
        self.minus_button = QPushButton("-")
        self.minus_button.setFixedSize(35, 35)  
        self.minus_button.setStyleSheet(button_style)
        self.minus_button.clicked.connect(self.decrease_level)
        self.minus_button.setEnabled(False)
        button_layout.addWidget(self.minus_button)
        
        # Add spacing between buttons
        button_layout.addSpacing(5)  
        
        # Create increase button
        self.plus_button = QPushButton("+")
        self.plus_button.setFixedSize(35, 35)  
        self.plus_button.setStyleSheet(button_style)
        self.plus_button.clicked.connect(self.increase_level)
        self.plus_button.setEnabled(False)
        button_layout.addWidget(self.plus_button)
        layout.addLayout(button_layout)
        
        # Add spacing between buttons and network selector
        layout.addSpacing(25)  # Increased to 25px
        
        # Create network interface selector
        network_layout = QHBoxLayout()
        network_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        network_label = QLabel("Network:")
        network_label.setStyleSheet("font-size: 10px; margin-right: 5px;")
        network_layout.addWidget(network_label)
        
        self.network_selector = QComboBox()
        self.network_selector.setStyleSheet("""
            QComboBox {
                font-size: 10px;
                padding: 2px 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: #333333;
                min-width: 80px;
            }
            QComboBox:hover {
                background-color: #e0e0e0;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #d0d0d0;
                selection-color: #333333;
                border: 1px solid #cccccc;
            }
        """)
        interfaces, self.interface_names = get_network_interfaces()
        self.network_selector.addItems(interfaces)
        # Set current interface (strip % if present)
        current_interface = self.interface.lstrip('%')
        # Find friendly name for current interface
        current_friendly_name = None
        for friendly_name, iface in self.interface_names.items():
            if iface == current_interface:
                current_friendly_name = friendly_name
                break
        if current_friendly_name:
            index = self.network_selector.findText(current_friendly_name)
            if index >= 0:
                self.network_selector.setCurrentIndex(index)
        self.network_selector.currentTextChanged.connect(self.on_network_changed)
        network_layout.addWidget(self.network_selector)
        layout.addLayout(network_layout)
        
        # Add spacing between network selector and status
        layout.addSpacing(5)  # Smaller spacing before status
        
        # Create status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            font-size: 10px;
            color: #666666;
            margin: 5px;
        """)
        layout.addWidget(self.status_label)
        
        # Create timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_level)
    
    def start_scanning(self):
        logger.info("\nStarting speaker scan...")
        self.status_label.setText("Scanning for speakers...")
        self.scan_thread = TrackerThread(self.interface)
        self.scan_thread.finished.connect(self.on_scan_complete)
        self.scan_thread.status_update.connect(self.status_label.setText)
        self.scan_thread.speakers_lost.connect(self.on_speakers_lost)  # Connect new signal
        self.scan_thread.start()
    
    def on_scan_complete(self, setup):
        logger.info(f"\nScan complete. Setup: {setup}")
        self.setup = setup
        if not self.setup or not self.setup.ssc_devices:
            logger.info("No speakers found in final result")
            self.status_label.setText("No speakers found")
            return
        
        # Ensure interface is set for each device
        for device in self.setup.ssc_devices:
            device.interface = self.interface
            
        logger.info(f"Successfully connected to {len(self.setup.ssc_devices)} speakers")
        self.status_label.setText("Connected")
        self.minus_button.setEnabled(True)
        self.plus_button.setEnabled(True)
        self.update_level()
        self.timer.start(2000)  
    
    def on_speakers_lost(self):
        """Handle when speakers are disconnected or not fully available"""
        self.setup = None  # Clear the setup
        self.minus_button.setEnabled(False)
        self.plus_button.setEnabled(False)
        self.level_label.setText("--")
        if hasattr(self, 'timer'):
            self.timer.stop()  # Stop the level update timer
    
    def on_network_changed(self, new_friendly_name):
        """Handle network interface change"""
        new_interface = self.interface_names.get(new_friendly_name, 'en0')
        logger.info(f"\nSwitching to network interface: {new_friendly_name} ({new_interface})")
        self.interface = f"%{new_interface}"
        # Stop current scan if running
        if hasattr(self, 'scan_thread'):
            self.scan_thread.stop()
            self.scan_thread.wait()
        # Reset UI state
        self.minus_button.setEnabled(False)
        self.plus_button.setEnabled(False)
        self.level_label.setText("--")
        # Start new scan
        self.start_scanning()
    
    def __del__(self):
        """Cleanup when window is closed"""
        if hasattr(self, 'scan_thread'):
            self.scan_thread.stop()
            self.scan_thread.wait()
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'setup'):
            self.setup.disconnect_all()
    
    def show_error_and_exit(self, message):
        """Show error message and exit application"""
        error_widget = QWidget()
        error_layout = QVBoxLayout()
        error_label = QLabel(message)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_layout.addWidget(error_label)
        error_widget.setLayout(error_layout)
        self.setCentralWidget(error_widget)
        self.show()
    
    def update_level(self):
        try:
            # Get level from first speaker (assuming all are synced)
            response = self.setup.ssc_devices[0].send_ssc(
                '{"audio": {"out": {"level": null}}}',
                interface=self.interface
            )
            level = float(eval(response.RX)['audio']['out']['level'])
            self.level_label.setText(f"{level:.1f}dB")
        except Exception as e:
            self.level_label.setText("Error")
            logger.error(f"Error updating level: {e}")
            # If there's an error, try to reconnect
            try:
                self.setup.connect_all(interface=self.interface)
            except Exception as reconnect_error:
                self.speakers_lost()
    
    def increase_level(self):
        try:
            # Get current level
            response = self.setup.ssc_devices[0].send_ssc(
                '{"audio": {"out": {"level": null}}}',
                interface=self.interface
            )
            current_level = float(eval(response.RX)['audio']['out']['level'])
            
            # Increase by 1dB, but don't exceed 90
            new_level = min(90, current_level + 1)
            
            # Set new level
            command = {"audio": {"out": {"level": new_level}}}
            self.setup.send_all(json.dumps(command), interface=self.interface)
            
            # Update display immediately
            self.level_label.setText(f"{new_level:.1f}dB")
        except Exception as e:
            logger.error(f"Error increasing level: {e}")
            # If there's an error, try to reconnect
            try:
                self.setup.connect_all(interface=self.interface)
            except Exception as reconnect_error:
                self.speakers_lost()
    
    def decrease_level(self):
        try:
            # Get current level
            response = self.setup.ssc_devices[0].send_ssc(
                '{"audio": {"out": {"level": null}}}',
                interface=self.interface
            )
            current_level = float(eval(response.RX)['audio']['out']['level'])
            
            # Decrease by 1dB, but don't go below 0
            new_level = max(0, current_level - 1)
            
            # Set new level
            command = {"audio": {"out": {"level": new_level}}}
            self.setup.send_all(json.dumps(command), interface=self.interface)
            
            # Update display immediately
            self.level_label.setText(f"{new_level:.1f}dB")
        except Exception as e:
            logger.error(f"Error decreasing level: {e}")
            # If there's an error, try to reconnect
            try:
                self.setup.connect_all(interface=self.interface)
            except Exception as reconnect_error:
                self.speakers_lost()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'scan_thread'):
            self.scan_thread.stop()
            self.scan_thread.wait()
        event.accept()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.expanduser('~/speaker_control_debug.log'))
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Speaker Control application")
    
    try:
        parser = argparse.ArgumentParser(description='SSC Speaker Control GUI')
        parser.add_argument('--interface', '-i', default='en0',
                          help='Network interface to use (default: en0)')
        args = parser.parse_args()
        
        logger.info("Creating QApplication")
        app = QApplication(sys.argv)
        logger.info("Creating main window")
        window = SpeakerControlWindow(interface=f"%{args.interface}")
        logger.info("Showing main window")
        window.show()
        logger.info("Entering main event loop")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
