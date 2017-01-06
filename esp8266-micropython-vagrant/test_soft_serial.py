import time, machine
s = machine.SoftUART(machine.Pin(12),machine.Pin(14), baudrate=9600)
print(s)
s.flush()
s.write("ON\n")
print(s.readline())
time.sleep(1.0)
s.write("OFF\n")
print(s.readline())

