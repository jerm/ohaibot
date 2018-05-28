#!/usr/bin/env python

import click
import ipdb
import logging
import time
import atexit
import gevent
import boto.sqs
from boto.sqs.message import Message
from signal import pause

import wiringpi
from Adafruit_MotorHAT import Adafruit_MotorHAT, Adafruit_DCMotor, Adafruit_StepperMotor
from gpiozero import LED, Button

# Amazon Rekognition lib
import jermops_rek

formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "progname":' +
            ' "%(name)s", "loglevel": "%(levelname)s", "message":, "%(message)s"}')
log = logging.getLogger(__file__)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

stepperpower = LED(24)
stepperpower.on()

ENDSTOP_RIGHT = Button(17)
ENDSTOP_LEFT = Button(18)

VALID_FACES = ['jeremy']
# import check_for_shutdown_button
# create a default object, no changes to I2C address or frequency
mh = Adafruit_MotorHAT()

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    mh.getMotor(1).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(2).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(3).run(Adafruit_MotorHAT.RELEASE)
    mh.getMotor(4).run(Adafruit_MotorHAT.RELEASE)
    stepperpower.off()

atexit.register(turnOffMotors)

myStepper = mh.getStepper(200, 1)  # 200 steps/rev, motor port #1
myStepper.setSpeed(180)             # 30 RPM


def move_degrees(degrees):
    global ENDSTOP_RIGHT
    global ENDSTOP_LEFT
    movement_type = Adafruit_MotorHAT.MICROSTEP
    if degrees < 0:
        direction = Adafruit_MotorHAT.BACKWARD
        degrees = -degrees
        endbutton = ENDSTOP_LEFT
    else:
        direction = Adafruit_MotorHAT.FORWARD
        endbutton = ENDSTOP_RIGHT

    steps = int(degrees / .875)
    try:
        for step in range (0, steps):
            log.debug(step)
            myStepper.step(1, direction, movement_type)
            if endbutton.is_pressed:
                myStepper.step(-1, direction, movement_type)
                log.info("Hit endstop {}".format(endbutton))
                break

    except KeyboardInterrupt:
        log.info("Stopping Movement.")
        myStepper.step(1, direction, movement_type)
        return 0


# def forward_degrees(degrees):
#     steps = int(degrees / .887)
#     for step in range (0, steps):
#         myStepper.step(1, Adafruit_MotorHAT.FORWARD,  Adafruit_MotorHAT.MICROSTEP)
#         if ENDSTOP_RIGHT.is_pressed:
#             break
#     # turnOffMotors()


def ohai():
    ohai_degrees = 40
    log.debug("Forward {} degrees".format(ohai_degrees))
    move_degrees(ohai_degrees)


def kthxbai():
    kthxbai_degrees = -40
    log.debug("Backward {} degrees".format(-kthxbai_degrees))
    move_degrees(kthxbai_degrees)


def so_reply(queue, valid_face):
    msg = Message()
    if valid_face == None:
        msg.set_body('much lonely')
        log.debug('much lonely')
    elif valid_face == False:
        msg.set_body('newfacewhodis')
        log.debug('newfacewhodis')
    else:
        msg.set_body('such face')
        log.debug('such face')
    queue.write(msg)


def snap_and_verify_valid_face_from_db(valid_faces=VALID_FACES):
    log.debug("Checking who is in front of workstation")
    if type(valid_faces) == str:
        valid_faces = [valid_faces]
    face = rek.find_new_face()
    if not face:
        if face == False:
            log.debug("Unkown face found in snap_and_verify_valid_face_from_db")
            return False
        if face == None:
            log.debug("No Faces found in snap_and_verify_valid_face_from_db")
            return None

    # Look in our DB to match face to name
    face_name = rek.lookup_face_hash(face['Face']['FaceId'])
    if not face_name:
        log.debug("No DB record of face {}".format(face['Face']['FaceId']))
        return False
    else:
        if face_name in valid_faces:
            log.debug("Matched valid face {} from db".format(face_name))
            return face_name
        else:
            log.debug("Face {} found, but not allowed, per valid_faces=={}".format(face_name, valid_faces))
            return False


def run(check_faces, noorigin):
    conn = boto.sqs.connect_to_region('us-east-2')
    tobotq = conn.get_queue('ohaijermops')
    frombotq = conn.get_queue('ohaicallback')

    # Origin the ohaibot at startup, because gravity and unpowered motors
    if not noorigin:
        kthxbai()

    log.info("Very running...")
    while True:
        try:
            msg = tobotq.read(wait_time_seconds=20)
            if msg:
                body = msg._body.split(":")[0]
                tobotq.delete_message(msg)
                if body in 'ohai':
                    if check_faces:
                        valid_face = snap_and_verify_valid_face_from_db()
                        so_reply(frombotq, valid_face)
                    else:
                        so_reply(frombotq, "Ohai is like a box of chocolates")
                        valid_face = True
                    if valid_face:
                        ohai()
                elif body in 'bye':
                    kthxbai()
                else:
                    print("Say what? (msg: {})", body)

        except KeyboardInterrupt:
            print("Exiting...")
            return 0

@click.command()
@click.option('--check-faces', is_flag=True, help="Should we check for valid faces?")
@click.option('--noorigin', is_flag=True, help="Don't home on startup")
def main(check_faces, noorigin):
    # type: (bool) -> None

    run(check_faces, noorigin)

if __name__ == "__main__":
    # ipdb.set_trace()
    main()
