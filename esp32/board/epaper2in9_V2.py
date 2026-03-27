"""
MicroPython Waveshare 2.9" Black/White GDEY029T94 e-paper display driver
https://github.com/mcauser/micropython-waveshare-epaper

MIT License
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from micropython import const
from time import sleep_ms
import ustruct

# Display resolution
EPD_WIDTH  = const(128)
EPD_HEIGHT = const(296)

# Display commands
DRIVER_OUTPUT_CONTROL                = const(0x01)
BOOSTER_SOFT_START_CONTROL           = const(0x0C)
#GATE_SCAN_START_POSITION             = const(0x0F)
DEEP_SLEEP_MODE                      = const(0x10)
DATA_ENTRY_MODE_SETTING              = const(0x11)
SW_RESET                             = const(0x12)
#TEMPERATURE_SENSOR_CONTROL           = const(0x1A)
MASTER_ACTIVATION                    = const(0x20)
DISPLAY_UPDATE_CONTROL_1             = const(0x21)
DISPLAY_UPDATE_CONTROL_2             = const(0x22)
WRITE_RAM                            = const(0x24)
WRITE_VCOM_REGISTER                  = const(0x2C)
WRITE_LUT_REGISTER                   = const(0x32)
SET_DUMMY_LINE_PERIOD                = const(0x3A)
SET_GATE_TIME                        = const(0x3B)
BORDER_WAVEFORM_CONTROL              = const(0x3C)
SET_RAM_X_ADDRESS_START_END_POSITION = const(0x44)
SET_RAM_Y_ADDRESS_START_END_POSITION = const(0x45)
SET_RAM_X_ADDRESS_COUNTER            = const(0x4E)
SET_RAM_Y_ADDRESS_COUNTER            = const(0x4F)
TERMINATE_FRAME_READ_WRITE           = const(0xFF)

BUSY = const(1)  # 1=busy, 0=idle

class EPD:
    GENERATION = 2
    def __init__(self, spi, cs, dc, rst, busy, appcfg=None):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        # Default to 1 (always full refresh) if not set
        extras = getattr(appcfg, "DRIVER_EXTRAS", {})
        v2_cfg = extras.get("epaper2in9_V2", {})
        self.full_refresh_interval = v2_cfg.get("FULL_REFRESH_INTERVAL", 1)
        self.refresh_count = 0
        self.update_time = ""
        print(f"DEBUG: Driver initialized. Full refresh every {self.full_refresh_interval} updates.")

    # Reference: https://github.com/waveshareteam/e-Paper/blob/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd/epd2in9_V2.py
    WS_20_30 = bytearray(b'\x80\x66\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x10\x66\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x80\x66\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x10\x66\x00\x00\x00\x00\x00\x00\x20\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\x08\x00\x00\x00\x00\x02\x0A\x0A\x00\x0A\x0A\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x14\x08\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x44\x44\x44\x44\x44\x44\x00\x00\x00\x22\x17\x41\x00\x32\x36')
    WF_FULL = bytearray(b'\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x60\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x60\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x19\x19\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x24\x42\x22\x22\x23\x32\x00\x00\x00\x22\x17\x41\xAE\x32\x38')
    WF_PARTIAL = bytearray(b'\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x40\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0A\x00\x00\x00\x00\x00\x01\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x22\x22\x22\x22\x22\x22\x00\x00\x00\x22\x17\x41\xB0\x32\x36\x00\x00\x00\x00\x00\x00')

    def _command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def _init_full(self):
        self.reset()
        self.wait_until_idle()
        self._command(SW_RESET)
        self.wait_until_idle()

        self._command(DRIVER_OUTPUT_CONTROL, b'\x27\x01\x00')
        self._command(DATA_ENTRY_MODE_SETTING, b'\x03')
        
        # Set Window
        self._command(SET_RAM_X_ADDRESS_START_END_POSITION, bytes([0, (self.width - 1) >> 3]))
        self._command(SET_RAM_Y_ADDRESS_START_END_POSITION, bytes([0, 0, (self.height - 1) & 0xFF, (self.height - 1) >> 8]))
        
        # Display Update Control 1
        self._command(DISPLAY_UPDATE_CONTROL_1, b'\x00\x80')
        
        # Set Cursor
        self._command(SET_RAM_X_ADDRESS_COUNTER, b'\x00')
        self._command(SET_RAM_Y_ADDRESS_COUNTER, b'\x00\x00')
        
        # Enable internal LUT and refresh
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xB1') 

        self.set_lut(self.WS_20_30)

    def _init_fast(self):
        self.reset()
        self.wait_until_idle()
        self._command(SW_RESET)
        self.wait_until_idle()

        self._command(DRIVER_OUTPUT_CONTROL, b'\x27\x01\x00')
        self._command(DATA_ENTRY_MODE_SETTING, b'\x03')
        
        self.set_memory_area(0, 0, self.width - 1, self.height - 1)
        self.set_memory_pointer(0, 0)

        self._command(BORDER_WAVEFORM_CONTROL, b'\x05')
        self._command(DISPLAY_UPDATE_CONTROL_1, b'\x00\x80')
        
        self.wait_until_idle()
        self.set_lut(self.WF_FULL)

    def _display_partial(self, image, old_image=None):
        """
        Execute partial update.
        If old_image is provided, uses 0x26 command to minimize ghosting.
        """
        # Hardware Reset (2ms sequence)
        self.rst(0)
        sleep_ms(2)
        self.rst(1)
        sleep_ms(2)
        self.wait_until_idle()
        
        # LUT and Border Configuration
        self.set_lut(self.WF_PARTIAL)
        self._command(0x37, b'\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00')
        self._command(BORDER_WAVEFORM_CONTROL, b'\x80')
        
        # Power and Clock Activation Process
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC0')
        self._command(MASTER_ACTIVATION)
        self.wait_until_idle()

        # RAM Address and Counter
        self.set_memory_area(0, 0, self.width - 1, self.height - 1)
        self.set_memory_pointer(0, 0)
        
        # 0x24: Write New Data to RAM
        self._command(WRITE_RAM, image)     
        
        # 0x26: Write Old Data to RAM (History for differential update)
        if old_image is not None:
            self._command(0x26, old_image)
            print("DEBUG: History-based update enabled (0x26)")
        
        # Execute Display Update
        self._command(DISPLAY_UPDATE_CONTROL_2, b'\x0F') 
        self._command(MASTER_ACTIVATION)
        self.wait_until_idle()

    def init(self):
        self.reset()
        self.wait_until_idle()

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def reset(self):
        self.rst(0)
        sleep_ms(200)
        self.rst(1)
        sleep_ms(200)

    def set_lut(self, lut):
        self._command(WRITE_LUT_REGISTER, lut[:153])
        self.wait_until_idle()

        self._command(0x3f, bytes([lut[153]]))
        self._command(0x03, bytes([lut[154]])) # gate voltage
        self._command(0x04, bytes([lut[155], lut[156], lut[157]])) # source voltage
        self._command(0x2c, bytes([lut[158]])) # VCOM
        self.wait_until_idle()

    # put an image in the frame memory
    def set_frame_memory(self, image, x, y, w, h):
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        x = x & 0xF8
        w = w & 0xF8

        if (x + w >= self.width):
            x_end = self.width - 1
        else:
            x_end = x + w - 1

        if (y + h >= self.height):
            y_end = self.height - 1
        else:
            y_end = y + h - 1

        self.set_memory_area(x, y, x_end, y_end)
        self.set_memory_pointer(x, y)
        self._command(WRITE_RAM, image)

    # replace the frame memory with the specified color
    def clear_frame_memory(self, color):
        print("clear_frame_memory", color)
        self.set_memory_area(0, 0, self.width - 1, self.height - 1)
        self.set_memory_pointer(0, 0)
        self._command(WRITE_RAM)
        # send the color data
        for i in range(0, self.width // 8 * self.height):
            b = bytearray([color])
            self._data(b)

    # draw the current frame memory and switch to the next memory area
    def display_frame(self, image, old_image=None):
        if self.refresh_count == 0:
            print("Action: Executing Full Refresh...")
            self._init_full()
            self.set_memory_area(0, 0, self.width - 1, self.height - 1)
            self.set_memory_pointer(0, 0)
            self._command(WRITE_RAM, image)
            self._command(DISPLAY_UPDATE_CONTROL_2, b'\xF7')
            self._command(MASTER_ACTIVATION)
            self.wait_until_idle()
            self.refresh_count = 1
        else:
            print(f"Action: Executing Partial Refresh ({self.refresh_count}/{self.full_refresh_interval})")
            self._display_partial(image, old_image)
            self.refresh_count += 1
            if self.refresh_count >= self.full_refresh_interval:
                self.refresh_count = 0

    # specify the memory area for data R/W
    def set_memory_area(self, x_start, y_start, x_end, y_end):
        self._command(SET_RAM_X_ADDRESS_START_END_POSITION)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._data(bytearray([(x_start >> 3) & 0xFF]))
        self._data(bytearray([(x_end >> 3) & 0xFF]))
        self._command(SET_RAM_Y_ADDRESS_START_END_POSITION, ustruct.pack("<HH", y_start, y_end))

    # specify the start point for data R/W
    def set_memory_pointer(self, x, y):
        self._command(SET_RAM_X_ADDRESS_COUNTER)
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self._data(bytearray([(x >> 3) & 0xFF]))
        self._command(SET_RAM_Y_ADDRESS_COUNTER, ustruct.pack("<H", y))
        self.wait_until_idle()

    # to wake call reset() or init()
    def sleep(self):
        self.wait_until_idle()
        self._command(DEEP_SLEEP_MODE, b'\x01')

    def draw_debug_overlay(self, scr):
        count_text = f"{self.refresh_count}/{self.full_refresh_interval}"
        debug_text = f"{count_text} {self.update_time}" if self.update_time else count_text
        scr.printat(debug_text, 2, 2)
