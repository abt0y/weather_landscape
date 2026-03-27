
class AppConfig:

    TITLE = "WebFrame"
    
    VERSION = "1.2 MAR 2025" 

    # ===== EPD Driver Selection =====
    # Specify driver module name (without .py)
    # Examples:
    #   "epaper2in9"
    #   "epaper2in9_V2"
    EPD_DRIVER = "epaper2in9"

    # Driver-specific extended configurations
    DRIVER_EXTRAS = {
        "epaper2in9_V2": {
            # Number of partial updates before one full refresh to clear ghosting
            "FULL_REFRESH_INTERVAL": 15,
            # "light" for keeping RAM/variables, "deep" for maximum power saving
            "SLEEP_MODE": "light"
        }
    }
    
    # Enable debug overlay on display (refresh count and server timestamp)
    DEBUG_OVERLAY = False

    # ===== SPI Configuration =====
    SPI_ID = 2
    SPI_BAUDRATE = 4000000
    SPI_POLARITY = 0
    SPI_PHASE = 0
    SPI_BITS = 8
    SPI_FIRSTBIT = 0

    # ===== Pin configuration =====
    PIN_CLK = 18
    PIN_DIN = 23 # MOSI
    PIN_DOUT = 19 # MISO, not used
    PIN_CS = 5
    PIN_DC = 13
    PIN_RST = 12
    PIN_BUSY = 14
    
    PIN_LED = 2
    
    # ===== Image reload control =====
    IMAGE_RELOAD_PERIOD_MS = 15*60*1000
    IMAGE_RELOAD_TIMEOUT_MS = 60*60*1000

    # ===== Display configuration =====
    SCR_WIDTH = 128
    SCR_HEIGHT = 296
    SCR_BYTES_PER_LINE = int(SCR_WIDTH/8)
    
    # ===== Network =====
    AP_SSID = '<your wifi ssid>'
    AP_PASS = '<your wifi password>'
  
    
    URL = "<url that points to the bmp image>"
    
    ERROR_RETRY_SEC = [10,30,5*60,20*60,60*60]
    ERROR_RETRY_COUNT = len(ERROR_RETRY_SEC)
    
    
    
    def print(self):
        print("***",self.TITLE,"***    Ver. ",self.VERSION)
        print("EPD Driver =", self.EPD_DRIVER)
        print("EInk ",self.SCR_WIDTH,"x",self.SCR_HEIGHT)
        print("Pin CLK =", self.PIN_CLK)
        print("Pin DIN =", self.PIN_DIN) 
        print("Pin CS =", self.PIN_CS)
        print("Pin DC =", self.PIN_DC)
        print("Pin RST =", self.PIN_RST)
        print("Pin BUSY =", self.PIN_BUSY)
        print("Pin LED =", self.PIN_LED)
        print("SSID", self.AP_SSID)
        print("PASS", self.AP_PASS)
        print("URL", self.URL)
        
        
        
    

    