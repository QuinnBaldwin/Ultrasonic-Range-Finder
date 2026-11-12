"""
Ultrasonic range finder (HC-SR04 style sensor) on a Raspberry Pi.

Sends a 10 microsecond trigger pulse, times the returning echo pulse,
converts the time of flight into a distance, and repeats the measurement
to report the mean distance and its standard deviation.

Wiring (BCM numbering):
    TRIG -> GPIO 17
    ECHO -> GPIO 27 (use a voltage divider: the sensor outputs 5 V, the Pi expects 3.3 V)
"""

import time
import statistics

import RPi.GPIO as GPIO

TRIG = 17
ECHO = 27

SPEED_OF_SOUND = 34300   # cm/s in air at ~20 °C
START_TIMEOUT = 1.0      # s to wait for the echo pulse to begin
PULSE_TIMEOUT = 0.05     # s maximum echo pulse length (beyond sensor range)


def setup():
    """Configure the GPIO pins and let the sensor settle."""
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    GPIO.output(TRIG, False)
    time.sleep(0.3)


def reading():
    """Take a single distance reading in cm, or return None if it timed out."""
    # Send a 10 microsecond trigger pulse
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    # Wait for the echo pulse to start
    wait_start = time.time()
    pulse_start = wait_start
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start - wait_start > START_TIMEOUT:
            return None

    # Time how long the echo pulse lasts
    pulse_end = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end - pulse_start > PULSE_TIMEOUT:
            return None

    time_of_flight = pulse_end - pulse_start
    # Sound travels to the object and back, so halve the distance
    return time_of_flight * SPEED_OF_SOUND / 2


def take_readings(n=20, gap=0.1):
    """Take n readings, gap seconds apart.

    Returns (values, n_failed, mean, std). mean and std are None if there
    were too few successful readings to calculate them.
    """
    values = []
    n_failed = 0
    for _ in range(n):
        d = reading()
        if d is None:
            n_failed += 1
        else:
            values.append(d)
        time.sleep(gap)

    mean = statistics.mean(values) if values else None
    std = statistics.stdev(values) if len(values) > 1 else None
    return values, n_failed, mean, std


if __name__ == "__main__":
    try:
        setup()
        values, n_failed, mean, std = take_readings(n=20, gap=0.1)
        print(f"Successful readings: {len(values)}, failed: {n_failed}")
        if mean is not None:
            if std is not None:
                print(f"Distance: {mean:.2f} ± {std:.2f} cm")
            else:
                print(f"Distance: {mean:.2f} cm (single reading)")
    finally:
        GPIO.cleanup()
