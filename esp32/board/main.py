from appconfig import AppConfig
from wifi import WiFi
from eink import EInk
from led import Led,LedDummy
from esp32_regs import GetResetCauseText

import sys
import time
from machine import deepsleep,lightsleep,reset


def print_message(text=None):
    eink.clear()
    eink.print("*** %s *** Ver. %s" % (cfg.TITLE,cfg.VERSION))
    eink.print("EInk %ix%i" % (cfg.SCR_WIDTH,cfg.SCR_HEIGHT) )
    eink.print("SSID %s" % cfg.AP_SSID)
    eink.print("URL %s" % cfg.URL)
    if (text):
        eink.print("")
        eink.print(text)
    eink.update(True)
    led.blink()

def print_error(text):
    global error_count
    print_message("Error: %s  %i(%i)" % (text,error_count+1,cfg.ERROR_RETRY_COUNT))
    if (error_count>=cfg.ERROR_RETRY_COUNT):
        print("There are too many errors. Reset.")
        reset()
    error_sleep_sec = cfg.ERROR_RETRY_SEC[error_count]
    error_count+=1
    print("Sleep %i sec" % error_sleep_sec)
    time.sleep(error_sleep_sec)
    
def start_sleep(ms, mode):
    if mode == "light":
        lightsleep(ms)
    else:
        deepsleep(ms)

cfg = AppConfig()
#led = Led(cfg.PIN_LED)
led = LedDummy()
wlan = WiFi(cfg,led)
eink = EInk(cfg)

cfg.print()
print("------")

#print_message(GetResetCauseText())
#time.sleep(10)

error_count = 0

while (True):
    img = None
    update_time = ""
    try:
        img, update_time = wlan.load()
    except Exception as e:
        print_error(f"Image load failed: {e}")
    
    if img:
        error_count = 0
        eink.show(img, update_time=update_time)
    else:
        print("Skipping display update due to error.")
    
    sleep_ms = cfg.IMAGE_RELOAD_PERIOD_MS
    sleep_mode = eink.sleep_mode
    print("Entering system %s sleep for %i sec..." % (sleep_mode, sleep_ms / 1000))
    if hasattr(sys, 'stdout') and hasattr(sys.stdout, 'flush'):
        sys.stdout.flush()
    time.sleep_ms(100)
    start_sleep(sleep_ms, sleep_mode)