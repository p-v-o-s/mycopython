import time, machine
ser = machine.SoftUART(machine.Pin(12),machine.Pin(14), baudrate=9600)
print(ser)
ser.flush()
ser.write("ON\n")
print(ser.readline())
time.sleep(1.0)
ser.write("OFF\n")
print(ser.readline())

