# PREMONITOR Deployment Checklist

## Pre-Deployment Setup

### 1. Hardware Setup
- [ ] Raspberry Pi 4 (4GB RAM) ready with Raspbian/Ubuntu installed
- [ ] Thermal camera(s) connected (I2C addresses configured)
- [ ] USB microphone(s) connected (hw:1,0, hw:2,0, etc.)
- [ ] Gas sensors connected to GPIO pins
- [ ] Temperature sensors (DS18B20) connected and configured
- [ ] All sensors tested individually

### 2. Software Dependencies
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python dependencies
pip3 install -r requirements.txt

# Verify TFLite runtime installation
python3 -c "import tflite_runtime.interpreter as tflite; print('TFLite OK')"

# Optional: Install additional alerting libraries
pip3 install requests  # For Discord webhooks
pip3 install twilio    # For SMS alerts (optional)
```

### 3. Directory Structure
- [ ] Create required directories:
```bash
cd /home/pi/PREMONITOR
mkdir -p logs captures models
```

- [ ] Copy TFLite models to `/home/pi/PREMONITOR/models/`:
  - [ ] `thermal_anomaly_model_int8.tflite`
  - [ ] `acoustic_anomaly_model_int8.tflite`
  - [ ] `lstm_autoencoder_model.tflite`

### 4. Configuration

#### Environment Variables
Create `/home/pi/.premonitor_env`:
```bash
export EMAIL_SENDER_ADDRESS="your_email@gmail.com"
export EMAIL_SENDER_PASSWORD="your_app_password"
export DEFAULT_EMAIL_RECIPIENT="alert_recipient@example.com"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK"
export PREMONITOR_LOG_LEVEL="INFO"
export PREMONITOR_DEBUG="false"
```

Load environment:
```bash
source /home/pi/.premonitor_env
```

- [ ] Email credentials configured
- [ ] Discord webhook configured (optional)
- [ ] SMS credentials configured (optional)

#### Device Configuration
- [ ] Copy and edit `device_config.json.example` to `device_config.json`
- [ ] Update equipment IDs, sensor addresses, and thresholds

### 5. Equipment Registry
- [ ] Edit `pythonsoftware/equipment_registry.py`
- [ ] Configure all monitored equipment
- [ ] Set correct sensor addresses (I2C, GPIO, USB)
- [ ] Configure alert channels per equipment
- [ ] Mark critical equipment appropriately

---

## Deployment Steps

### Step 1: Validate Configuration
```bash
cd /home/pi/PREMONITOR
python3 -c "import sys; sys.path.insert(0, 'pythonsoftware'); import config; print('Config OK')"
```

- [ ] No configuration errors
- [ ] All paths resolved correctly
- [ ] Model files found

### Step 2: Run Tests
```bash
python3 tests/run_all_tests.py
```

- [ ] All import tests pass
- [ ] Equipment registry tests pass
- [ ] Dataset tests pass (or warnings acknowledged)

### Step 3: Test Hardware Connections
```bash
# Test mock hardware
cd pythonsoftware
python3 mock_hardware.py
```

- [ ] Mock hardware initializes successfully
- [ ] Thermal data returns correct shape
- [ ] Audio data returns correct shape
- [ ] Temperature sensor returns values

### Step 4: Test Alert Channels
```bash
# Test email alerts (if configured)
python3 pythonsoftware/alert_manager.py

# Test Discord webhook (if configured)
python3 -c "
import sys
sys.path.insert(0, 'pythonsoftware')
from alert_manager import send_discord_alert
send_discord_alert('PREMONITOR Test Alert from Raspberry Pi')
"
```

- [ ] Email alerts working
- [ ] Discord alerts working
- [ ] SMS alerts working (if configured)

### Step 5: Dry Run Monitoring
```bash
# Run main script for 5 minutes
timeout 300 python3 pythonsoftware/premonitor_main_multi_equipment.py
```

- [ ] Script starts without errors
- [ ] Models load successfully
- [ ] Sensors read successfully
- [ ] No memory/CPU limit violations
- [ ] Logs created in `logs/premonitor_main.log`

### Step 6: Check Resource Usage
```bash
# Monitor resources while running
top -p $(pgrep -f premonitor_main)
```

Expected resource usage:
- [ ] RAM: 75-115 MB
- [ ] CPU: 1-5% average
- [ ] No memory leaks over 30+ minutes

---

## Production Deployment

### Setup Systemd Service
Create `/etc/systemd/system/premonitor.service`:
```ini
[Unit]
Description=PREMONITOR Predictive Maintenance System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PREMONITOR
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/home/pi/.premonitor_env
ExecStart=/usr/bin/python3 /home/pi/PREMONITOR/pythonsoftware/premonitor_main_multi_equipment.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable premonitor.service
sudo systemctl start premonitor.service
```

- [ ] Service file created
- [ ] Service enabled
- [ ] Service started successfully
- [ ] Service runs after reboot

### Verify Service Status
```bash
sudo systemctl status premonitor.service
sudo journalctl -u premonitor.service -f
```

- [ ] Service status: `active (running)`
- [ ] No errors in logs
- [ ] Monitoring loop running

---

## Post-Deployment Monitoring

### Week 1: Close Monitoring
- [ ] Check logs daily: `tail -f logs/premonitor_main.log`
- [ ] Monitor resource usage
- [ ] Verify alerts trigger correctly
- [ ] Check for false positives

### Ongoing Maintenance
- [ ] Weekly log review
- [ ] Monthly sensor calibration check
- [ ] Quarterly model performance review
- [ ] Update equipment registry as needed

### Log Rotation Setup
Create `/etc/logrotate.d/premonitor`:
```
/home/pi/PREMONITOR/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644 pi pi
}
```

- [ ] Log rotation configured

---

## Troubleshooting

### Common Issues

#### Models not found
```bash
# Check model paths
ls -lh /home/pi/PREMONITOR/models/
# Expected: 3 .tflite files (15-30 MB each)
```

#### Import errors
```bash
# Ensure pythonsoftware in path
cd /home/pi/PREMONITOR
export PYTHONPATH="${PYTHONPATH}:$(pwd)/pythonsoftware"
```

#### Sensor read failures
- Check I2C devices: `i2cdetect -y 1`
- Check USB audio: `arecord -l`
- Check GPIO permissions: `groups pi` (should include `gpio`)

#### High memory usage
- Check for memory leaks: Monitor RSS over time
- Reduce sensor read frequency (increase `SENSOR_READ_INTERVAL`)
- Disable DEBUG_MODE

#### Alerts not sending
- Verify environment variables loaded: `env | grep PREMONITOR`
- Check network connectivity
- Test alert channels individually
- Review alert_manager logs

---

## Rollback Procedure

If deployment fails:
```bash
# Stop service
sudo systemctl stop premonitor.service
sudo systemctl disable premonitor.service

# Review logs
tail -100 logs/premonitor_main.log

# Fix issues and retry deployment steps
```

---

## Success Criteria

- [ ] System runs for 24+ hours without crashes
- [ ] Resource usage within limits (75-115 MB RAM, <5% CPU)
- [ ] Alerts trigger and send successfully
- [ ] No false positives in first week
- [ ] All critical equipment monitored
- [ ] Logs rotating properly
- [ ] Service survives reboot

---

## Documentation

- [ ] Equipment registry documented
- [ ] Sensor calibration values recorded
- [ ] Alert escalation procedures documented
- [ ] Maintenance schedule created
- [ ] Team trained on alert responses

---

**Deployment Date:** _______________
**Deployed By:** _______________
**Sign-Off:** _______________
