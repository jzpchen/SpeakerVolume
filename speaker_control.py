import sys
import time
from pyssc.scan import scan
from pyssc.Ssc_device import Ssc_device
from pyssc.Ssc_device_setup import Ssc_device_setup
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QHBoxLayout)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QFont
import os
import json
import zeroconf

class SpeakerControlWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Speaker Control")
        self.setFixedSize(200, 150)
        
        # Set up the window icon
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Initialize speaker setup
        self.setup = self.scan_for_speakers()
        if not self.setup or not self.setup.ssc_devices:
            self.show_error_and_exit("No speakers found. Please ensure speakers are powered on and connected to the network.")
            return
            
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
        button_layout.addWidget(self.plus_button)
        
        layout.addLayout(button_layout)
        
        # Create timer for updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_level)
        self.timer.start(2000)  # Update every 2000ms (2 second)
        
        # Initial update
        self.update_level()
    
    def scan_for_speakers(self):
        """Scan for SSC speakers with timeout"""
        timeout = 60  # seconds
        scan_interval = 5  # seconds
        start_time = time.time()
        
        print("Scanning for SSC devices...")
        while time.time() - start_time < timeout:
            try:
                found_setup = scan()
                num_devices = len(found_setup.ssc_devices)
                
                if num_devices == 2:
                    print(f"\nFound {num_devices} devices:")
                    for device in found_setup.ssc_devices:
                        print(f"Device IP: {device.ip}")
                        print(f"Device Port: {device.port}")
                    print("\nScan completed in %f seconds" % (time.time() - start_time))
                    
                    # Try to connect to all devices
                    try:
                        found_setup.connect_all(interface='%en0')
                        print("Successfully connected to all devices")
                        return found_setup
                    except Exception as e:
                        print(f"Error connecting to devices: {str(e)}")
                        # Continue scanning if connection fails
                        time.sleep(scan_interval)
                        continue
                        
                elif num_devices == 1:
                    print("\nFound 1 speaker, looking for second speaker...")
                    time.sleep(scan_interval)
                else:
                    print("\nNo speakers found, continuing to scan...")
                    time.sleep(scan_interval)
            except zeroconf._exceptions.EventLoopBlocked as e:
                print(f"Warning: Zeroconf event loop blocked ({str(e)}), retrying...")
                time.sleep(1)  # Wait a bit before retrying
                continue
            except Exception as e:
                print(f"\nError during scan: {str(e)}")
                time.sleep(scan_interval)
                
        # If we get here, we've timed out
        if 'found_setup' in locals() and found_setup.ssc_devices:
            print("\nTimeout reached. Attempting to connect to found devices...")
            try:
                found_setup.connect_all(interface='%en0')
                print(f"Connected to {len(found_setup.ssc_devices)} device(s)")
                return found_setup
            except Exception as e:
                print(f"Error connecting to devices: {str(e)}")
                return None
        return None
    
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
                interface='%en0'
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
                interface='%en0'
            )
            current_level = float(eval(response.RX)['audio']['out']['level'])
            
            # Increase by 1dB, but don't exceed 90
            new_level = min(90, current_level + 1)
            
            # Set new level
            command = {"audio": {"out": {"level": new_level}}}
            self.setup.send_all(json.dumps(command), interface='%en0')
            
            # Update display immediately
            self.level_label.setText(f"{new_level:.1f}dB")
        except Exception as e:
            print(f"Error increasing level: {e}")
    
    def decrease_level(self):
        try:
            # Get current level
            response = self.setup.ssc_devices[0].send_ssc(
                '{"audio": {"out": {"level": null}}}',
                interface='%en0'
            )
            current_level = float(eval(response.RX)['audio']['out']['level'])
            
            # Decrease by 1dB, but don't go below 0
            new_level = max(0, current_level - 1)
            
            # Set new level
            command = {"audio": {"out": {"level": new_level}}}
            self.setup.send_all(json.dumps(command), interface='%en0')
            
            # Update display immediately
            self.level_label.setText(f"{new_level:.1f}dB")
        except Exception as e:
            print(f"Error decreasing level: {e}")
    
    def closeEvent(self, event):
        try:
            self.setup.disconnect_all()
        except:
            pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeakerControlWindow()
    window.show()
    sys.exit(app.exec())
