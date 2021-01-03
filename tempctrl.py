#
# Support container for my office heater/cooler controller
#
# Written by Glen Darling, April 2020.
#


import json
import os
import subprocess
import threading
import time
import datetime



# Import the GPIO library so python can work with the GPIO pins
import RPi.GPIO as GPIO



# Debug flags
DEBUG_STATUS = False
DEBUG_BUTTONS = False
DEBUG_FAN = False

# Debug print
def debug(flag, str):
  if flag:
    print(str)



# Time constants
TIME_QUANTUM_IN_MINUTES = 5
TIME_MAX_IN_MINUTES = 16
SECONDS_LED_1 = 60 * TIME_QUANTUM_IN_MINUTES
SECONDS_LED_2 = 120 * TIME_QUANTUM_IN_MINUTES



# These values need to be provided in the container environment
MY_LED_COOL_0        = int(os.environ['MY_LED_COOL_0'])
MY_LED_COOL_1        = int(os.environ['MY_LED_COOL_1'])
MY_LED_COOL_2        = int(os.environ['MY_LED_COOL_2'])
MY_RELAY_COOL        = int(os.environ['MY_RELAY_COOL'])
MY_BUTTON_COOL_MORE  = int(os.environ['MY_BUTTON_COOL_MORE'])
MY_BUTTON_COOL_LESS  = int(os.environ['MY_BUTTON_COOL_LESS'])
MY_LED_WARM_0        = int(os.environ['MY_LED_WARM_0'])
MY_LED_WARM_1        = int(os.environ['MY_LED_WARM_1'])
MY_LED_WARM_2        = int(os.environ['MY_LED_WARM_2'])
MY_RELAY_WARM        = int(os.environ['MY_RELAY_WARM'])
MY_BUTTON_WARM_MORE  = int(os.environ['MY_BUTTON_WARM_MORE'])
MY_BUTTON_WARM_LESS  = int(os.environ['MY_BUTTON_WARM_LESS'])



