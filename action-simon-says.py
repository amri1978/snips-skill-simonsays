#!/usr/bin/env python3
from hermes_python.hermes import Hermes
from matrix_lite import led
from random import randint
import time
import threading

CONFIGURATION_ENCODING_FORMAT = "utf-8"
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

INTENT_START = "amri_amin:start_simon_says"
INTENT_ANSWER = "amri_amin:give_sequence"
INTENT_STOP = "amri_amin:stop_game"
INTENT_DOES_NOT_KNOW = "amri_amin:does_not_know"
INTENT_SESSION_ENDED     = "hermes:dialogueManager:sessionEnded"

INTENT_FILTER_GET_ANSWER = [
    INTENT_ANSWER,
    INTENT_STOP,
    INTENT_DOES_NOT_KNOW
]
SessionsStates = {}
simonList = []
session_id = 0

def colorPick():
    x =  randint(0,3)
    if x == 0:
        color = 'blue'
    elif x == 1:
        color = 'green'
    elif x == 2:
        color = 'yellow'
    else:
        color = 'red'
    return color

def simon(simonList):
    # For every color simon has in the list turn on the led that color
    for color in simonList:
        led.set(color)
        time.sleep(0.30)
        # Turn it off for a bit
        led.set('black')
        time.sleep(0.25)

def gameover():
    global simonList
    for i in range(3):
        led.set('red')
        time.sleep(0.5)
        led.set('white')
        time.sleep(0.5)
    led.set('black')
    nextTurn()
    simonList = []


def nextTurn():
    everloop = ['black'] * led.length
    everloop[0] = {'b':100}
    for x in range(led.length):
        everloop.append(everloop.pop(0))
        led.set(everloop)
        time.sleep(0.1)

def verifySimon(color, counter):
    if color == '2869x255':
        color = 'red'
    elif color == '44161x255':
        color = 'blue'
    elif color=='11222x255':
        color = 'yellow'
    elif color=='21845x255':
        color = 'green'
    led.set(color)
    if(simonList[counter] == color):
        return  True
    else:
        print('game over')
        gameover()
        return False

def start_game(session_id):
    print('start')
    # initialize session state
    session_state = {
        "good": 0,
        "bad": 0,
        "step": 0
    }
    SessionsStates[session_id] = session_state
    # Add color to list
    simonList.append(colorPick())
    # Show the pattern
    simon(simonList)



def user_request_game(hermes,intent_message):
    session_id = intent_message.session_id
    start_game(session_id)
    hermes.publish_continue_session(session_id,'Let\'s start', INTENT_FILTER_GET_ANSWER)

def user_gives_answer(hermes, intent_message):
    session_id = intent_message.session_id
    answers = []
    index =-1
    print(simonList)
    # parse input message
    for slot_value in intent_message.slots.color.all():
        index=index+1        
        print (slot_value.value)
        if (not verifySimon(slot_value.value,index)):
           user_quits(hermes, intent_message)
           return 0
    simonList.append(colorPick())
    simon(simonList)
    hermes.publish_continue_session(session_id,'',INTENT_FILTER_GET_ANSWER)
               

def user_does_not_know(hermes, intent_message):
    session_id = intent_message.session_id
    response = "Try again"
    hermes.publish_continue_session(intent_message.session_id,response, INTENT_FILTER_GET_ANSWER)



def user_quits(hermes, intent_message):
    session_id = intent_message.session_id
    # clean up
    del SessionsStates[session_id]
    response = "Alright. Let's play again soon!"
    hermes.publish_end_session(session_id, response)

def session_ended(hermes, intent_message):
    session_id = intent_message.session_id
    response = "Session Ended!"
    hermes.publish_end_session(session_id, response)
    
with Hermes(MQTT_ADDR) as h:

    h.subscribe_intent(INTENT_START, user_request_game) \
        .subscribe_intent(INTENT_STOP, user_quits) \
        .subscribe_intent(INTENT_DOES_NOT_KNOW, user_does_not_know) \
        .subscribe_intent(INTENT_ANSWER, user_gives_answer) \
        .start()
    


