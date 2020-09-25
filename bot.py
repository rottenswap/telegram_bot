from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter
from twython import Twython
import requests
import time
import re
import random
import locale
import os

etherscan_api_key = os.environ.get('ETH_API_KEY')
APP_KEY = os.environ.get('TWITTER_API_KEY')
APP_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
locale.setlocale(locale.LC_ALL, 'en_US')

re_4chan = re.compile(r'^rot |rot$| rot |rotten|rotting')

twitter = Twython(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_SECRET_TOKEN)

how_many_tweets = 3


## UTIL
def format_tweet(tweet):
    tweet_id = tweet['id_str']
    url = "twitter.com/anyuser/status/" + tweet_id
    message = tweet['text'].replace("\n", "")
    user = tweet['user']['screen_name']
    message = user + " -- " + "<a href=\"" + url + "\">" + message[0:100] + "</a> \n"
    return message

# scraps the github project to get those sweet memes. Will chose one randomly and send it.
def get_url_meme():
    contents=requests.get("https://api.github.com/repos/rottenswap/rottenswap.org-website/contents/docs/memes").json()
    potential_memes = []
    for file in contents:
        if ('png' in file['name'] or 'jpg' in file['name'] or 'jpeg' in file['name'] or 'mp4' in file['name']):
            potential_memes.append(file['download_url'])
    url = random.choice(potential_memes)
    return url

def bop(bot, update):
    url = get_url_meme()
    chat_id = update.message.chat_id
    bot.send_photo(chat_id=chat_id, photo=url)

# tutorial on how to increase the slippage.
def howtoslippage(bot, update):
    url = "https://i.imgur.com/TVFhZML.png"
    chat_id = update.message.chat_id
    bot.send_photo(chat_id=chat_id, photo=url)

# Get the supply cache from etherscan. Uses the ETH_API_KEY passed as an env variable.
def getSupplyCap(bot, update):
    rotAddr = 'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress=0xD04785C4d8195e4A54d9dEc3a9043872875ae9E2&apikey=' + etherscan_api_key
    maggotAddr = 'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress=0x163c754eF4D9C03Fc7Fa9cf6Dd43bFc760E6Ce89&apikey=' + etherscan_api_key
    decimals = 1000000000000000000
    request_rot=round(int(requests.post(rotAddr).json()['result']) / decimals)
    request_maggot=round(int(requests.post(maggotAddr).json()['result']) / decimals)
    number_rot = locale.format_string("%d", request_rot, grouping=True)
    number_maggots = locale.format_string("%d", request_maggot, grouping=True)
    message = "It's <b>ROTTING</b> around here! There are <pre>" + str(number_rot) + "</pre> ROTS and <pre>" + str(number_maggots) + "</pre> MAGGOTS"
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=message, parse_mode='html')

# scraps /biz/ and returns a list of tuple (threadId, body, title) of threads matching the regex ^rot |rot$| rot |rotten|rotting
def getBizThreads():
    url = 'https://a.4cdn.org/biz/catalog.json'
    json = requests.get(url).json()
    threadsIds = []
    for page in json:
        for thread in page['threads']:
            try:                
                if 'com' in thread:
                    com = thread['com']
                else:
                    com = ""
                if 'sub' in thread:
                    sub = thread['sub']
                else:
                    sub = ""
            except KeyError:
                print("ERROR")
                pass
            else:
                #if(("rot" or "$rot" or "rotten" or "rotting") in (sub.lower() or com.lower())):
                if (re_4chan.search(com.lower()) or re_4chan.search(sub.lower())):
                    id = thread['no']
                    threadsIds.append((id, com, sub))
    return threadsIds

# sends the current biz threads
def getBiz(bot, update):
    threadsIds = getBizThreads()

    baseUrl = "boards.4channel.org/biz/thread/"
    message = """Plz go bump the /biz/ threads:
"""
    for thread_id in threadsIds:
        excerpt = thread_id[2] + " | " + thread_id[1]
        message+=baseUrl + str(thread_id[0]) + " -- " + excerpt[0: 100] + "[...] \n"
    if not threadsIds:
        chat_id = update.message.chat_id
        meme_url = get_url_meme()
        print("sent reminder 4chan /biz/")
        meme_caption = "There hasn't been a Rotten /biz/ thread for a while. Plz go make one https://boards.4channel.org/biz/, here's a meme, go make one."
        bot.send_photo(chat_id=chat_id, photo=meme_url, caption=meme_caption)
    else:
        chat_id = update.message.chat_id
        bot.send_message(chat_id=chat_id, text=message)


