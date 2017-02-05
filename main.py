#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# Yury Kuznetsov (WF_LM)
# 11.12.2016
# Telegram bot is "@My_C3P_bot"

# This program reads NFC-tags, shows information about
# this tags, open/close lock and sends information to
# the Telegram Messenger (if you want).

TELEGRAM_TOKEN = "...(enter your value)..."

class NFC_Telegram():
    def __init__(self):

        import wiringpi
        self.wiringpi = wiringpi

        from db import db
        self.db = db

        from pirc522 import RFID
        self.RFID = RFID

        import time
        self.time = time

    def __port_initialization__(self):

        self.RED_LED_PIN = 12
        self.GREEN_LED_PIN = 16

        self.wiringpi.wiringPiSetupPhys()
        self.wiringpi.pinMode(self.RED_LED_PIN, 2)
        self.wiringpi.pwmWrite(self.RED_LED_PIN, 1023)
        self.wiringpi.pinMode(self.GREEN_LED_PIN, 1)
        self.wiringpi.digitalWrite(self.GREEN_LED_PIN, 0)

        import RPi.GPIO
        RPi.GPIO.setwarnings(False)

    def __nfc_initialization__(self):
        self.rdr = self.RFID()
        self.util = self.rdr.util()

    def __nfc__tag__detect__(self):
        error, data = self.rdr.request()
        detect = not error
        return detect

    def __nfc_tag_capture__(self):
        error, uid = self.rdr.anticoll()
        tag_capture = not error
        return (tag_capture, uid)

    def __nfc_tag_stop__(self):
        self.util.deauth()

    def __db_user_find__(self, uid):
        return self.db[uid] if uid in self.db else False

    def __access_handler__(self, access):

        if access:

            self.wiringpi.digitalWrite(self.GREEN_LED_PIN, 1)
            self.wiringpi.pwmWrite(self.RED_LED_PIN, 0)
            self.time.sleep(1)

            for i in range(1024):
                self.wiringpi.pwmWrite(self.RED_LED_PIN, i)
                self.time.sleep(2 / 1024)
            self.time.sleep(1)
            self.wiringpi.digitalWrite(self.GREEN_LED_PIN, 0)
            for i in range(3):
                self.time.sleep(0.25)
                self.wiringpi.pwmWrite(self.RED_LED_PIN, 0)
                self.time.sleep(0.25)
                self.wiringpi.pwmWrite(self.RED_LED_PIN, 1023)


        else:
            for i in range(3):
                self.time.sleep(0.25)
                self.wiringpi.pwmWrite(self.RED_LED_PIN, 0)
                self.time.sleep(0.25)
                self.wiringpi.pwmWrite(self.RED_LED_PIN, 1023)

    def __initial_states__(self):
        self.wiringpi.pwmWrite(12, 0)
        self.wiringpi.digitalWrite(16, 0)
        self.wiringpi.pinMode(12, 0)
        self.wiringpi.pinMode(16, 0)

    def __output_to_console__(self, uid, user):

        if user == False:
            output = "Unidientified user. \nACCESS IF DENIED!"
        else:
            localtime = self.time.localtime()
            output = self.time.strftime("%H:%M:%S %d/%m/%Y", self.time.localtime()) + "\n{name} {second_name}, {job}.".format(
                name=user[0],
                second_name=user[1],
                job=user[2])

            if user[3]:
                output += "\nACCESS IS ALLOWED."
            else:
                output += "\nACCESS IS DENIED!"

        return output

    def start_standart(self):
        self.__port_initialization__()
        self.__nfc_initialization__()
        while True:

            try:

                if self.__nfc__tag__detect__():
                    tag_capture, uid = self.__nfc_tag_capture__()
                    uid = tuple(uid)
                    self.__nfc_tag_stop__()

                    if tag_capture:
                        user = self.__db_user_find__(uid)
                        to_print = self.__output_to_console__(uid, user)
                        print(to_print)
                        print('*' * 20)
                        if user:
                            self.__access_handler__(user[3])
                        else:
                            self.__access_handler__(False)


                self.time.sleep(0.5)

            except KeyboardInterrupt:
                self.__initial_states__()
                break

    def __telegram_initialization__(self):
        self.__quit_bit__ = False
        from telegram.ext import CommandHandler
        self.CommandHandler = CommandHandler

        from threading import Thread
        self.Thread = Thread

        from telegram.ext import Updater
        self.updater = Updater(token=TELEGRAM_TOKEN)
        self.dispatcher = self.updater.dispatcher

        self.start_continue = [False, ]


    def start_telegram(self):
        self.__telegram_initialization__()

        self.__port_initialization__()
        self.__nfc_initialization__()

        start_thread_handler = self.CommandHandler('start', self.__start__)
        stop_thread_handler = self.CommandHandler('stop', self.__stop__)

        self.dispatcher.add_handler(start_thread_handler)
        self.dispatcher.add_handler(stop_thread_handler)

        self.updater.start_polling()




    def __start_thread__(self, bot, update):
        if self.start_continue[0] == False:
            self.start_continue[0] = True

            bot.sendMessage(chat_id=update.message.chat_id, text='OK.')

            while self.start_continue[0]:

                try:

                    if self.__nfc__tag__detect__():
                        tag_capture, uid = self.__nfc_tag_capture__()
                        uid = tuple(uid)
                        self.__nfc_tag_stop__()

                        if tag_capture:
                            user = self.__db_user_find__(uid)

                            to_print = self.__output_to_console__(uid, user)
                            print(to_print)
                            bot.sendMessage(chat_id=update.message.chat_id, text=to_print)

                            if user:
                                self.__access_handler__(user[3])
                            else:
                                self.__access_handler__(False)

                            print('*' * 20)
                    self.time.sleep(0.5)

                except KeyboardInterrupt:
                    self.__initial_states__()
                    break

        else:
            bot.sendMessage(chat_id=update.message.chat_id, text='The program working now.')

    def __stop_thread__(self, bot, update):
        if self.start_continue[0] == True:
            self.start_continue[0] = False
            bot.sendMessage(chat_id=update.message.chat_id, text='OK')
        else:
            bot.sendMessage(chat_id=update.message.chat_id, text='The program isn\'t working now.')

    def __start__(self, bot, update):

        self.start_thread_object = self.Thread(target=self.__start_thread__, args=(bot, update))
        self.start_thread_object.start()

    def __stop__(self, bot, update):

        self.stop_thread_object = self.Thread(target=self.__stop_thread__, args=(bot, update))
        self.stop_thread_object.start()


def main():
    from sys import argv
    global execution
    execution = NFC_Telegram()

    if len(argv) == 2:
        if argv[1] == '-t':
            print("Start Telegram version")
            execution.start_telegram()
        else:
            print("Start standart version")
            execution.start_standart()
    else:
        print("Start standart version")
        execution.start_standart()

main()
