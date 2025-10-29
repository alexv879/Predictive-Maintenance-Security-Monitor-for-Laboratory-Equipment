# -*- coding: utf-8 -*-
"""
Unit tests for PREMONITOR raw sensor alerting logic.
Tests emergency thresholds for fire, gas, O2, CO2, vibration, and current.
"""

import sys
import os
import pytest
import numpy as np

# Add pythonsoftware to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pythonsoftware'))

# Mock config before importing main
class MockConfig:
    THERMAL_CRITICAL_THRESHOLD_C = 75.0
    GAS_ANALOG_THRESHOLD = 600
    DEBUG_MODE = False

sys.modules['config'] = MockConfig()

# Mock hardware
class MockHardware:
    @staticmethod
    def read_thermal_camera():
        return np.zeros((224, 224, 3))
    @staticmethod
    def read_microphone():
        return np.zeros((128, 128))
    @staticmethod
    def read_gas_sensor():
        return 300
    @staticmethod
    def read_temperature():
        return 5.0
    @staticmethod
    def read_co2_sensor():
        return 5.0
    @staticmethod
    def read_oxygen_sensor():
        return 20.9
    @staticmethod
    def read_vibration_sensor():
        return 0.2
    @staticmethod
    def read_current_sensor():
        return 2.5

sys.modules['mock_hardware'] = MockHardware()
sys.modules['hardware_drivers'] = MockHardware()

# Mock alert_manager
class MockAlertManager:
    alerts_sent = []
    @classmethod
    def send_discord_alert(cls, message):
        cls.alerts_sent.append(('discord', message))
        return True
    @classmethod
    def send_email_alert(cls, subject, message):
        cls.alerts_sent.append(('email', message))
        return True
    @classmethod
    def reset(cls):
        cls.alerts_sent = []

sys.modules['alert_manager'] = MockAlertManager()

# Now import functions to test
from premonitor_main_multi_equipment import check_raw_sensor_thresholds, calibrate_gas_sensor, build_lstm_feature_vector
import equipment_registry


