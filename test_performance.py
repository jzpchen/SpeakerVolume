#!/usr/bin/env python3
import time
import logging
from pyssc.scan import scan
from pyssc.ssc_device_setup import Ssc_device_setup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scan_performance(num_trials=3):
    total_time = 0
    successful_scans = 0
    
    for i in range(num_trials):
        logger.info(f"\nTrial {i+1}/{num_trials}")
        start_time = time.time()
        
        try:
            # Perform scan
            logger.info("Starting scan...")
            setup = scan(scan_time_seconds=0.5)
            
            if setup and hasattr(setup, 'ssc_devices'):
                num_devices = len(setup.ssc_devices)
                logger.info(f"Found {num_devices} devices")
                for j, device in enumerate(setup.ssc_devices):
                    logger.info(f"Device {j+1}: IP={device.ip}, Port={device.port}")
                
                if num_devices > 0:
                    successful_scans += 1
            
            scan_time = time.time() - start_time
            total_time += scan_time
            logger.info(f"Scan completed in {scan_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during scan: {str(e)}")
        
        # Wait a bit between trials
        if i < num_trials - 1:
            time.sleep(1)
    
    avg_time = total_time / num_trials if num_trials > 0 else 0
    success_rate = (successful_scans / num_trials) * 100 if num_trials > 0 else 0
    
    logger.info(f"\nPerformance Summary:")
    logger.info(f"Average scan time: {avg_time:.2f} seconds")
    logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info(f"Successful scans: {successful_scans}/{num_trials}")

if __name__ == "__main__":
    test_scan_performance()
