# SENSOR MODULES

## Student Handout

Using, mounting, and logging data from four common robotics sensors

| Goal: Connect each sensor safely, mount it so it measures the intended quantity, and record data that can be checked and analyzed later. |
| :---- |

### **Quick comparison**

| Module | Measures | Interface | Typical range/rate | Mounting priority |
| :---- | :---- | :---- | :---- | :---- |
| VL53L0X | Distance | I²C | Up to \~2 m; 10–30 Hz | Clean, direct optical path |
| GP2Y0A02YK0F | Distance | Analog | 20–150 cm; 10–25 Hz | Broad target; perpendicular aim |
| NEO-6M | Position/time | UART | Usually 1 Hz | Antenna faces open sky |
| GY-521 / MPU-6050 | Motion | I²C | 50–200 Hz | Rigid, axis-aligned mounting |

### **Before you begin**

* Confirm the voltage requirements of your exact breakout board—not only the underlying sensor chip.  
* Connect all module and microcontroller grounds together. Do not allow motor current to return through thin sensor-ground wiring.  
* Record units, sample rate, sensor settings, and mounting orientation with every dataset.  
* Power down before changing wiring. Check polarity before reconnecting power.

## **1\. VL53L0X Time-of-Flight Distance Sensor**

*Digital laser ranging for obstacle, clearance, and level measurements*

**What it does:** Emits invisible 940 nm light and measures its return time. It reports absolute distance over I²C, with useful range up to about 2 m under suitable conditions.

### **Connect and use**

* Connect VIN, GND, SDA, and SCL according to the breakout-board labels.  
* Initialize a VL53L0X library, then select single-shot or continuous ranging.  
* Read distance in millimetres and retain the timeout or range-status value.

### **Mounting**

* Keep a completely unobstructed line of sight. Enclosure edges and screws must remain outside the field of view.  
* Point the sensor perpendicular to the target when possible. For ground clearance, point straight down. An angled sensor reports slant distance, not vertical height.  
* Keep the optical window clean, rigid, and free of condensation.  
* For a protective window, use thin, flat, low-haze material that transmits 940 nm IR; keep it close and parallel to the sensor. Calibrate for optical crosstalk.

### **Avoiding interference**

* Strong sunlight can reduce usable range. Shade the optical path when practical.  
* If several ToF sensors view the same area, aim them apart or read them sequentially.  
* Keep I²C wiring short and away from motor, PWM, and high-current battery wiring.  
* Use local decoupling and a clean regulated supply.

### **Log these fields**

| timestamp\_ms,distance\_mm,status1250,438,valid |
| :---- |

| Good practice: Log invalid readings explicitly. A blank or zero can otherwise be mistaken for a real distance. |
| :---- |

## **2\. GP2Y0A02YK0F Infrared Distance Sensor**

*Analog triangulation sensor for approximately 20–150 cm*

**What it does:** Produces an analog voltage related nonlinearly to distance. Target reflectivity, shape, and angle can influence the result.

### **Connect and use**

* Connect VCC to the required 5 V supply, connect GND, and connect VO to an analog input.  
* Read the ADC value and convert it to voltage.  
* Convert voltage to distance using a calibration curve or interpolation table—not a simple linear equation.

### **Mounting**

* Keep both optical openings clean and unobstructed.  
* Aim approximately perpendicular to a broad, flat target. For ground measurements, start by pointing directly downward.  
* Keep enclosure walls out of the optical path; internal reflections can cause false readings.  
* Calibrate with the final mounting angle and representative target material.

### **Avoiding interference**

* Shield the sensor from direct sunlight and strong IR sources. A short matte-black hood may help if it does not block the optics.  
* Separate overlapping IR sensor views or power/read the sensors alternately.  
* Place supply decoupling close to the module; the sensor draws pulsed current.  
* Route VO beside a ground conductor and away from motor-driver outputs, switching regulators, and PWM wires. Average several ADC samples.

### **Calibrate and log**

**Calibration:** At several known distances, collect multiple voltage readings from a representative target. Average each group and create a curve or lookup table.

| timestamp\_ms,adc\_raw,voltage\_V,distance\_cm1250,392,1.264,53.8 |
| :---- |

| Keep the raw data: Raw ADC values allow the distance conversion to be improved later without repeating the experiment. |
| :---- |

## **3\. NEO-6M GPS Module**

*Satellite-based position, altitude, speed, and UTC time*

**What it does:** Receives very weak satellite signals and commonly outputs NMEA messages over UART serial.

### **Connect and use**

* Connect module TX to the microcontroller serial RX. Connect RX only when configuration commands are needed.  
* Power the exact breakout according to its specification. A common hobby-board UART default is 9600 baud.  
* Use a GPS/NMEA parsing library and wait for a valid fix before accepting coordinates.

### **Mounting**

* Give the antenna the clearest possible view of the sky. Metal, buildings, and indoor roofs reduce reception.  
* Mount a ceramic patch antenna with its broad active face pointing upward.  
* Do not place a battery, metal plate, carbon-fibre panel, or circuit board above the antenna.  
* Secure the antenna and cable. Keep antenna leads short and avoid sharp bends.