class TestRawSensorAlerts:
    """Test raw sensor threshold alerting"""

    def setup_method(self):
        """Reset alert tracking before each test"""
        MockAlertManager.reset()

    def test_critical_temperature_alert(self):
        """Test fire/critical temperature detection"""
        equipment = {
            "id": "test_fridge",
            "type": "fridge",
            "name": "Test Fridge",
            "alert_channels": ["discord"]
        }

        readings = {
            "sensors": {
                "temperature": 80.0  # Above THERMAL_CRITICAL_THRESHOLD_C (75)
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 1
        alert = MockAlertManager.alerts_sent[0]
        assert alert[0] == 'discord'
        assert 'CRITICAL' in alert[1]
        assert '80' in alert[1]

    def test_gas_threshold_alert(self):
        """Test gas sensor threshold"""
        equipment = {
            "id": "test_fridge",
            "type": "fridge",
            "name": "Test Fridge",
            "alert_channels": ["discord"]
        }

        readings = {
            "sensors": {
                "gas": 650  # Above gas_analog_threshold (600)
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 1
        assert 'Gas sensor' in MockAlertManager.alerts_sent[0][1]

    def test_low_oxygen_alert(self):
        """Test low oxygen detection"""
        equipment = {
            "id": "test_fridge",
            "type": "fridge",
            "name": "Test Fridge",
            "alert_channels": ["discord"]
        }

        # Add oxygen_min to fridge thresholds
        thresholds = equipment_registry.EQUIPMENT_THRESHOLDS["fridge"]
        thresholds["oxygen_min"] = 19.5

        readings = {
            "sensors": {
                "oxygen": 18.0  # Below oxygen_min (19.5)
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 1
        assert 'oxygen' in MockAlertManager.alerts_sent[0][1].lower()

    def test_co2_out_of_range_alert(self):
        """Test CO2 range detection for incubators"""
        equipment = {
            "id": "test_incubator",
            "type": "incubator",
            "name": "Test Incubator",
            "alert_channels": ["discord"]
        }

        readings = {
            "sensors": {
                "co2": 7.0  # Outside co2_range (4.5-5.5)
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 1
        assert 'CO2' in MockAlertManager.alerts_sent[0][1]

    def test_high_vibration_alert(self):
        """Test vibration threshold for centrifuge"""
        equipment = {
            "id": "test_centrifuge",
            "type": "centrifuge",
            "name": "Test Centrifuge",
            "alert_channels": ["discord"]
        }

        readings = {
            "sensors": {
                "vibration": 0.8  # Above vibration_threshold (0.5)
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 1
        assert 'vibration' in MockAlertManager.alerts_sent[0][1].lower()
        assert 'bearing' in MockAlertManager.alerts_sent[0][1].lower()

    def test_motor_overload_alert(self):
        """Test current threshold for motor overload"""
        equipment = {
            "id": "test_centrifuge",
            "type": "centrifuge",
            "name": "Test Centrifuge",
            "alert_channels": ["discord"]
        }

        readings = {
            "sensors": {
                "current": 6.0  # Above current_threshold (5.0)
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 1
        assert 'overload' in MockAlertManager.alerts_sent[0][1].lower()

    def test_no_alert_for_normal_values(self):
        """Test that normal sensor values don't trigger alerts"""
        equipment = {
            "id": "test_fridge",
            "type": "fridge",
            "name": "Test Fridge",
            "alert_channels": ["discord"]
        }

        readings = {
            "sensors": {
                "temperature": 5.0,  # Normal fridge temp
                "gas": 250,  # Normal gas level (below threshold)
                "vibration": 0.2,  # Normal vibration
                "current": 2.5  # Normal current
            }
        }

        check_raw_sensor_thresholds(equipment, readings)

        assert len(MockAlertManager.alerts_sent) == 0


class TestGasCalibration:
    """Test gas sensor calibration helper"""

    def test_uncalibrated_conversion(self):
        """Test default 1:1 ADC to PPM mapping"""
        result = calibrate_gas_sensor(350, "MQ-2")

        assert result["adc_value"] == 350
        assert result["sensor_type"] == "MQ-2"
        assert result["calibrated"] == False
        assert result["ppm_estimate"] == 350

    def test_calibrated_conversion(self):
        """Test custom calibration"""
        calibration_params = {
            "zero_ppm_adc": 200,  # ADC value in clean air
            "sensitivity": 2.0     # 2 PPM per ADC unit
        }

        result = calibrate_gas_sensor(400, "MQ-2", calibration_params)

        assert result["adc_value"] == 400
        assert result["calibrated"] == True
        # (400 - 200) * 2.0 = 400 PPM
        assert result["ppm_estimate"] == 400.0


class TestLSTMFeatureVector:
    """Test LSTM feature vector builder"""

    def test_deterministic_feature_order(self):
        """Test that feature order is fixed"""
        readings1 = {
            "sensors": {
                "temperature": 5.0,
                "gas": 300,
                "vibration": 0.2,
                "current": 2.5
            }
        }

        readings2 = {
            "sensors": {
                "current": 2.5,  # Different order
                "gas": 300,
                "temperature": 5.0,
                "vibration": 0.2
            }
        }

        vec1 = build_lstm_feature_vector(readings1, "fridge")
        vec2 = build_lstm_feature_vector(readings2, "fridge")

        np.testing.assert_array_equal(vec1, vec2)

    def test_feature_vector_shape(self):
        """Test that feature vector has correct shape"""
        readings = {
            "sensors": {
                "temperature": 5.0,
                "gas": 300,
                "vibration": 0.2,
                "current": 2.5,
                "audio": np.ones((128, 128)),
                "thermal": np.ones((224, 224, 3))
            }
        }

        vec = build_lstm_feature_vector(readings, "fridge")

        assert vec.shape == (6,)  # temp, gas, vib, current, audio_rms, thermal_mean
        assert vec.dtype == np.float32

    def test_missing_sensors_filled_with_nan(self):
        """Test that missing sensors are replaced with NaN"""
        readings = {
            "sensors": {
                "temperature": 5.0,
                # Missing: gas, vibration, current, audio, thermal
            }
        }

        vec = build_lstm_feature_vector(readings, "fridge")

        assert vec[0] == 5.0  # temperature present
        assert np.isnan(vec[1])  # gas missing
        assert np.isnan(vec[2])  # vibration missing
        assert np.isnan(vec[3])  # current missing
        assert np.isnan(vec[4])  # audio missing
        assert np.isnan(vec[5])  # thermal missing


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
