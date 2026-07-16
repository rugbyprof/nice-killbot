```sh
esptool --port /dev/cu.usbserial-0001 flash-id
```

```sh
esptool --chip esp32 --port /dev/cu.usbserial-0001 erase-flash
```

```sh
esptool \
--chip esp32 \
--port /dev/cu.usbserial-0001 \
--baud 460800 write-flash \
-z 0x1000 \
./firmware/ESP32_GENERIC-20260406-v1.28.0.bin
```

```sh
mpremote connect /dev/cu.usbserial-0001 repl
```

```sh
mpremote connect /dev/cu.usbserial-0001 fs cp main.py :main.py
```

```sh
mpremote connect /dev/cu.usbserial-0001 run main.py
```
