#from twython import Twython
import time
import random
import json
import RPi.GPIO as GPIO


###################################################################################
#
# Pins connection:
#
# Sensor A on pin 33 (BOARD)
# Sensor B on pin 35 (BOARD)
#
# ! Connect 10K ohm (or 5) from white input wire to Vcc (3.3V) for both receivers
#
##################################################################################


"""
#######
#LCD
#OUTPUTS: map GPIO to LCD lines
LCD_RS = 7 #GPIO7 = Pi pin 26
LCD_E = 8 #GPIO8 = Pi pin 24
LCD_D4 = 17 #GPIO17 = Pi pin 11
LCD_D5 = 18 #GPIO18 = Pi pin 12
LCD_D6 = 27 #GPIO21 = Pi pin 13
LCD_D7 = 22 #GPIO22 = Pi pi

OUTPUTS = [LCD_RS,LCD_E,LCD_D4,LCD_D5,LCD_D6,LCD_D7]
#INPUTS: map GPIO to Switches
SW1 = 4 #GPIO4 = Pi pin 7
SW2 = 23 #GPIO16 = Pi pin 16
SW3 = 10 #GPIO10 = Pi pin 19
SW4= 9 #GPIO9 = Pi pin 21
INPUTS = [SW1,SW2,SW3,SW4]
#HD44780 Controller Commands
CLEARDISPLAY = 0x01
SETCURSOR = 0x80
#Line Addresses. 
LINE = [0x00,0x40] #for 16x2 display

def InitIO():
    #Sets GPIO pins to input & output, as required by LCD board
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for lcdLine in OUTPUTS:
        GPIO.setup(lcdLine, GPIO.OUT)
    for switch in INPUTS:
        GPIO.setup(switch, GPIO.IN,
        pull_up_down=GPIO.PUD_UP)

def PulseEnableLine():
    #Pulse the LCD Enable line; used for clocking in data
    mSec = 0.0005 #use half-millisecond delay
    time.sleep(mSec) #give time for inputs to settle
    GPIO.output(LCD_E, GPIO.HIGH) #pulse E high
    time.sleep(mSec)
    GPIO.output(LCD_E, GPIO.LOW) #return E low
    time.sleep(mSec) #wait before doing anything else

def SendNibble(data):
    #sends upper 4 bits of data byte to LCD data pins D4-D7
    GPIO.output(LCD_D4, bool(data & 0x10))
    GPIO.output(LCD_D5, bool(data & 0x20))
    GPIO.output(LCD_D6, bool(data & 0x40))
    GPIO.output(LCD_D7, bool(data & 0x80))

def SendByte(data,charMode=False):
    #send one byte to LCD controller
    GPIO.output(LCD_RS,charMode) #set mode: command vs. char
    SendNibble(data) #send upper bits first
    PulseEnableLine() #pulse the enable line
    data = (data & 0x0F)<< 4
    #shift 4 bits to left
    SendNibble(data) #send lower bits now
    PulseEnableLine() #pulse the enable line

def InitLCD():
    #initialize the LCD controller & clear display
    SendByte(0x33) #initialize
    SendByte(0x32) #set to 4-bit mode
    SendByte(0x28) #2 line, 5x7 matrix
    SendByte(0x0C) #turn cursor off (0x0E to enable)
    SendByte(0x06) #shift cursor right
    SendByte(CLEARDISPLAY)#remove any stray characters on display



######
"""

### Read json data file ###

with open('data.json') as json_file:
	json_data = json.load(json_file)

TOTAL_PARKING_SPOTS = int(json_data["total_parking_spots"])
free_parking_spots = int(json_data["free_parking_spots"])
print 'total_parking_spots: ', TOTAL_PARKING_SPOTS
print 'free_parking_spots: ', free_parking_spots




def set_up():
    """set up the board"""

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    #GPIO.setup(11, GPIO.IN) #sensor
    GPIO.setup(16,GPIO.OUT) #led when parking lot has free spaces
    GPIO.setup(18,GPIO.OUT) #led when parking lot doesn't have free spaces
    GPIO.setup(33, GPIO.IN)
    GPIO.setup(35, GPIO.IN)

set_up()

def free_spaces_on():
    """turn green led on"""
    GPIO.output(16,GPIO.HIGH)

def free_spaces_off():
    """turn green led off"""
    GPIO.output(16,GPIO.LOW)

def no_free_spaces_on():
    """turn red led on"""
    GPIO.output(18,GPIO.HIGH)

def no_free_spaces_off():
    """turn red led off"""
    GPIO.output(18,GPIO.LOW)

