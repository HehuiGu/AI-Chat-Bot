#Author name: HEHUI GU
#Time：2019-Sep-12

# Import necessary modules
from rasa_nlu import config
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config

import spacy
import random
import pandas as pd

nlp = spacy.load("en_core_web_md")
# Create a trainer that uses this config
trainer = Trainer(config.load("config_spacy.yml"))

# Load the training data
training_data = load_data('train_calorie.json')

# Create an interpreter by training the model
interpreter = trainer.train(training_data)

results = ['Please try {0}, {1}, {2} ',
          'Why not try {0}, {1}, {2} ']
responses = [
    "Sorry, no such meal plan can meet your requirements",
    '{0} would work for you!',
    '{0}, {1} is a good meal plan!',
    random.choice(results)
]

# Define the states
import re
INIT = 0
AUTHED = 1
CHOOSE_RESTAURANT = 2
ORDER_FOOD = 3
DELIVERY = 4
DE= 5
PLAN_CAL = 6
MEAL_PLAN = 7
CHAT = 8
#PIE = 8

# Define the policy rules
policy_rules = {
    #(INIT, "ask_condition"): (INIT, "I am a bot to help you make a meal plan or order some food", None),
    (INIT, "order"): (INIT, "Please offer your phone number at first", AUTHED),
    (INIT, "ask_condition"): (INIT, "I am a bot to help you make a meal plan or order some food", None),
    (INIT, "plan"): (PLAN_CAL, "How many calories are you planning to consume in one day ?", None),
    (PLAN_CAL, "meal_plan"): (MEAL_PLAN, None, None),
    (MEAL_PLAN, "meal_plan"): (MEAL_PLAN,None, None),
    (MEAL_PLAN, "pie"): (INIT, None, None),
    (INIT, "number"): (AUTHED, "You can order food now",None),
    (AUTHED, "order"): (CHOOSE_RESTAURANT, "Which restaurant would you like to order from?", None),
    (CHOOSE_RESTAURANT, "restaurant"): (ORDER_FOOD, "What food would you like in {0} ?", None),
    (ORDER_FOOD, "recommand"): (ORDER_FOOD, "How about {0} ?", None),
    (DELIVERY, "ask_calories"): (INIT, "The calories are {0}", None),
    (ORDER_FOOD, "food"): (DELIVERY, "OK, you can get your delivery a few minutes later", None),
    (INIT, "greet"): (CHAT, None,None),
    (CHAT, "chat"): (CHAT, None,None),
    (CHAT, "ask_condition"): (INIT, "I am a bot to help you make a meal plan or order some food",None)
}

import requests


# find restaurant
def find_restaurant(message):
    name = None
    # Create a pattern for finding capitalized words
    name_pattern = re.compile('[A-Z]{1}[a-z|A-Z]*')
    # Get the matching words in the string
    name_words = name_pattern.findall(message)
    if len(name_words) > 0:
        # Return the name if the keywords are present
        name = ' '.join(name_words)
        return name
    return None


