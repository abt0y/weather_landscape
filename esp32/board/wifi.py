import network
import urequests
import time
import socket
import gc

def lebytes_to_int(data):
    return int.from_bytes(data, 'little')

class WiFi:
    def __init__(self, appcfg, led):
        self.led = led
        self.cfg = appcfg
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        print("WiFi init")

    def get_ip(self):
        try:
            return self.wlan.ifconfig()[0]
        except:
            return '0.0.0.0'

    def connect(self, force_reconnect=False):
        """
        Establishes a WiFi connection.
        If force_reconnect is True, waits for the stack to fully disconnect 
        to ensure the next connection is fresh.
        """
        if not force_reconnect:
            if self.wlan.isconnected() and self.get_ip() != '0.0.0.0':
                self.led.blink(1)
                return True
        else:
            # Wait for the network stack to realize it is disconnected
            print("Ensuring clean disconnection...")
            for _ in range(10): # Max 1s wait
                if not self.wlan.isconnected():
                    break
                time.sleep_ms(100)
            
        self.led.blink()
        print(f'Connecting to {self.cfg.AP_SSID}... ', end='')
        self.wlan.connect(self.cfg.AP_SSID, self.cfg.AP_PASS)
        
        connected = False
        for retry in range(200):
            connected = self.wlan.isconnected()
            if connected:
                break
            time.sleep(0.1)
            print('.', end='')
        print()
            
        if connected:
            return self.wait_network_ready()
        else:
            print('Connection Failed.')
            self.led.flash()
            return False
    
    def wait_network_ready(self):
        """Poll until a valid IP address is assigned by DHCP"""
        print("Waiting for IP address...")
        for i in range(20):  # Max 4 seconds
            if self.wlan.isconnected():
                ip = self.get_ip()
                if ip != "0.0.0.0":
                    print("Network ready:", ip)
                    try:
                        self.wlan.config(pm=network.WLAN.PM_NONE)
                    except:
                        pass
                    # Stabilization delay
                    time.sleep_ms(500)
                    self.led.off()
                    return True
            time.sleep(0.2)
        print("Network not ready (timeout)")
        return False

    def warmup(self, url):
        """Establish routing by performing a dummy TCP connection to prevent EHOSTUNREACH"""
        try:
            temp_url = url.split("://")[-1]
            host_part = temp_url.split("/")[0]
            if ":" in host_part:
                host, port_str = host_part.split(":")
                port = int(port_str)
            else:
                host = host_part
                port = 443 if url.startswith("https") else 80
                
            print(f"Warming up connection to {host}:{port}...")
            addr = socket.getaddrinfo(host, port)[0][-1]
            s = socket.socket()
            s.settimeout(2)
            s.connect(addr)
            s.close()
            time.sleep_ms(200)
        except Exception as e:
            print(f"Warmup skipped: {e}")
            pass

    def load(self):
        max_retries = 2
        img_bytes = None
        
        for attempt in range(max_retries):
            r = None
            try:
                # Refresh logic
                force_reconnect = False
                if attempt == 0 and self.wlan.isconnected():
                    print("Refreshing connection for stable session...")
                    self.wlan.disconnect()
                    force_reconnect = True
                
                # Establish connection
                if not self.connect(force_reconnect=force_reconnect):
                    raise Exception("WiFi Connection Failed")
                
                # Pre-verify path
                self.warmup(self.cfg.URL)

                self.led.blink()
                print(f"Loading {self.cfg.URL} (Attempt {attempt+1}/{max_retries})")
                
                r = urequests.get(self.cfg.URL, headers={'accept': 'image/bmp'}, timeout=15)
                
                # Debug Overlay: Extract and format server timestamp
                formatted_date = ""
                if self.cfg.DEBUG_OVERLAY:
                    raw_date = r.headers.get('Date', '')
                    print(f"Server Date: {raw_date}")
                    if raw_date:
                        parts = raw_date.split(' ')
                        if len(parts) >= 6:
                            formatted_date = f"{parts[4][:5]}{parts[5]}"  # "21:37GMT"
                            
                img_bytes = r.content
                if (img_bytes is None) or (len(img_bytes) < 54):
                    raise Exception("Invalid image data")

                print("Image loaded successfully")
                self.led.off()
                
                # BMP Header validation
                start_pos = lebytes_to_int(img_bytes[10:14])
                # Ensure the offset is within the downloaded data
                if start_pos >= len(img_bytes):
                    raise Exception(f"Invalid BMP offset: {start_pos} / {len(img_bytes)}")
                
                width = lebytes_to_int(img_bytes[18:22])
                height = lebytes_to_int(img_bytes[22:26])
                
                if (width != self.cfg.SCR_WIDTH) or (height != self.cfg.SCR_HEIGHT):
                    raise Exception(f"Size mismatch: {width}x{height}")

                return img_bytes[start_pos:], formatted_date

            except Exception as e:
                self.led.flash()
                print(f"\nLoad failed: {e}")
                
                if attempt < max_retries - 1:
                    print("Force resetting WiFi hardware for retry...")
                    self.wlan.active(False)
                    time.sleep_ms(300)
                    self.wlan.active(True)
                else:
                    raise
            finally:
                if r:
                    r.close()
                gc.collect()