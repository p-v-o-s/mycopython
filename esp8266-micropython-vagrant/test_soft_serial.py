import machine
s = machine.SoftUART(machine.Pin(12),machine.Pin(14), baudrate=9600)
print(s)

print(s.read(10))

