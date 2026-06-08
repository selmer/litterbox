from app.device_faults import decode_device_faults


def test_decode_device_faults_handles_zero_and_none():
    assert decode_device_faults(None) == (None, [])
    assert decode_device_faults(0) == (0, [])


def test_decode_device_faults_handles_known_and_combined_bits():
    assert decode_device_faults(1) == (1, ["motor_fault"])
    assert decode_device_faults(3) == (3, ["motor_fault", "program_fault"])
    assert decode_device_faults(7) == (7, ["motor_fault", "program_fault", "g_sensor_fault"])


def test_decode_device_faults_preserves_unknown_bits():
    assert decode_device_faults(8) == (8, ["unknown_fault_code_8"])
    assert decode_device_faults(9) == (9, ["motor_fault", "unknown_fault_code_8"])
