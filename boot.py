#####################################################################
# このプログラムは下記copyright表記のプログラムを引用して使用しています。
# Copyright (c) 2022 Takao Akaki. All rights reserved.
#####################################################################

# Notice:
# If you want to use it with Sipeed Maix series, you need config.json in flash.
# Run the script in the link below.
# https://github.com/sipeed/MaixPy_scripts/tree/master/board

# BOARD_NAME == M5STICKV or M1DOCK or MAIXDUINO
BOARD_NAME = "M5STICKV"

import time
from Maix import GPIO, I2S
from fpioa_manager import *
from board import board_info
import os, Maix, lcd, image
from machine import I2C,UART

# サーボボードを動かすためのI2Cインポート
from machine import I2C
import servo


if (BOARD_NAME == "M5STICKV"):
    from pmu import axp192
    pmu = axp192()
    pmu.enablePMICSleepMode(True)

sample_rate   = 16000


#####################################################################
# Initial values
#####################################################################
# If you increase the words array, the number of registered words
# will also increase.
words = ["open", "close", "Vsign", "aloha", "good"]

# If the word recognition rate is low, look at the values of
# dtw_value and current_frame_len in the terminal and adjust them.
dtw_threshold = 400
frame_len_threshold = 70

if (BOARD_NAME == "M5STICKV"):
# GPIO Settings for M5StickV.
    lcd.init(type=3)
    fm.register(board_info.MIC_DAT,fm.fpioa.I2S0_IN_D0, force=True)
    fm.register(board_info.MIC_LRCLK,fm.fpioa.I2S0_WS, force=True)
    fm.register(board_info.MIC_CLK,fm.fpioa.I2S0_SCLK, force=True)
    fm.register(34, fm.fpioa.UART2_TX, force=True)
    fm.register(35, fm.fpioa.UART2_RX, force=True)
    fm.register(board_info.BUTTON_A, fm.fpioa.GPIO1, force=True)
    fm.register(board_info.BUTTON_B, fm.fpioa.GPIO2, force=True)
    button_a_label = "BtnA"
elif ((BOARD_NAME == "MAIXDUINO") or (BOARD_NAME == "M1DOCK")):
# GPIO Settings for Maixduino or M1Dock.
    lcd.init()
    fm.register(board_info.MIC0_DATA, fm.fpioa.I2S0_IN_D0, force=True)
    fm.register(board_info.MIC0_WS, fm.fpioa.I2S0_WS, force=True)
    fm.register(board_info.MIC0_BCK, fm.fpioa.I2S0_SCLK, force=True)
    fm.register(21, fm.fpioa.UART2_TX, force=True)  # Maixduino PIN2
    fm.register(22, fm.fpioa.UART2_RX, force=True)  # Maixduino PIN3
    fm.register(board_info.BOOT_KEY, fm.fpioa.GPIO1, force=True)
    button_a_label = "BtnBoot"

uart_port = UART(UART.UART2, 115200, 8, None, 1, timeout=1000, read_buf_len=4096)
button_a = GPIO(GPIO.GPIO1, GPIO.IN, GPIO.PULL_UP)  # LCD横のボタン
button_b = GPIO(GPIO.GPIO2, GPIO.IN, GPIO.PULL_UP)  # LCD側面のボタン





# data storage "/sd/" or "/flash/"
storage = "/sd/"
# storage = "/flash/"


#####################################################################
# Functions
#####################################################################
def print_lcd(str1=None, str2=None, str3=None, serial_out=True, bgcolor=(0, 0, 0)):
    if (str1 != None):
        img.draw_rectangle((0, 0, lcd_w, 45), fill=True, color=bgcolor)
        img.draw_string(10, 10, str1, color=(255, 0, 0), scale=2, mono_space=0)
        if (serial_out):
            print(str1)
    if (str2 != None):
        img.draw_rectangle((10, 45, lcd_w, 40), fill=True, color=bgcolor)
        img.draw_string(10, 45, str2, color=(0, 0, 255), scale=2, mono_space=0)
        if (serial_out):
            print(str2)
    if (str3 != None):
        img.draw_rectangle((10, 90, lcd_w, 40), fill=True, color=bgcolor)
        img.draw_string(10, 90, str3, color=(0, 0, 255), scale=2, mono_space=0)
        if (serial_out):
            print(str3)
    lcd.display(img)


