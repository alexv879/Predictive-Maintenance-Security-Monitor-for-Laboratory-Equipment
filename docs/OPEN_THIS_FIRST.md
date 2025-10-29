# OPEN THIS FIRST — PREMONITOR Cheat Sheet

Quick, one-page guide for a demo or walkthrough. Open these files in order and follow the short demo plan below.

1) Files to open (in this order)
- `README.md` — elevator pitch and run notes
- `docs/PROJECT_DESCRIPTION_FOR_AI.md` — architecture & datasets (backup reference)
- `docs/OPEN_THIS_FIRST.md` — (this file)
- `pythonsoftware/premonitor_main_multi_equipment.py` — main monitoring loop (show flow)
- `pythonsoftware/equipment_registry.py` — example equipment entry and enabled sensors
- `pythonsoftware/premonitor_config_py.py` — runtime settings (intervals, model paths)
- `pythonsoftware/mock_hardware.py` — how sensors are simulated (for demo)
- `pythonsoftware/hardware_drivers.py` — hardware API & TODOs (what to implement)
- `pythonsoftware/alert_manager.py` — how alerts are formatted and routed
- `docs/SECURITY_FEATURES.md` — motion/tamper features (if relevant to discussion)

2) 60–90 second talking points you can use verbatim
- Problem & impact: "PREMONITOR detects thermal, acoustic and time-series anomalies to prevent sample loss and equipment failure. Runs on a single Raspberry Pi 4 (4GB)."
- Architecture: "Three lightweight edge models (thermal CNN, acoustic CNN, LSTM autoencoder) run under TFLite; a registry maps sensors to each piece of equipment; alerts go to Discord/email."
- Resource argument: "tflite_runtime + INT8 quantization keeps memory use low (<150 MB) and inference fast (<200 ms per equipment)."
- Safety: "Immediate raw-sensor checks (temp, gas, O2, CO2) trigger critical alerts before ML confirmation."
- Security: "PIR motion, tamper hooks, camera activation on motion, and per-event activity logging are included."

3) 3–5 minute demo plan (what to run, and what to show)
- Terminal: `cd D:/PREMONITOR`
- Show `pythonsoftware/premonitor_config_py.py` (SENSOR_READ_INTERVAL) and one equipment entry in `equipment_registry.py`.
- Run (mock hardware demo):
  - `python pythonsoftware/premonitor_main_multi_equipment.py`
  - Show console logs for periodic sensor reads.
  - Trigger an anomaly: either (A) edit `mock_hardware` to return high temperature/gas, or (B) let unit run until the 5% anomaly injection occurs.
  - Show resulting alert message printed and logged, and point to `alert_manager` for outgoing channels.

4) Minimal bundle to present (files to include when handing code to professor)
- `README.md`, `docs/PROJECT_DESCRIPTION_FOR_AI.md`, `docs/OPEN_THIS_FIRST.md`
- `pythonsoftware/premonitor_main_multi_equipment.py`
- `pythonsoftware/equipment_registry.py`
- `pythonsoftware/premonitor_config_py.py`
- `pythonsoftware/hardware_drivers.py` (stubs)
- `pythonsoftware/mock_hardware.py`
- `pythonsoftware/alert_manager.py`
- `tests/test_alert_logic.py` (unit tests)
- Optional: `models/*.tflite` (small sample models) or a note pointing to release artifacts

5) Quick navigation tips (where to look in the code)
- In `premonitor_main_multi_equipment.py`:
  - Top: model loading helpers
  - `read_equipment_sensors()` — how sensors are read and exceptions handled
  - `check_raw_sensor_thresholds()` — immediate non-AI checks (fire/gas/O2)
  - `monitor_equipment()` and the main loop near the bottom — scheduling and orchestration
- In `equipment_registry.py`:
  - Show a single equipment dict entry — this config drives everything
- In `hardware_drivers.py`:
  - Point out driver stubs and the LED controller API for visual status

6) FAQ (expected questions & short answers)
- Q: "Are real hardware drivers implemented?" — A: Hardware stubs exist in `hardware_drivers.py`. For demo we use `mock_hardware.py`. Place real drivers in `hardware_drivers.py` when ready.
- Q: "How to avoid false positives?" — A: Equipment-specific thresholds, sensor fusion, and unit tests reduce false alarms; we can add adaptive baselines later.
- Q: "Where are the models?" — A: `models/` contains INT8 TFLite models (or see releases). Training scripts are in `premonitor_train_models_py.py`.

7) One-line license note to tell the professor
- "This code is proprietary — Copyright (c) 2025 Alexandru Emanuel Vasile. Contact repository owner to request use or licensing. See `LICENSE` for details."

8) If you want: I can create a `presentation_bundle/` with only the minimal bundle listed above and a `RUN_DEMO.md` containing the commands and a prepared anomaly toggle. Ask "Create presentation bundle" and I'll build it now.

---
End of cheat sheet — open this file first when preparing any demo or walkthrough.
