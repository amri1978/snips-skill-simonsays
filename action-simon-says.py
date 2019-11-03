#!/usr/bin/env python3


import paho.mqtt.client as mqtt
from matrix_lite import led
from random import randint
import random
import time
import json
import io


CONFIGURATION_ENCODING_FORMAT = "utf-8"
MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

INTENT_START = "start_simon_says"
INTENT_ANSWER = "give_sequence"
INTENT_STOP = "stop_game"
INTENT_DOES_NOT_KNOW = "does_not_know"

INTENT_FILTER_GET_ANSWER = [
    INTENT_ANSWER,
    INTENT_STOP,
    INTENT_DOES_NOT_KNOW
]

# MQTT client to connect to the bus
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    client.subscribe("hermes/intent/#")

def message(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    session_id = data['sessionId']
    try:
        user, intentname = data['intent']['intentName'].split(':')

            say(session_id, intentname)
    except KeyError:
        pass

def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession',
                        json.dumps({'text': text, "sessionId": session_id}))


if __name__ == "__main__":
    mqtt_client.on_connect = on_connect
    mqtt_client.message_callback_add("hermes/intent/maxbachmann:RockPaperScissors/#", message)
    mqtt_client.connect("localhost", 1883)
    mqtt_client.loop_forever()		
	

SessionsStates = {}
simonList = []

def continue_game(response, session_id):
    SessionsStates[session_id]["step"] += 1

    if SessionsStates[session_id]["step"] == SessionsStates[session_id]["n_questions"]:
        response += "You had {} out of {} correct. ".format(SessionsStates[session_id]["good"],
                                                                             SessionsStates[session_id]["n_questions"])
        percent_correct = float(SessionsStates[session_id]["good"]) / SessionsStates[session_id]["n_questions"]
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
        question, answer = create_question()
        response += question
        SessionsStates[session_id]["ans"] = answer
        cont = True

    return response, cont


def user_request_game(hermes, intent_message):
    session_id = intent_message.session_id

    print('start')
    # initialize session state
    session_state = {
        "ans": answer,
        "good": 0,
        "bad": 0,
        "step": 0,
        "n_questions": n_questions
    }
    SessionsStates[session_id] = session_state
	# Add color to list
    simonList.append(colorPick())
    # Show the pattern
    simon(simonList)
    hermes.publish_continue_session(session_id, '', INTENT_FILTER_GET_ANSWER)


def user_gives_answer(hermes, intent_message):
    session_id = intent_message.session_id

    # parse input message
    answer = intent_message.slots.answer.first().value

    # check user answer, NOTE the extra space at the end since we will add more to the response!
    if answer == SessionsStates[session_id]["ans"]:
        response = "Correct! "
        SessionsStates[session_id]["good"] += 1
    else:
        response = "Incorrect. The answer is {}. ".format(SessionsStates[session_id]["ans"])
        SessionsStates[session_id]["bad"] += 1

    # create new question or terminate if reached desired number of questions
    response, cont = continue_lesson(response, session_id)
    if cont:
        hermes.publish_continue_session(intent_message.session_id, response, INTENT_FILTER_GET_ANSWER)
    else:
        hermes.publish_end_session(session_id, response)


def user_does_not_know(hermes, intent_message):
    session_id = intent_message.session_id

    response = "That's quite alright! The answer is {}. ".format(SessionsStates[session_id]["ans"])

    # create new question or terminate if reached desired number of questions
    response, cont = continue_game(response, session_id)
    if cont:
        hermes.publish_continue_session(intent_message.session_id, response, INTENT_FILTER_GET_ANSWER)
    else:
        hermes.publish_end_session(session_id, response)


def user_quits(hermes, intent_message):
    session_id = intent_message.session_id

    # clean up
    del SessionsStates[session_id]
    response = "Alright. Let's play again soon!"
    hermes.publish_end_session(session_id, response)


# with Hermes(MQTT_ADDR) as h:

    # h.subscribe_intent(INTENT_START, user_request_game) \
        # .subscribe_intent(INTENT_STOP, user_quits) \
        # .subscribe_intent(INTENT_DOES_NOT_KNOW, user_does_not_know) \
        # .subscribe_intent(INTENT_ANSWER, user_gives_answer) \
        # .start()

		
		



def simon(simonList):
    # For every color simon has in the list turn on the led that color
    for color in simonList:
        led.set(color)
        time.sleep(0.40)
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


def user(simonList):
    counter = 0
    # Check every press until you match simon's pattern
    while not (counter == len(simonList)):
        # Restart game
        if counter == -1:
            return
        if(not gpio.getDigital(bluePin)):
            counter = verifySimon('blue', bluePin, counter)
        elif(not gpio.getDigital(greenPin)):
            counter = verifySimon('green', greenPin, counter)
        elif(not gpio.getDigital(yellowPin)):
            counter = verifySimon('yellow', yellowPin, counter)
        elif(not gpio.getDigital(redPin)):
            counter = verifySimon('red', redPin, counter)
    nextTurn()

def verifySimon(color, pin, counter):
    # All push logic is opposite(!push == pushed)
    led.set(color)
    if(simonList[counter] == color):
        counter += 1
    else:
        gameover()
        return -1
    # User is holding the button, avoid double input
    while True:
        # When the user lets go break the loop
        if(gpio.getDigital(pin)):
            led.set('black')
            break
    return counter


def colorPick():
    # Pick a random number representing one of four colors
    x =  randint(0,3)

    # Return the color matching that random number
    if x == 0:
        color = 'blue'
    elif x == 1:
        color = 'green'
    elif x == 2:
        color = 'yellow'
    else:
        color = 'red'
    return color





#while True:
    # Add color to list
 #   simonList.append(colorPick())
  #  # Show the pattern
   # simon(simonList)
    # Get user to repeat the pattern
    #user(simonList)