def save_file(number, data):
    print_lcd("Data Saving...")
    lcd.display(img)
    filename0 = storage + "rec0_" + str(number) + ".sr"
    filename1 = storage + "rec1_" + str(number) + ".sr"
    t0 = data[0]
    t1 = data[1]
    print(type(t0))
    print(type(t1))
    with open(filename0, 'w') as f:
        f.write(str(t0))
    with open(filename1, 'wb') as f:
        f.write(bytearray(t1))

def load_data(number):
    print_lcd("Data Loading...")
    for i in range(number):
        print("load_data:" + str(i))
        filename0 = storage + "rec0_" + str(i) + ".sr"
        filename1 = storage + "rec1_" + str(i) + ".sr"
        with open(filename0, 'r') as f:
            data0 = f.read()
        with open(filename1, 'rb') as f:
            data1 = f.read()
        print(data0)
        print(data1)
        tupledata = [int(data0), data1]
        sr.set(i*2, tupledata)
        print(b'0x0d0x0a')

def record_voice():
    for i in range(len(words)):
        while True:
            time.sleep_ms(100)
            print(sr.state())
            if sr.Done == sr.record(i*2):
                print_lcd("get !")
                data = sr.get(i*2)
                save_file(i, data)
                print(data)
                break
            for sec in range(3, 0, -1):
                print_lcd("wait {} sec".format(sec))
                time.sleep(1)
            if sr.Speak == sr.state():
                for sec in range(2, 0, -1):
                    print_lcd("Please speak {}".format(words[i]), "remain {} sec".format(sec))
                    time.sleep(1)

        sr.set(i*2, data)
        time.sleep_ms(500)

def servo_hand(i):
    i2c = I2C(I2C.I2C0, freq=100000, scl=34, sda=35)
    s = servo.Servos(i2c)

    if i == 0:
        s.position(1,0)     # guu
        s.position(2,150-0) # guu
        s.position(3,150-0) # guu
        s.position(4,150-0) # guu
        s.position(5,150-0) # guu

    elif i == 1:
        s.position(1,150)     # paa
        s.position(2,150-150) # paa
        s.position(3,150-150) # paa
        s.position(4,150-150) # paa
        s.position(5,150-150) # paa

    elif i == 2:
        s.position(1,0)       # choki
        s.position(2,150-150) # choki
        s.position(3,150-150) # choki
        s.position(4,150-0)   # choki
        s.position(5,150-0)   # choki

    elif i == 3:
        s.position(1,150)       # aloha
        s.position(2,150-0)     # aloha
        s.position(3,150-0)     # aloha
        s.position(4,150-0)     # aloha
        s.position(5,150-150)   # aloha

    elif i == 4:
        s.position(1,150)       # good
        s.position(2,150-0)     # good
        s.position(3,150-0)     # good
        s.position(4,150-0)     # good
        s.position(5,150-0)     # good


##############################################################################
# Main
##############################################################################

i2c_sv = I2C(I2C.I2C0, freq=100000, scl=34, sda=35)
s = servo.Servos(i2c_sv)
s.position(1,150)     # paa
s.position(2,150-150) # paa
s.position(3,150-150) # paa
s.position(4,150-150) # paa
s.position(5,150-150) # paa
time.sleep_ms(1000)
#servo_hand(3)
s.position(1,150)       # aloha
s.position(2,150-0)     # aloha
s.position(3,150-0)     # aloha
s.position(4,150-0)     # aloha
s.position(5,150-150)   # aloha
time.sleep_ms(1000)
s.position(1,0)       # choki
s.position(2,150-150) # choki
s.position(3,150-150) # choki
s.position(4,150-0)   # choki
s.position(5,150-0)   # choki
time.sleep_ms(1000)
s.position(1,150)       # good
s.position(2,150-0)     # good
s.position(3,150-0)     # good
s.position(4,150-0)     # good
s.position(5,150-0)     # good


