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



# Loop forever checking timers, setting status LEDs, and operating the relays
SLEEP_BETWEEN_STATUS_CHECKS_SEC = 0.25
class StatusThread(threading.Thread):
  def run(self):
    debug(DEBUG_STATUS, "StatusThread is starting...")
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

      time.sleep(SLEEP_BETWEEN_STATUS_CHECKS_SEC)
    debug(DEBUG_STATUS, "StatusThread has ended.")



# Loop forever watching the buttons, and adjusting cool and warm timer globals
SLEEP_BETWEEN_BUTTON_CHECKS_SEC = 0.5
class ButtonThread(threading.Thread):

  # Helper function for modifications the *_off_time variables
  @classmethod
  def new_off_time(cls, off_time, delta):
    debug(DEBUG_BUTTONS, "--> new_off_time(%0.2f) [%0.2f]" % (delta, off_time - time.time()))
    if off_time < time.time():
      if delta > 0:
        off_time = time.time() + delta
    else:
      if delta > 0:
        off_time += delta
      elif delta < 0 and off_time + delta <= time.time():
        off_time = time.time() - 1
      else:
        off_time += delta
    # Enforce the timer maximum
    now = time.time()
    max = now + (TIME_MAX_IN_MINUTES * 60.0)
    if off_time > max:
      off_time = max
    debug(DEBUG_BUTTONS, "<-- new_off_time(%0.2f) [%0.2f]" % (delta, off_time - time.time()))
    return off_time

  def run(self):
    global cool_off_time
    global warm_off_time
    debug(DEBUG_BUTTONS, "ButtonThread is starting...")
    while keep_running:
      if GPIO.event_detected(MY_BUTTON_COOL_MORE):
        debug(DEBUG_BUTTONS, "COOL MORE")
        warm_off_time = time.time() - 1
        cool_off_time = ButtonThread.new_off_time(cool_off_time, TIME_QUANTUM_IN_MINUTES * 60.0)
      if GPIO.event_detected(MY_BUTTON_COOL_LESS):
        debug(DEBUG_BUTTONS, "COOL LESS")
        cool_off_time = ButtonThread.new_off_time(cool_off_time, - TIME_QUANTUM_IN_MINUTES * 60.0)
      if GPIO.event_detected(MY_BUTTON_WARM_MORE):
        debug(DEBUG_BUTTONS, "WARM MORE")
        cool_off_time = time.time() - 1
        warm_off_time = ButtonThread.new_off_time(warm_off_time, TIME_QUANTUM_IN_MINUTES * 60.0)
      if GPIO.event_detected(MY_BUTTON_WARM_LESS):
        debug(DEBUG_BUTTONS, "WARM LESS")
        warm_off_time = ButtonThread.new_off_time(warm_off_time, - TIME_QUANTUM_IN_MINUTES * 60.0)
      time.sleep(SLEEP_BETWEEN_BUTTON_CHECKS_SEC)
    debug(DEBUG_BUTTONS, "ButtonThread has ended.")



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
cool_off_time = time.time() - 1
warm_off_time = time.time() - 1
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

    GPIO.add_event_detect(MY_BUTTON_COOL_MORE, GPIO.RISING)
    GPIO.add_event_detect(MY_BUTTON_COOL_LESS, GPIO.RISING)
    GPIO.add_event_detect(MY_BUTTON_WARM_MORE, GPIO.RISING)
    GPIO.add_event_detect(MY_BUTTON_WARM_LESS, GPIO.RISING)

    global cool_off_time
    global warm_off_time
    global keep_running
    keep_running = True

    # Monitor timers, set LEDS, and control the relays
    status = StatusThread()
    status.start()

    # Monitor the button objects, and set the *_off_time globals as needed
    buttons = ButtonThread()
    buttons.start()

    while keep_running:
      time.sleep(2)

  except KeyboardInterrupt:
    cleanup()

if __name__ == '__main__':
  main()

