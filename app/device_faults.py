FAULT_LABELS = {
    1: "motor_fault",
    2: "program_fault",
    4: "g_sensor_fault",
}


def decode_device_faults(value) -> tuple[int | None, list[str]]:
    if value is None:
        return None, []
    try:
        code = int(value)
    except (TypeError, ValueError):
        return None, []
    if code <= 0:
        return code, []

    labels = [label for bit, label in FAULT_LABELS.items() if code & bit]
    known_mask = 0
    for bit in FAULT_LABELS:
        known_mask |= bit
    unknown_bits = code & ~known_mask
    bit = 1
    while unknown_bits:
        if unknown_bits & bit:
            labels.append(f"unknown_fault_code_{bit}")
            unknown_bits &= ~bit
        bit <<= 1
    return code, labels
