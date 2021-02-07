#!/usr/bin/env python
import epd2in13bc
import logging
import subprocess
import os
import json
import socket
import psutil
import datetime

# Import Requests Library
import requests

# Import Python Imaging Library
from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne
from font_hanken_grotesk import HankenGroteskBold
from gpiozero import CPUTemperature

# Set current directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

#Prepare display
epd = epd2in13bc.EPD()
logging.info("Init and clear")
epd.init()
#epd.Clear()
scale_size = 1
padding = 0

HBlackimage = Image.new('1', (epd.height, epd.width), 255)  # 298*126
HRYimage = Image.new('1', (epd.height, epd.width), 255)  # 298*126  ryimage: red or yellow image  draw = ImageDraw.Draw(HBlackimage)
drawry = ImageDraw.Draw(HRYimage)

#load time
now = datetime.datetime.now()
datestamp = now.strftime("%m/%d %H:%M")
print(datestamp)

# Load graphics
imgB = Image.open("logoB.gif")
imgR = Image.open("logoR.gif")

scaled_width = 60
scaled_height = imgR.height * 60 // imgR.width
imgR = imgR.resize((scaled_width, scaled_height))
imgB = imgB.resize((scaled_width, scaled_height))

#paste in logo
HRYimage.paste(imgR, (0,12))
HBlackimage.paste(imgB, (0,12))

# system monitoring from here :
print("Getting System Info")
#IP = socket.gethostbyname(socket.gethostname())
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
#print(s.getsockname()[0])
IP = s.getsockname()[0]
s.close()
cpu = psutil.cpu_percent()
temp = CPUTemperature()
cputemp = temp.temperature
memory = psutil.virtual_memory().available * 100 / psutil.virtual_memory().total
ram = round(memory)

# Shell scripts for system monitoring from here :
# https://unix.stackexchange.com/questions/119126/command-to-display-memory-usage-disk-usage-and-cpu-load
#cmd = "hostname -I | cut -d\' \' -f1 | tr -d \'\\n\'"
#IP = subprocess.check_output(cmd, shell=True).decode("utf-8")
cmd = "hostname | tr -d \'\\n\'"
HOST = subprocess.check_output(cmd, shell=True).decode("utf-8")
#cmd = "top -bn1 | grep load | awk " \
#      "'{printf \"CPU Load: %.2f\", $(NF-2)}'"
#CPU = subprocess.check_output(cmd, shell=True).decode("utf-8")
#cmd = "free -m | awk 'NR==2{printf " \
#      "\"Mem: %s/%sMB %.2f%%\", $3,$2,$3*100/$2 }'"
#MemUsage = subprocess.check_output(cmd, shell=True).decode("utf-8")
#cmd = "df -h | awk '$NF==\"/\"{printf " \
#      "\"Disk: %d/%dGB %s\", $3,$2,$5}'"
#Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")

# get api data // Pi Hole data!
api_url = 'http://localhost/admin/api.php'
print("getting pi-hole data")

try:
    r = requests.get(api_url)
    data = json.loads(r.text)
    DNSQUERIES = data['dns_queries_today']
    ADSBLOCKED = data['ads_blocked_today']
    CLIENTS = data['unique_clients']
    ratioblocked = data['ads_percentage_today']

except KeyError:
    time.sleep(1)

ratio = round(float(str(ratioblocked)),2)

font1 = ImageFont.truetype(HankenGroteskBold, int(24 * scale_size))
font2 = ImageFont.truetype(FredokaOne, int(30 * scale_size))
font4 = ImageFont.truetype(HankenGroteskBold, int(12 * scale_size))
font7 = ImageFont.truetype("Font.ttc", int(12 * scale_size))
degrees = u"\N{DEGREE SIGN}"

print("drawing data")
draw.text((0,0), "IP: " + str(IP), fill = 0, font = font7)
draw.text((60,78), datestamp, fill = 0, font = font7)
draw.text((0,92), "Clients: " + str(CLIENTS), fill = 0, font = font7)
draw.text((60,92), "Queries: " + str(DNSQUERIES), fill = 0, font = font4)
draw.text((epd.height-60,epd.width-36), "CPU: " + str(cpu), fill = 0, font = font4)
draw.text((epd.height-60,epd.width-24), "  " + str(cputemp) + degrees + "C", fill = 0, font = font4)
draw.text((epd.height-60,epd.width-12), "RAM: " + str(ram) + "%", fill = 0, font = font4)

drawry.text((120,6), str(ADSBLOCKED), fill = 0, font = font2)
draw.text((100,38), str(ratio) + "%", fill = 0, font = font1)

#print all images to e-ink
epd.display(epd.getbuffer(HBlackimage), epd.getbuffer(HRYimage))

epd2in13bc.epdconfig.module_exit()
exit()