# Setup the GPIOs
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(MY_LED_COOL_0, GPIO.OUT)
GPIO.setup(MY_LED_COOL_1, GPIO.OUT)
GPIO.setup(MY_LED_COOL_2, GPIO.OUT)
GPIO.setup(MY_RELAY_COOL, GPIO.OUT)
GPIO.setup(MY_BUTTON_COOL_MORE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_BUTTON_COOL_LESS, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_LED_WARM_0, GPIO.OUT)
GPIO.setup(MY_LED_WARM_1, GPIO.OUT)
GPIO.setup(MY_LED_WARM_2, GPIO.OUT)
GPIO.setup(MY_RELAY_WARM, GPIO.OUT)
GPIO.setup(MY_BUTTON_WARM_MORE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(MY_BUTTON_WARM_LESS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# The relays are triggered by LOW not HIGH
RELAY_ON = GPIO.LOW
RELAY_OFF = GPIO.HIGH



# This is useful at least during development:
GPIO.setwarnings(True)



# Buttons require debouncing!
BUTTON_DEBOUNCE_TIME_MSEC = 300
BUTTON_BETWEEN_TIME_SEC = 0.3



# Helper function for modifications the *_off_time variables
def new_off_time(off_time, delta):
  debug(DEBUG_BUTTONS, "--> new_off_time(%0.2f) [%0.2f]" % (delta, off_time - time.time()))
  if off_time < time.time():
    if delta > 0:
      off_time = time.time() + delta
  else:
    if delta > 0:
      off_time += delta
    elif delta < 0 and off_time + delta <= time.time():
      off_time = time.time() - 0.01
    else:
      off_time += delta
  # Enforce the timer maximum
  now = time.time()
  max = now + (TIME_MAX_IN_MINUTES * 60.0)
  if off_time > max:
    off_time = max
  debug(DEBUG_BUTTONS, "<-- new_off_time(%0.2f) [%0.2f]" % (delta, off_time - time.time()))
  return off_time



last_button=time.time() - 0.01
def cool_more(pin):
  global cool_off_time
  global warm_off_time
  global last_button
  if time.time() > last_button + BUTTON_BETWEEN_TIME_SEC:
    debug(DEBUG_BUTTONS, "COOL MORE")
    last_button = time.time()
    warm_off_time = time.time() - 0.01
    cool_off_time = new_off_time(cool_off_time, TIME_QUANTUM_IN_MINUTES * 60.0)

def cool_less(pin):
  global cool_off_time
  global warm_off_time
  global last_button
  if time.time() > last_button + BUTTON_BETWEEN_TIME_SEC:
    debug(DEBUG_BUTTONS, "COOL LESS")
    last_button = time.time()
    warm_off_time = time.time() - 0.01
    cool_off_time = new_off_time(cool_off_time, - TIME_QUANTUM_IN_MINUTES * 60.0)

def warm_more(pin):
  global cool_off_time
  global warm_off_time
  global last_button
  if time.time() > last_button + BUTTON_BETWEEN_TIME_SEC:
    debug(DEBUG_BUTTONS, "WARM MORE")
    last_button = time.time()
    cool_off_time = time.time() - 0.01
    warm_off_time = new_off_time(warm_off_time, TIME_QUANTUM_IN_MINUTES * 60.0)

def warm_less(pin):
  global cool_off_time
  global warm_off_time
  global last_button
  if time.time() > last_button + BUTTON_BETWEEN_TIME_SEC:
    debug(DEBUG_BUTTONS, "WARM LESS")
    last_button = time.time()
    cool_off_time = time.time() - 0.01
    warm_off_time = new_off_time(warm_off_time, - TIME_QUANTUM_IN_MINUTES * 60.0)



def cleanup():
  global keep_running
  keep_running = False
  GPIO.output(MY_RELAY_COOL, RELAY_OFF)
  GPIO.output(MY_RELAY_WARM, RELAY_OFF)
  GPIO.output(MY_LED_COOL_0, GPIO.LOW)
  GPIO.output(MY_LED_COOL_1, GPIO.LOW)
  GPIO.output(MY_LED_COOL_2, GPIO.LOW)
  GPIO.output(MY_LED_WARM_0, GPIO.LOW)
  GPIO.output(MY_LED_WARM_1, GPIO.LOW)
  GPIO.output(MY_LED_WARM_2, GPIO.LOW)



# Global variables and main program
cool_off_time = time.time() - 0.01
warm_off_time = time.time() - 0.01
def main():

  try:                                                                        

    # Initialize the output (LED and relay) pins
    GPIO.output(MY_LED_COOL_0, GPIO.LOW)
    GPIO.output(MY_LED_COOL_1, GPIO.LOW)
    GPIO.output(MY_LED_COOL_2, GPIO.LOW)
    GPIO.output(MY_RELAY_COOL, RELAY_OFF)
    GPIO.output(MY_LED_WARM_0, GPIO.LOW)
    GPIO.output(MY_LED_WARM_1, GPIO.LOW)
    GPIO.output(MY_LED_WARM_2, GPIO.LOW)
    GPIO.output(MY_RELAY_WARM, RELAY_OFF)

    # Attach callback functions to each of the buttons
    GPIO.add_event_detect(MY_BUTTON_COOL_MORE, GPIO.FALLING, callback=cool_more, bouncetime=BUTTON_DEBOUNCE_TIME_MSEC)
    GPIO.add_event_detect(MY_BUTTON_COOL_LESS, GPIO.FALLING, callback=cool_less, bouncetime=BUTTON_DEBOUNCE_TIME_MSEC)
    GPIO.add_event_detect(MY_BUTTON_WARM_MORE, GPIO.FALLING, callback=warm_more, bouncetime=BUTTON_DEBOUNCE_TIME_MSEC)
    GPIO.add_event_detect(MY_BUTTON_WARM_LESS, GPIO.FALLING, callback=warm_less, bouncetime=BUTTON_DEBOUNCE_TIME_MSEC)

    
    # Loop forever to monitor timers, set LEDS, and control the relays
    global cool_off_time
    global warm_off_time
    global keep_running
    keep_running = True
    MAIN_LOOP_SLEEP_SEC = 0.5
    debug(DEBUG_STATUS, "Main loop is starting...")
    while keep_running:
      now = time.time()
      if cool_off_time > now:
        debug(DEBUG_STATUS, "FAN is ON (and COOL LED 0 is ON)")
        GPIO.output(MY_RELAY_COOL, RELAY_ON)
        GPIO.output(MY_LED_COOL_0, GPIO.HIGH)
        remaining = cool_off_time - now
        debug(DEBUG_STATUS, "COOL REMAINING = " + str(remaining))
        if remaining > SECONDS_LED_1:
          debug(DEBUG_STATUS, "COOL LED 1 is ON")
          GPIO.output(MY_LED_COOL_1, GPIO.HIGH)
        else:
          GPIO.output(MY_LED_COOL_1, GPIO.LOW)
        if remaining > SECONDS_LED_2:
          debug(DEBUG_STATUS, "COOL LED 2 is ON")
          GPIO.output(MY_LED_COOL_2, GPIO.HIGH)
        else:
          GPIO.output(MY_LED_COOL_2, GPIO.LOW)
      else:
        debug(DEBUG_STATUS, "FAN is OFF")
        GPIO.output(MY_RELAY_COOL, RELAY_OFF)
        GPIO.output(MY_LED_COOL_0, GPIO.LOW)
        GPIO.output(MY_LED_COOL_1, GPIO.LOW)
        GPIO.output(MY_LED_COOL_2, GPIO.LOW)
      if warm_off_time > now:
        debug(DEBUG_STATUS, "HEATER is ON (and WARM LED 0 is ON)")
        GPIO.output(MY_RELAY_WARM, RELAY_ON)
        GPIO.output(MY_LED_WARM_0, GPIO.HIGH)
        remaining = warm_off_time - now
        debug(DEBUG_STATUS, "WARM REMAINING = " + str(remaining))
        if remaining > SECONDS_LED_1:
          debug(DEBUG_STATUS, "WARM LED 1 is ON")
          GPIO.output(MY_LED_WARM_1, GPIO.HIGH)
        else:
          GPIO.output(MY_LED_WARM_1, GPIO.LOW)
        if remaining > SECONDS_LED_2:
          debug(DEBUG_STATUS, "WARM LED 2 is ON")
          GPIO.output(MY_LED_WARM_2, GPIO.HIGH)
        else:
          GPIO.output(MY_LED_WARM_2, GPIO.LOW)
      else:
        debug(DEBUG_STATUS, "HEATER is OFF")
        GPIO.output(MY_RELAY_WARM, RELAY_OFF)
        GPIO.output(MY_LED_WARM_0, GPIO.LOW)
        GPIO.output(MY_LED_WARM_1, GPIO.LOW)
        GPIO.output(MY_LED_WARM_2, GPIO.LOW)

      time.sleep(MAIN_LOOP_SLEEP_SEC)
    debug(DEBUG_STATUS, "Program has ended.")

  except KeyboardInterrupt:
    cleanup()

if __name__ == '__main__':
  main()

