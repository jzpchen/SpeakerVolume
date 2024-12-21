import sys
import time
import argparse
from pyssc.scan import scan
from pyssc.Ssc_device import Ssc_device
from pyssc.Ssc_device_setup import Ssc_device_setup
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QHBoxLayout)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
import os
import json
import zeroconf

class ScanThread(QThread):
    finished = pyqtSignal(object)
    status_update = pyqtSignal(str)
    
    def __init__(self, interface):
        super().__init__()
        self.interface = interface
        self.running = True
        
    def run(self):
        timeout = 60  # seconds
        scan_interval = 10  # seconds
        start_time = time.time()
        
        print(f"\nStarting scan with interface: {self.interface}")
        
        while self.running and (time.time() - start_time < timeout):
            try:
                print("\nAttempting scan...")
                setup = scan()  # Removed interface parameter from scan()
                if setup:
                    print(f"Scan result: setup={setup}")
                    if hasattr(setup, 'ssc_devices'):
                        print(f"Found devices: {len(setup.ssc_devices)}")
                        for i, device in enumerate(setup.ssc_devices):
                            print(f"Device {i+1}: IP={device.ip}, Port={device.port}")
                    else:
                        print("Setup has no ssc_devices attribute")
                
                if setup and setup.ssc_devices:
                    num_devices = len(setup.ssc_devices)
                    if num_devices == 2:
                        try:
                            print("\nAttempting to connect to all devices...")
                            setup.connect_all(interface=self.interface)
                            print("Successfully connected to all devices")
                            self.finished.emit(setup)
                            return
                        except Exception as e:
                            print(f"Connection error: {str(e)}")
                            self.status_update.emit(f"Retrying connection...")
                    elif num_devices == 1:
                        print("Only one speaker found, continuing search...")
                        self.status_update.emit("Found 1 speaker...")
                    time.sleep(scan_interval)
                else:
                    print("No devices found in this scan")
                    self.status_update.emit("Searching...")
                    time.sleep(scan_interval)
            except Exception as e:
                print(f"\nScan error: {str(e)}")
                print(f"Error type: {type(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                self.status_update.emit("Retrying...")
                time.sleep(scan_interval)
        
        print(f"\nScan loop ended. Time elapsed: {time.time() - start_time:.1f}s")
        print(f"Reason: {'Timeout' if time.time() - start_time >= timeout else 'Stopped'}")
        # If we get here, we've timed out or stopped
        self.finished.emit(None)
    
    def stop(self):
        print("Stopping scan thread...")
        self.running = False

class SpeakerControlWindow(QMainWindow):
    def __init__(self, interface='%en0'):
        super().__init__()
        self.interface = interface
        self.setWindowTitle("Speaker Control")
        self.setFixedSize(200, 180)  # Increased height to accommodate status label
        
        # Set up the window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setup = None
        self.init_ui()
        self.start_scanning()
    
    def init_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create level display
        self.level_label = QLabel("--")
        fixed_font = QFont("Menlo")  # macOS system monospace font
        fixed_font.setStyleHint(QFont.StyleHint.Monospace)  # Fallback to system monospace if Menlo not found
        self.level_label.setFont(fixed_font)
        self.level_label.setMinimumWidth(50)  # Ensure consistent width
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center align the text
        self.level_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            margin: 10px;
        """)
        layout.addWidget(self.level_label)
        
        # Create buttons layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create decrease button
        self.minus_button = QPushButton("-")
        self.minus_button.setFixedSize(35, 35)  
        self.minus_button.setStyleSheet("""
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
        """)
        self.minus_button.clicked.connect(self.decrease_level)
        self.minus_button.setEnabled(False)
        button_layout.addWidget(self.minus_button)
        
        # Add spacing between buttons
        button_layout.addSpacing(5)  
        
        # Create increase button
        self.plus_button = QPushButton("+")
        self.plus_button.setFixedSize(35, 35)  
        self.plus_button.setStyleSheet("""
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
        """)
        self.plus_button.clicked.connect(self.increase_level)
        self.plus_button.setEnabled(False)
        button_layout.addWidget(self.plus_button)
        
        layout.addLayout(button_layout)
        
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
        print("\nStarting speaker scan...")
        self.status_label.setText("Scanning for speakers...")
        self.scan_thread = ScanThread(self.interface)
        self.scan_thread.finished.connect(self.on_scan_complete)
        self.scan_thread.status_update.connect(self.status_label.setText)
        self.scan_thread.start()
    
    def on_scan_complete(self, setup):
        print(f"\nScan complete. Setup: {setup}")
        self.setup = setup
        if not self.setup or not self.setup.ssc_devices:
            print("No speakers found in final result")
            self.status_label.setText("No speakers found")
            return
        
        print(f"Successfully connected to {len(self.setup.ssc_devices)} speakers")
        self.status_label.setText("Connected")
        self.minus_button.setEnabled(True)
        self.plus_button.setEnabled(True)
        self.update_level()
        self.timer.start(2000)  # Update every 2000ms (2 second)
    
    def __del__(self):
        """Cleanup when window is closed"""
        if hasattr(self, 'zeroconf'):
            self.zeroconf.close()
    
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
            print(f"Error updating level: {e}")
    
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
            print(f"Error increasing level: {e}")
    
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
            print(f"Error decreasing level: {e}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if hasattr(self, 'scan_thread'):
            self.scan_thread.stop()
            self.scan_thread.wait()
        event.accept()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SSC Speaker Control GUI')
    parser.add_argument('--interface', '-i', default='en0',
                      help='Network interface to use (default: en0)')
    args = parser.parse_args()
    
    # Add % prefix if not present
    interface = f"%{args.interface}" if not args.interface.startswith('%') else args.interface
    
    app = QApplication(sys.argv[:1])  # Exclude our custom args from Qt
    window = SpeakerControlWindow(interface)
    window.show()
    sys.exit(app.exec())
