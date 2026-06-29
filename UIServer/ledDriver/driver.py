
import time
import spidev

spi = spidev.SpiDev()
spi.open(bus=0, device=0)

ws2812bOne  = 0b11111000
ws2812bZero = 0b11100000

def componentToSpiData(value: int) -> bytes:
    return bytes(ws2812bOne if value & (1 << bit) else ws2812bZero for bit in reversed(range(8)))

def colorToSpiData(r: int, g: int, b: int) -> bytes:
    return componentToSpiData(g) + componentToSpiData(r) + componentToSpiData(b)

try:
    while True:
        msg = b""

        for color in input().split(';'):
            if len(color) < 5:
                continue
            r, g, b = color.split(",")
            msg += colorToSpiData(int(r), int(g), int(b))

        spi.xfer3(msg, 9000000)
        # time.sleep(0.005)
except EOFError:
    pass
