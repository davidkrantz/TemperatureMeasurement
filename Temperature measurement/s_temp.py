import os
import glob
import time
import sys
import MySQLdb as mdb

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'


# Read the temperature
def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


# Convert the temperature to degrees Celsius
def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c


time.sleep(57)

# Save the temperature to the MySQL database
try:
    pi_temp = read_temp()
    con = mdb.connect('localhost',
                      'pi_insert',
                      'password',
                      'measurements')
    cur = con.cursor()
    cur.execute("""INSERT INTO temperature(temperature) \
                       VALUES(%s)""", (pi_temp))
    con.commit()

except mdb.Error:
    con.rollback()
    sys.exit(1)

finally:
    if con:
        con.close()
