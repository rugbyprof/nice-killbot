#!/bin/bash

PORT=/dev/cu.SLAB_USBtoUART

esptool \
    --chip esp32 \
    --port "$PORT" \
    erase-flash

esptool \
    --chip esp32 \
    --port "$PORT" \
    --baud 460800 \
    write-flash \
    -z \
    0x1000 \
    firmware/ESP32_GENERIC.bin