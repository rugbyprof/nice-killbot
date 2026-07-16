START_BYTE = 0xA5
DEVICE_ID = 0x01


def calculate_checksum(start_byte, device_id, command):
    return start_byte ^ device_id ^ command


def build_packet(command):
    checksum = calculate_checksum(
        START_BYTE,
        DEVICE_ID,
        command,
    )

    return bytes(
        [
            START_BYTE,
            DEVICE_ID,
            command,
            checksum,
        ]
    )