ok = 1 #assume that there are free spaces at the begining

#setup leds
set_up()

"""
#setup lcd
InitIO()
InitLCD()
"""

TIME_LIMIT = 10000
time_running = 0
BLOCKED = 0
CLEAR = 1
a = None
b = None

if (free_parking_spots > 0):
    free_spaces_on()
    no_free_spaces_off()


def read_pins():
    global a
    global b
    a = GPIO.input(33)
    b = GPIO.input(35)
    if (a == BLOCKED):
        print 'beam A broken'
    else:
        print 'beam A on'

    if (b == BLOCKED):
        print 'beam B broken'
    else:
        print 'beam B on'
    time.sleep(0.1)


######################### Car ENTERING the parking lot ############################

def state_enter():
    # A is now interrupted
    global a
    global b

    if (free_parking_spots <= 0):
        print "There are NO free parking spots!"
        time.sleep(3)
        return

    while True:
        print '--State Enter'
        read_pins()
        if (b == BLOCKED):
            state_enter_phase_2()

        if (a == CLEAR):
            state_no_cars_entering_or_exiting()


def state_enter_phase_2():
    # B is now interrupted and possibly also A (still)
    global a
    global b
    while True:
        print '--State enter phase 2'
        read_pins()
        if (b == CLEAR):
            state_enter()

        if (a == CLEAR):
            state_enter_phase_3()


def state_enter_phase_3():
    # A is now clear, B still interrupted
    global a
    global b
    while True:
        print '--State enter phase 3'
        read_pins()
        if (a == BLOCKED):
            # return to state_enter_phase_2 (maybe car reversed direction)
            state_enter_phase_2()

        if (b == CLEAR):
            car_entered_parking()


def car_entered_parking():
    global free_parking_spots
    global TOTAL_PARKING_SPOTS
    print '--CAR entered parking lot!!!'

    free_parking_spots -= 1
    if (free_parking_spots <= 0):
        free_spaces_off()
        no_free_spaces_on()

    print 'Remaining free parking spots: ', free_parking_spots
    time.sleep(2)
    state_no_cars_entering_or_exiting()


######################### Car EXITING the parking lot ############################

def state_exit():
    # B is now interrupted
    global a
    global b
    if (free_parking_spots >= TOTAL_PARKING_SPOTS):
        print "There shouldn't be any cars left in the parking lot!"
        time.sleep(3)
        return


    while True:
        print '--State Enter'
        read_pins()
        if (a == BLOCKED):
            state_exit_phase_2()

        if (b == CLEAR):
            state_no_cars_entering_or_exiting()


def state_exit_phase_2():
    # A is now interrupted and possibly also B (still)
    global a
    global b
    while True:
        print '--State enter phase 2'
        read_pins()
        if (a == CLEAR):
            state_exit()

        if (b == CLEAR):
            state_exit_phase_3()


def state_exit_phase_3():
    # B is now clear, A still interrupted
    global a
    global b
    while True:
        print '--State enter phase 3'
        read_pins()
        if (b == BLOCKED):
            # return to state_exit_phase_2 (maybe car reversed direction)
            state_exit_phase_2()

        if (a == CLEAR):
            car_exit_parking()


def car_exit_parking():
    global free_parking_spots
    global TOTAL_PARKING_SPOTS
    print '--CAR exited parking lot!!!'

    free_parking_spots += 1
    free_spaces_on()
    no_free_spaces_off()

    print 'Remaining free parking spots: ', free_parking_spots
    time.sleep(2)
    state_no_cars_entering_or_exiting()


#################### No cars Entering/Exiting the parking lot ####################

def state_no_cars_entering_or_exiting():
    global time_running
    global a
    global b

    while time_running < TIME_LIMIT:
           """i = GPIO.input(11)
           if i==0:                 #nothing new happens
               time.sleep(1)
           elif i==1:               #When output from sensor is HIGH
               x = random.randint(1, 10) #generate a random number, just for debugging purposes
               if x > 0:
                   if ok == 1:
                       pass
                   else:
                       ok = 1
                       no_free_spaces_off() #turn off red led
                       free_spaces_on() #turn on green led
                else:
                    if ok == 0:
                        pass
                    else:
                        ok = 0
                        free_spaces_off()
                        no_free_spaces_on()


                #show value on lcd
                showMessage(x)

                make_tweet(x) #make the tweet
                time.sleep(1)"""

           read_pins()

           if (a == BLOCKED):
               state_enter()

           if (b == BLOCKED):
               state_exit()

           time_running += 1

state_no_cars_entering_or_exiting()

GPIO.cleanup()















