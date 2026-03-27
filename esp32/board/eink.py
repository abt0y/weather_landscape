from machine import Pin, SPI
import machine
import time
from screenbuffer import Screen
from imagecomparer import ImageComparer




class EInk:
    def __init__(self,appcfg):
        self.cfg = appcfg
        spi = SPI(  appcfg.SPI_ID,
                    baudrate=appcfg.SPI_BAUDRATE,
                    polarity=appcfg.SPI_POLARITY,
                    phase=appcfg.SPI_PHASE,
                    bits=appcfg.SPI_BITS,
                    firstbit=appcfg.SPI_FIRSTBIT,
                    sck=Pin(appcfg.PIN_CLK),
                    mosi=Pin(appcfg.PIN_DIN),
                    miso=Pin(appcfg.PIN_DOUT))
        
        cs = Pin(appcfg.PIN_CS,Pin.OUT)
        dc = Pin(appcfg.PIN_DC,Pin.OUT)
        rst = Pin(appcfg.PIN_RST,Pin.OUT)
        busy = Pin(appcfg.PIN_BUSY,Pin.IN)

        # Dynamic EPD Driver Loading
        try:
            module = __import__(self.cfg.EPD_DRIVER)
            EPD = getattr(module, "EPD")
        except Exception as e:
            raise RuntimeError("Failed to load EPD driver: " + str(e))
        
        try:
            self.dev = EPD(spi, cs, dc, rst, busy, self.cfg) # V2 Style
        except TypeError:
            self.dev = EPD(spi, cs, dc, rst, busy) # V1 Style fallback
            
        self.dev.init()
        print("EInk init")

        # Get driver generation (Default to 1 if not specified)
        self.gen = getattr(self.dev, 'GENERATION', 1)

        self.scr = Screen(appcfg)
        self.cmp = ImageComparer()
        
        # State management for partial updates
        self.old_data = None
        self.sleep_mode = self.cfg.DRIVER_EXTRAS.get(self.cfg.EPD_DRIVER, {}).get("SLEEP_MODE", "deep")
        
    def clear(self):
        self.scr.clear()        
        
    def update(self,isforceupdate=False):
        self.show(self.scr.data,isforceupdate)
        
    def show(self, data, isforceupdate=False, update_time="") -> bool: 
        """
        Displays image data. Handles V1/V2 driver differences automatically.
        """
        # Change detection
        isthesame = self.cmp.check(data)
        if (isthesame) and (not isforceupdate):
            print("EInk update skipped: No changes detected")
            return False

        if self.gen >= 2:
            print("Using V2 strategy (Unified refresh)")
            
            # Overlay debug info onto the current screen buffer
            self.dev.update_time = update_time
            self.scr.scrbuf = bytearray(data)
            
            # Draw debug info (refresh count and server timestamp) onto screen buffer
            if self.cfg.DEBUG_OVERLAY and hasattr(self.dev, 'draw_debug_overlay'):
                self.dev.draw_debug_overlay(self.scr)
            
            # Use the buffer that now contains both image and debug text
            current_frame = self.scr.data
            
            # Determine refresh mode based on data availability
            needs_full = (isforceupdate or (self.old_data is None))

            # Wake up the panel
            self.dev.init() 

            # Refresh Control Logic
            if needs_full:
                # Ensure the driver performs a clean, full refresh
                self.dev.refresh_count = 0

            # Execute Display Update
            self.dev.display_frame(current_frame, self.old_data)
            self.old_data = bytearray(current_frame)
            
        else:
            # Generation 1 Strategy (Legacy)
            print("Using V1 strategy (Split-method refresh)")
            self.dev.set_frame_memory(data, 0, 0, self.cfg.SCR_WIDTH, self.cfg.SCR_HEIGHT)
            self.dev.display_frame()
            self.old_data = None

        return True
        
    def print(self,text):
        self.scr.print(text)
             
    def printat(self,text,x,y):
        self.scr.printat(text,x,y)

    def sleep_panel(self):
        if hasattr(self.dev, 'sleep'):
            try:
                self.dev.sleep()
            except Exception as e:
                print("Warning: EPD sleep failed:", e)