def find_food(params):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/food/menuItems/search"
    querystring = {"offset": "0", "number": "1", "minCalories": "0", "maxCalories": "5000", "minProtein": "0",
                   "maxProtein": "100", "minFat": "0", "maxFat": "100", "minCarbs": "0", "maxCarbs": "100", "query": ""}
    querystring['query'] = params
    headers = {
        'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        'x-rapidapi-key': "1530809090mshbd1bfa86ad13155p19a75djsn12b4d43f7fcb"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = response.json()
    return response['menuItems'][0]['title'], response['menuItems'][0]['image']


def find_calories(params):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/guessNutrition"
    querystring = {"title": ""}
    querystring['title'] = params
    headers = {
        'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        'x-rapidapi-key': "1530809090mshbd1bfa86ad13155p19a75djsn12b4d43f7fcb"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = response.json()
    return response['calories']['value']


def find_meal_plans(params, neg_params):
    import requests
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/mealplans/generate"
    querystring = {"timeFrame":"day","targetCalories":None,"diet":None,"exclude":None}
    for pa in params:
        querystring[pa] = params[pa]
    for pa in neg_params:
        querystring["exclude"] = neg_params[pa]
    #querystring["exclude"] = neg_params
    headers = {
        'x-rapidapi-host': "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        'x-rapidapi-key': "1530809090mshbd1bfa86ad13155p19a75djsn12b4d43f7fcb"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)
    response = response.json()
    result = []
    for res in response['meals']:
        result.append(res['title'])
    rate = response['nutrients']
    return result,params,neg_params,rate


def make_pie(rate):
    from matplotlib import pyplot as plt
    picture = plt.figure(figsize=(6,9))
    labels = []
    sizes = []
    response = None
    for ra in rate:
        if ra != 'calories':
            labels.append(ra)
            sizes.append(rate[ra])
        else:
            response = rate[ra]
    colors = ['pink','yellowgreen','skyblue']
    plt.pie(sizes,labels=labels,colors=colors,autopct='%2.0f%%')
    plt.axis('equal')
    plt.legend()
    plt.show()
    picture.savefig("pie.png")
    return response


def negated_ents(phrase, ent_vals):
    ents = [e for e in ent_vals if e in phrase]
    ends = sorted([phrase.index(e) + len(e) for e in ents])
    start = 0
    chunks = []
    for end in ends:
        chunks.append(phrase[start:end])
        start = end
    result = {}
    for chunk in chunks:
        for ent in ents:
            if ent in chunk:
                if "not" in chunk or "n't" in chunk:
                    result[ent] = False
                else:
                    result[ent] = True
    return result


# Define send_messages()

import string


# Define send_message()
def send_message(state, pending, message, params, flag, neg_params, rate):
    # print("USER : {}".format(message))
    intent = interpret(message)
    print(intent)
    response2 = None
    new_state, response, pending_state = policy_rules[(state, interpret(message))]
    if response != None and '{0}' in response:
        if state == CHOOSE_RESTAURANT:
            restaurant = find_restaurant(message)
            params = restaurant
            response = response.format(restaurant)
        elif state == DELIVERY:
            # doc = nlp(message)
            # food_kind = extract_food(doc)
            calori = find_calories(params)
            response = response.format(calori)
        elif state == ORDER_FOOD:
            food, response2 = find_food(params)
            response = response.format(food)

    else:
        if state == ORDER_FOOD:
            doc = nlp(message)
            food_kind = extract_food(doc)
            params = food_kind
    if intent == 'chat':
        response, phrase = match_rule(rules, message)
        # print("aaaaaa"+phrase)
        if '{0}' in response:
            # Replace the pronouns in the phrase
            phrase = replace_pronouns(phrase)
            # Include the phrase in the response
            response = response.format(phrase)
    if intent == 'pie':
        cal = make_pie(rate)
        response = "Here you are"
        return response, response2, new_state, pending, params, flag, neg_params, rate
    if intent == "meal_plan":
        # Extract the entities
        entities = interpreter.parse(message)["entities"]
        ent_vals = [e["value"] for e in entities]
        negated = negated_ents(message, ent_vals)
        for ent in entities:
            if ent["value"] in negated and not negated[ent["value"]]:
                neg_params[ent["entity"]] = str(ent["value"])
            else:
                params[ent["entity"]] = str(ent["value"])
        # Find the meal plan
        meal_plans, params, neg_params, rate = find_meal_plans(params, neg_params)
        n = min(len(meal_plans), 3)
        # Return the appropriate response
        return responses[n].format(*meal_plans), response2, new_state, pending, params, flag, neg_params, rate
    if intent == 'greet':
        response = 'Hello, I am glad to help you'
    elif intent == 'goodbye':
        response = 'See you!'

    if pending is not None and flag == False:
        new_state, response2, pending_state = policy_rules[pending]
        # print("BOT : {}".format(response))
        flag = True
    if pending_state is not None:
        pending = (pending_state, interpret(message))
    return response, response2, new_state, pending, params, flag, neg_params, rate

eats = ['drink', 'eat']
def entity_type(word):
    _type = None
    if word in eats:
        _type = "eat"
    return _type

def extract_food(doc):
    flag = False
    for word in doc:
        if flag == True:
            return word.text
        if entity_type(word.text) == "eat":
            flag = True
    return None


def interpret(message):
    msg = message.lower()
    intent = interpreter.parse(msg)["intent"]['name']
    mached = match_intent(msg)
    if mached != None:
        return mached
    elif any([d in msg for d in string.digits]) and intent != 'meal_plan':
        return 'number'
    else:
        return intent
    return 'none'


keywords = {
    'thankyou': ['thank', 'thanks', 'thx'],
    'goodbye': ['bye', 'see you', 'farewell']
}
# Define a dictionary of patterns
regular_intent = {}

# Iterate over the keywords dictionary
for intent, keys in keywords.items():
    # Create regular expressions and compile them into pattern objects
    regular_intent[intent] = re.compile("|".join(keys))


def match_intent(message):
    matched_intent = None
    for intent, pattern in regular_intent.items():
        # Check if the pattern occurs in the message
        if re.search(pattern, message):
            matched_intent = intent
    return matched_intent


def replace_pronouns(message):

    message = message.lower()
    if 'me' in message:
        # Replace 'me' with 'you'
        return message.replace('me','you')
    if 'my' in message:
        # Replace 'my' with 'your'
        return message.replace('my','your')
    if 'your' in message:
        # Replace 'your' with 'my'
        return message.replace('your','my')
    if 'you' in message:
        # Replace 'you' with 'me'
        return message.replace('you','me')
    if 'i ' in message:
        # Replace 'you' with 'me'
        return message.replace('i ','you ')

    return message


rules = {
    'do you remember (.*)': ['Did you think I would forget {0}',
                             "Why haven't you been able to forget {0}",
                             'What about {0}',
                             'Yes .. and?'],
    'if (.*)': ["Do you really think it's likely that {0}",
                'Do you wish that {0}',
                'What do you think about {0}',
                'Really--if {0}']
}


# Define match_rule()
def match_rule(rules, message):
    response, phrase = "default", None

    # Iterate over the rules dictionary
    for word in rules:
        # Create a match
        match = re.match(word, message, re.I)
        if match is not None:
            # Choose a random response
            response = random.choice(rules[word])
            if '{0}' in response:
                phrase = match[1]
    # Return the response and phrase
    return response, phrase


import telebot
import time
import urllib
from urllib import request

bot = telebot.TeleBot('971916109:AAESTSMLMfat5-8-wDWip5qj1BEMm7Nl164')

state = INIT
pending = None
params = {}
flag = False

params_2 = {}
neg_params = {}
rate = None

orderFood = False
rate = 0


@bot.message_handler()
def send_reply(message2):
    # Get the bot's response to the message
    message = message2.text
    intent = interpreter.parse(message)["intent"]['name']

    global state
    global pending
    global params
    global flag

    global params_2
    global neg_params
    global rate

    global orderFood
    response2 = None
    response, response2, state, pending, params, flag, neg_params, rate = send_message(state, pending, message, params,
                                                                                       flag, neg_params, rate)
    # response = respond(message.text)
    # print(type(message.text))
    # Print the bot template including the bot's response.
    # print(bot_template.format(response))
    bot.send_message(message2.chat.id, response)
    if intent == 'pie':
        bot.send_photo(message2.chat.id, photo=open("pie.png", "rb"))
    if response2 != None:
        if interpreter.parse(response2)["intent"]['name'] == 'url':
            f = open('pic.jpg', 'wb')
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}
            rep = request.Request(response2, headers=headers)
            f.write(urllib.request.urlopen(rep).read())
            f.close()
            bot.send_photo(message2.chat.id, photo=open('pic.jpg', "rb"))
        else:
            bot.send_message(message2.chat.id, response2)


bot.polling()