### **Avoiding interference**

* Separate the antenna and receiver from motors, switching regulators, motor drivers, high-current wiring, fast digital electronics, and radio transmitters.  
* Do not route antenna or UART wiring parallel to motor and battery cables.  
* Twist motor leads, minimize high-current loop area, and suppress brushed-motor noise.  
* If fixes disappear when motors start, test with a separate clean supply; then consider additional filtering, shielding, or ferrites.

### **Log these fields**

| utc\_time,latitude\_deg,longitude\_deg,altitude\_m,speed\_mps,satellites,hdop,fix\_valid14:32:18,-33.856784,151.215297,42.6,0.18,8,1.12,true |
| :---- |

| Quality check: Retain satellite count, HDOP, and fix-valid status. Coordinates without quality information are difficult to trust. |
| :---- |

## **4\. GY-521 / MPU-6050 IMU**

*Three-axis gyroscope plus three-axis accelerometer*

**What it does:** Measures angular velocity, linear acceleration, and sensor temperature over I²C. It does not contain a magnetometer.

### **Connect and use**

* Connect VCC, GND, SDA, and SCL according to the breakout-board requirements.  
* Select gyro and accelerometer ranges appropriate to the expected motion.  
* At startup, hold the finished assembly still and average samples to estimate gyro zero offsets.  
* Use sensor fusion when estimating orientation; integrated gyro angle drifts over time.

### **Mounting**

* Mount the board rigidly to the object being measured and document how its X, Y, and Z axes align with the vehicle.  
* Place it near the centre of rotation when measuring overall attitude.  
* The board need not be horizontal if software accounts for a known fixed angle.  
* Avoid loose mounts and flexible panels. Use carefully chosen isolation only when high-frequency vibration requires it.

### **Avoiding interference**

* Magnetic fields do not directly corrupt this IMU because it has no magnetometer; motor vibration and electrical noise still can.  
* Balance rotating parts and separate the IMU from motors, gearboxes, and propellers.  
* Keep I²C wiring short and away from motor-driver and high-current conductors.  
* Use local decoupling and a clean supply. Apply the built-in digital low-pass filter or software filtering without adding excessive delay.

### **Log these fields**

| timestamp\_us,gx\_dps,gy\_dps,gz\_dps,ax\_g,ay\_g,az\_g,temp\_C1250000,-0.31,1.42,0.08,0.012,-0.018,0.997,24.8 |
| :---- |

| Timing matters: Use microsecond timestamps for motion work and record the selected ranges, filter settings, and sample rate. |
| :---- |

## **Setup and Data-Logging Checklist**

*Complete this check before collecting your final dataset*

* ☐ Sensor power and logic voltage confirmed  
* ☐ Common ground connected without sharing the motor-current return path  
* ☐ Sensor mounted rigidly and optical/antenna path unobstructed  
* ☐ Sensor axes or viewing direction documented  
* ☐ Motor and battery wiring separated from sensor wiring  
* ☐ Local decoupling installed  
* ☐ Units, sample rate, and sensor settings recorded  
* ☐ Raw values retained where possible  
* ☐ Validity or quality fields included  
* ☐ Test performed once with motors off and once with motors operating

## **Diagnosing interference**

1. Record a stationary baseline with motors and transmitters off.  
2. Turn on one noisy subsystem at a time while continuing to log.  
3. Compare noise, invalid readings, resets, GPS fix quality, and supply voltage.  
4. Move wiring or the sensor temporarily. If the problem changes, physical coupling is likely.  
5. Improve separation, grounding, decoupling, filtering, shielding, or vibration control; then repeat the same test.

## **General wiring rules**

* Cross sensor and noisy power wiring at about 90° instead of running them parallel.  
* Twist motor leads and battery supply/return pairs.  
* Use a separate regulated sensor rail when necessary, but keep controller and sensor grounds connected.  
* Log motor command, operating state, and battery voltage beside sensor data to reveal load-related errors.

## **Manufacturer References**

*Primary documentation used for specifications and installation guidance*

* **STMicroelectronics — VL53L0X overview:** https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html  
* **STMicroelectronics — VL53L0X cover-window guidelines (AN4907):** https://www.st.com/resource/en/application\_note/an4907-vl53l0x-ranging-module-cover-window-guidelines-stmicroelectronics.pdf  
* **Sharp — distance-sensor specifications:** https://global.sharp/products/device/lineup/selection/opto/haca/diagram.html  
* **Sharp — GP2Y0A/GP2Y0D application note:** https://global.sharp/products/device/lineup/data/pdf/datasheet/gp2y0a\_gp2y0d\_series\_appl\_e.pdf  
* **u-blox — NEO-6 datasheet:** https://content.u-blox.com/sites/default/files/products/documents/NEO-6\_DataSheet\_%28GPS.G6-HW-09005%29.pdf  
* **u-blox — LEA/NEO/MAX-6 hardware integration manual:** https://content.u-blox.com/sites/default/files/products/documents/LEA-NEO-MAX-6\_HIM\_%28UBX-14054794%29\_1.pdf  
* **TDK InvenSense — MPU-6000/MPU-6050 specification:** https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet.pdf