# AI-Chat-Bot
* Use some natural language processing knowledge to bulid a chat bot in Telegram
* This bot can chat with fun, order food delivery and make a meal plan regarding certain calories

## Demo - Video
You can also see this video in [YouTuBe](https://youtu.be/TL2TMgcRpvk)

![Image text](https://github.com/HehuiGu/AI-Chat-Bot/blob/master/DEMO-VIDEO1.gif)
![Image text](https://github.com/HehuiGu/AI-Chat-Bot/blob/master/DEMO-VIDEO2.gif)
![Image text](https://github.com/HehuiGu/AI-Chat-Bot/blob/master/DEMO-VIDEO3.gif)

## Prerequisites
* Python == 3.6.8
* You also need to install some packages:
rasa_nlu, spacy, pandas, random, re, requests, matplotlib, time, telebot, urllib
```
pip install spacy --target=<your site package locate in>
```
* Install en-core-web-md module
```
python -m spacy download en_core_web_md
```
* Download OrderFood_ControlCalories.py, config_spacy.yml, train_calorie.json from this web page to the same directory.
  * OrderFood_ControlCalories.py
  * config_spacy.yml
  * train_calorie.json
  
## Running Telebot
* Download telebot APP and create your own account
* Send '/start' to BotFather and follow the instructions to create your own bot
* Use your own token to fill in the code here in OrderFood_ControlCalories.py
```
bot = telebot.TeleBot('YOUR TOKEN')
```
* Activate your enviroment and run OrderFood_ControlCalories.py
* Send messages to your bot in Telegram App

## Contact
If you have any question, please feel free to contact with me
My email: guhehui0206@163.com or 271204788@qq.com