lcd.rotation(0)

#if (BOARD_NAME == "M5STICKV"):
#    # set lcd backlight for M5StickV
#    i2c = I2C(I2C.I2C0, freq=400000, scl=28, sda=29)
#    i2c.writeto_mem(0x34, 0x91, b'\xa0')
#elif ((BOARD_NAME == "MAIXDUINO") or (BOARD_NAME == "M1DOCK")):
#    lcd.set_backlight(50)

lcd_w = lcd.width()
lcd_h = lcd.height()
img = image.Image(size=(lcd_w, lcd_h))
print_lcd("MaixPy", "Isolated words Recognizer")
rx = I2S(I2S.DEVICE_0)
rx.channel_config(rx.CHANNEL_0, rx.RECEIVER, align_mode=I2S.STANDARD_MODE)
rx.set_sample_rate(sample_rate)
print(rx)
from speech_recognizer import isolated_word
# model
sr = isolated_word(dmac=2, i2s=I2S.DEVICE_0, size=50)
print(sr.size())
print(sr)
## threshold
sr.set_threshold(0, 0, 10000)


# data set
try:
    load_data(len(words))
except Exception as e:
    record_voice()

# recognition
print_lcd("Recognition begin")
time.sleep_ms(1000)

while True:
    time.sleep_ms(200)
    print_lcd("Please speak word!", button_a_label + ":Record Voice", serial_out=False)
    if (button_a.value() == 0): # Aボタンが押された場合
        record_voice()

    if button_b.value() == 0:   # Bボタンが押された場合
        machine.reset()

    if sr.Done == sr.recognize():
        res = sr.result()
        print("(Number,dtw_value,currnt_frame_len,matched_frame_len)=" + str(res))
        print_lcd(str3=str(res))
        if (res != None) and (res[1] < dtw_threshold) and (res[2] > frame_len_threshold):
            print(str(res[0]))
            for i in range(len(words)):
                if res[0] == (i * 2):
                    print_lcd("Recognize",str3="Word: " + words[i], bgcolor=(0, 255, 255))

                    #servo_hand(i/2)
                    print("i = " + str(i/2) + "\n")   #iの値を確認

                    if i == 0:
                        #open
                        s.position(1,150)     # paa
                        s.position(2,150-150) # paa
                        s.position(3,150-150) # paa
                        s.position(4,150-150) # paa
                        s.position(5,150-150) # paa

                    elif i == 1:
                        #close
                        s.position(1,0)     # guu
                        s.position(2,150-0) # guu
                        s.position(3,150-0) # guu
                        s.position(4,150-0) # guu
                        s.position(5,150-0) # guu

                    elif i == 2:
                        s.position(1,0)       # choki
                        s.position(2,150-150) # choki
                        s.position(3,150-150) # choki
                        s.position(4,150-0)   # choki
                        s.position(5,150-0)   # choki

                    elif i == 3:
                        s.position(1,150)       # aloha
                        s.position(2,150-0)     # aloha
                        s.position(3,150-0)     # aloha
                        s.position(4,150-0)     # aloha
                        s.position(5,150-150)   # aloha

                    elif i == 4:
                        s.position(1,150)       # good
                        s.position(2,150-0)     # good
                        s.position(3,150-0)     # good
                        s.position(4,150-0)     # good
                        s.position(5,150-0)     # good


                    # data_packet = bytearray([0xFF, 0x05, 0xFF, i]) # header FF05FF
                    time.sleep_ms(200)