# sends the astrotools chart of the $ROT token
def chart(bot, update):
    test = "https://app.astrotools.io/pair-explorer/0x5a265315520696299fa1ece0701c3a1ba961b888"
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=test)

# sends the astrotools chart of the $MAGGOT token
def chartMaggot(bot, update):
    test = "https://app.astrotools.io/pair-explorer/0x46ba95ff4f4cd9353eadde43bee519fa50886e72"
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=test)

# uniswap page
def getuniswap(bot, update):
    test = """<b>$ROT</b> -> https://app.uniswap.org/#/swap?inputCurrency=0xd04785c4d8195e4a54d9dec3a9043872875ae9e2
<b>$MAGGOT</b> -> https://app.uniswap.org/#/swap?inputCurrency=0x163c754ef4d9c03fc7fa9cf6dd43bfc760e6ce89"""
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=test, parse_mode='html')

# tutorial on how to stake
def stakeCommand(bot, update):
    text = """<b>How to stake/farm ROT :</b> 

1. Buy on Uniswap : https://app.uniswap.org/#/swap?inputCurrency=0xd04785c4d8195e4a54d9dec3a9043872875ae9e2

2. Make sure to add the ROT contract number in your wallet so your wallet can show your ROT coins (metamask etc)

3. Buy/transfer eth

4. Add Liquidity ...
...
See the full instructions on https://pastebin.pl/view/raw/3db66672"""
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=text, parse_mode='html')

last_time_since_check = 0

# callback function that sends a reminder if no /biz/ threads are rooting
def callback_4chan_thread(bot, job):
    global last_time_since_check
    biz = getBizThreads()
    if not biz:
        meme_url = get_url_meme()
        last_time_since_check += 15
        print("sending 4chan reminder, no post for " + str(last_time_since_check))
        meme_caption = "There hasn't been a Rotten /biz/ thread in the last " + str(last_time_since_check) + " minutes. Plz go make one https://boards.4channel.org/biz/, here's a meme."
        bot.send_photo(chat_id=job.context, photo=meme_url, caption=meme_caption)
        #bot.send_message(chat_id=job.context, text='No /biz/ threads for a while. Let\'s go make one!')
    else:
        last_time_since_check = 0
    

def callback_timer(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id, text='gotcha')
    job_queue.run_repeating(callback_4chan_thread, 900, context=update.message.chat_id)
    

def getLastTweets(bot, update):
    results = twitter.search(q='$ROT')
    message = "Ppl are tweeting about ROT, go comment/like/RT: \n"
    if results.get('statuses'):
        count = 0
        tweets = results['statuses']
        for tweet in tweets:
            if ("RT " not in tweet['text']):
                if (count < how_many_tweets):
                    message = message + format_tweet(tweet)
                    count = count + 1
    chat_id = update.message.chat_id
    bot.send_message(chat_id=chat_id, text=message, parse_mode='html')



def main():
    updater = Updater('1240870832:AAGFH0uk-vqk8de07pQV9OAQ1Sk9TN8auiE')
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('rotme',bop))
    dp.add_handler(CommandHandler('rottedChart', chart))
    dp.add_handler(CommandHandler('maggotChart',chartMaggot))
    dp.add_handler(CommandHandler('rotfarmingguide',stakeCommand))
    dp.add_handler(CommandHandler('howtoslippage',howtoslippage))
    dp.add_handler(CommandHandler('getuniswap',getuniswap))
    dp.add_handler(CommandHandler('supplycap',getSupplyCap))
    dp.add_handler(CommandHandler('4biz',getBiz))
    dp.add_handler(CommandHandler('twitter',getLastTweets))
    updater.dispatcher.add_handler(CommandHandler('startBiz', callback_timer, pass_job_queue=True))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

commands = """
rotme - Give me a random meme
rottedchart - Get the charts of $ROT
maggotchart - Get the charts of $MAGGOTS
rotfarmingguide - Guide to $ROT farming
howtoslippage - How to increase slippage
getuniswap - Get the uniswap pages
supplycap - How ROTTED are we
4biz - List biz thread
twitter - List twitter threads
"""


