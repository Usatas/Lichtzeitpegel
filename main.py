##########################################
### This Code is for Raspberry Pi Pico ###
###      copyright 2021 balance19      ###
##########################################

import machine
import time
#import neopixel
import array, time
from machine import Pin
import rp2
import math 
 
# Configure the number of WS2812 LEDs, pins and brightness.
NUM_LEDS = 42
PIN_NUM = 18
brightness = 0.1
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE)

#class for getting Realtime from the DS3231 in different modes.
class RTC:
    #w = ["FRI","SAT","SUN","MON","TUE","WED","THU"] #if you want different names for Weekdays, feel free to add.
    w = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    
    #initialisation of RTC object. Several settings are possible but everything is optional. If you meet this standards no parameter's needed.
    def __init__(self, sda_pin=16, scl_pin=17, port=0, speed=100000, address=0x68, register=0x00):
        self.rtc_address = address      #for using different i2c address
        self.rtc_register = register    #for using different register on device. DON'T change for DS3231
        sda=machine.Pin(sda_pin)        #configure the sda pin
        scl=machine.Pin(scl_pin)        #configure the scl pin
        self.i2c=machine.I2C(port,sda=sda, scl=scl, freq=speed) #configure the i2c interface with given parameters

    #function for setting the Time
    def DS3231_SetTime(self, NowTime = b'\x00\x45\x21\x50\x16\x12\x21'):
        # NowTime has to be in format like b'\x00\x23\x12\x28\x14\x07\x21'
        # It is encoded like this           sec min hour week day month year
        # Then it's written to the DS3231
        self.i2c.writeto_mem(int(self.rtc_address), int(self.rtc_register),NowTime)

    #the DS3231 gives data in bcd format. This has to be converted to binary format.
    def bcd2bin(self, value):
        return (value or 0) - 6 * ((value or 0) >> 4)

    #add a 0 in front of numbers smaler than 10
    def pre_zero(self, value):
        pre_zero = True #change to False if you don't want a "0" in fron of numbers smaler than 10
        if pre_zero:
            if value < 10:
                value = "0"+str(value)  #from now the value is a string!
        return value

    #read the Realtime from the DS3231 with errorhandling. Several output modes can be used.
    def DS3231_ReadTime(self,mode=0):
        try:
            buffer = self.i2c.readfrom_mem(self.rtc_address,self.rtc_register,7)    #read RT from DS3231 and write to the buffer variable. It's a list with 7 entries. Every entry needs to be converted from bcd to bin.
            year = self.bcd2bin(buffer[6]) + 2000           #the year consists of 2 digits. Here 2000 years are added to get format like "2021"
            month = self.bcd2bin(buffer[5])                 #just put the month value in the month variable and convert it.
            day = self.bcd2bin(buffer[4])                   #same for the day value
            weekday = self.w[self.bcd2bin(buffer[3])]       #weekday will be converted in the weekdays name or shortform like "Sunday" or "SUN"
            #weekday = self.bcd2bin(buffer[3])              #remove comment in this line if you want a number for the weekday and comment the line before.
            hour = self.pre_zero(self.bcd2bin(buffer[2]))   #convert bcd to bin and add a "0" if necessary
            minute = self.pre_zero(self.bcd2bin(buffer[1])) #convert bcd to bin and add a "0" if necessary
            second = self.pre_zero(self.bcd2bin(buffer[0])) #convert bcd to bin and add a "0" if necessary
            if mode == 0:   #mode 0 returns a list of second, minute, ...
                #return second, minute, hour, weekday, day, month, year
                return (second, minute, hour)
            if mode == 1:   #mode 1 returns a formated string with time, weekday and date
                time_string = str(hour) + ":" + str(minute) + ":" + str(second) + "      " + str(self.bcd2bin(buffer[3])) + " " + str(day) + "." + str(month) + "." + str(year)
                return time_string
            #if you need different format, feel free to add
        except:
            return "Error: is the DS3231 not connected?"   #exception occurs in any case of error.

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()
 
def pixels_show():
    dimmer_ar = array.array("I", [0 for _ in range(NUM_LEDS)])
    for i,c in enumerate(theLEDs):
        r = int(((c >> 8) & 0xFF) * brightness)
        g = int(((c >> 16) & 0xFF) * brightness)
        b = int((c & 0xFF) * brightness)
        dimmer_ar[i] = (g<<16) + (r<<8) + b
    sm.put(dimmer_ar, 8)
    time.sleep_ms(10)
 
def pixels_set(i, color):
    theLEDs[i] = (color[1]<<16) + (color[0]<<8) + color[2]
 
def pixels_fill(color):
    for i in range(len(theLEDs)):
        pixels_set(i, color)

def led_control(second, minute, hour, color):
    # Reset aller LED
    pixels_fill(BLACK)
    #pixels_show()
    # Sekunden Einer 0-8
    for i in range (second % 10):
        pixels_set(i, color)

    # Sekunden Zehner */ 9-13
    for i in range (int(second / 10)):
        pixels_set(13 - i, color)

    pixels_set(14, RED)
    
    # Minuten Einer */ 15-23
    for i in range(minute % 10):
        pixels_set(15 + i , color)

    # Minuten Zehner */ 24-28
    for i in range (int(minute / 10)):
        pixels_set(28 - i, color)

    pixels_set(29, RED)
    # Stunden Einer */ 30-38
    for i in range (hour % 10):
        pixels_set(30 + i, color)

    # Stunden Zehner */ 39-40
    for i in range (int(hour/ 10)):
        pixels_set(40 - i, color)
        
    pixels_set(41, RED)
    pixels_show()


if __name__ == "__main__":
    #initialisation of RTC object. Several settings are possible but everything is optional. If you meet the standards (see /my_lib/RTC_DS3231.py) no parameter's needed.
    rtc = RTC()

    # It is encoded like this sec min hour week day month year
    #rtc.DS3231_SetTime(b'\x00\x03\x09\x50\x18\x12\x21')    #remove comment to set time. Do this only once otherwise time will be set everytime the code is executed.

    # Create the StateMachine with the ws2812 program, outputting on Pin(16).
    sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(PIN_NUM))
     
    # Start the StateMachine, it will wait for data on its FIFO.
    sm.active(1)
     
    # Display a pattern on the LEDs via an array of LED RGB values.
    theLEDs = array.array("I", [0 for _ in range(NUM_LEDS)])
    
    pixels_fill(WHITE)
    #led_control(int(59), int(59), int(19),WHITE)
    pixels_show()
    while True:
       # second, minute, hour, weekday, day, month, year = rtc.DS3231_ReadTime(0)  #read RTC and receive data in Mode 1 (see /my_lib/RTC_DS3231.py)
        #second, minute, hour = rtc.DS3231_ReadTime(0)  #read RTC and receive data in Mode 1 (see /my_lib/RTC_DS3231.py)
        r = rtc.DS3231_ReadTime(0)  #read RTC and receive data in Mode 1 (see /my_lib/RTC_DS3231.py)
        second = r[0]
        minute = r[1]
        hour = r[2]
        print(str(hour) + ":" + str(minute) + ":" + str(second))
        led_control(int(second), int(minute), int(hour),WHITE)
        #print(rtc.DS3231_ReadTime(1))
        time.sleep(1)

