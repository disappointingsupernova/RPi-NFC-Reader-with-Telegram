def main():
    import time
    import RPi.GPIO
    RPi.GPIO.setwarnings(False)
    from pirc522 import RFID
    RFID = RFID
    rdr = RFID()
    util = rdr.util()
    while True:

        error, data = rdr.request()
        error, uid = rdr.anticoll()

        if not error:
            break
        time.sleep(0.5)

    return uid

print(main())