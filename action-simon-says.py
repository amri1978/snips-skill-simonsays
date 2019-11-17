#!/usr/bin/env python3
from hermes_python.hermes import Hermes
from matrix_lite import led
from random import randint
import time

CONFIGURATION_ENCODING_FORMAT = "utf-8"
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

INTENT_START = "amri_amin:start_simon_says"
INTENT_ANSWER = "amri_amin:give_sequence"
INTENT_STOP = "amri_amin:stop_game"
INTENT_DOES_NOT_KNOW = "amri_amin:does_not_know"

INTENT_FILTER_GET_ANSWER = [
    INTENT_ANSWER,
    INTENT_STOP,
    INTENT_DOES_NOT_KNOW
]
SessionsStates = {}
simonList = []

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
        time.sleep(0.60)
        # Turn it off for a bit to differentiate the list
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
        time.sleep(0.01)



def verifySimon(color, pin, counter):
    led.set(color)
    if(simonList[counter] == color):
        counter += 1
    else:
        gameover()
        return -1
    return counter

def continue_game(response, session_id):
    SessionsStates[session_id]["step"] += 1

    if SessionsStates[session_id]["step"] == simonList.count():
        response += "You had {} out of {} correct. ".format(SessionsStates[session_id]["good"],
                                                                             simonList.count())
        percent_correct = float(SessionsStates[session_id]["good"]) / simonList.count()
        if percent_correct == 1.:
            response += "You are so smart!"
        elif percent_correct >= 0.75:
            response += "Well done! With a bit more practice you'll be a master."
        elif percent_correct >= 0.5:
            response += "Not bad. With more practice, you'll get better."
        else:
            response += "You should really practice more."
        del SessionsStates[session_id]
        cont = False
    else:
        
        cont = True

        nextTurn()

    return response, cont


def user_request_game(hermes, intent_message):
    session_id = intent_message.session_id
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
    hermes.publish_continue_session(session_id, 'Let\'s start', INTENT_FILTER_GET_ANSWER)


def user_gives_answer(hermes, intent_message):
    session_id = intent_message.session_id

    index = 0
    # parse input message
    for answer in intent_message.slots.answer:
             print(answer.value)



def user_does_not_know(hermes, intent_message):
    session_id = intent_message.session_id
    response = "That's quite alright! The answer is {}. ".format("Put answer here")
    # create new question or terminate if reached desired number of questions
    response, cont = continue_game(response, session_id)
    if cont:
        hermes.publish_continue_session(intent_message.session_id,response, INTENT_FILTER_GET_ANSWER)
    else:
        hermes.publish_end_session(session_id, response)


def user_quits(hermes, intent_message):
    session_id = intent_message.session_id
    # clean up
    del SessionsStates[session_id]
    response = "Alright. Let's play again soon!"
    hermes.publish_end_session(session_id, response)


with Hermes(MQTT_ADDR) as h:

    h.subscribe_intent(INTENT_START, user_request_game) \
        .subscribe_intent(INTENT_STOP, user_quits) \
        .subscribe_intent(INTENT_DOES_NOT_KNOW, user_does_not_know) \
        .subscribe_intent(INTENT_ANSWER, user_gives_answer) \
        .start()

