from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter, CallbackContext, Filters
from telegram import Update
from twython import Twython
from PIL import Image
from git import Repo
from datetime import datetime, timedelta
import requests
import imagehash
import shutil
import time
import re
import random
import locale
import os

# ENV FILES
etherscan_api_key = os.environ.get('ETH_API_KEY')
APP_KEY = os.environ.get('TWITTER_API_KEY')
APP_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
MEME_GIT_REPO = os.environ.get('MEME_GIT_REPO')
TMP_FOLDER = os.environ.get('TMP_MEME_FOLDER')

locale.setlocale(locale.LC_ALL, 'en_US')

re_4chan = re.compile(r'^rot |rot$| rot |rotten|rotting')

twitter = Twython(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_SECRET_TOKEN)

how_many_tweets = 5

# GIT INIT
repo = Repo(MEME_GIT_REPO)
assert not repo.bare
repo.config_reader()  # get a config reader for read-only access
with repo.config_writer():  # get a config writer to change configuration
    pass  # call release() to be sure changes are written and locks are released
assert not repo.is_dirty()  # check the dirty state


## UTIL
def format_tweet(tweet):
    tweet_id = tweet['id_str']
    url = "twitter.com/anyuser/status/" + tweet_id
    message = tweet['text'].replace("\n", "")
    
    time_tweet_creation = tweet['created_at']
    new_datetime = datetime.strptime(time_tweet_creation,'%a %b %d %H:%M:%S +0000 %Y')
    current_time = datetime.utcnow()
    diff_time = current_time - new_datetime
    minutessince = int(diff_time.total_seconds() / 60)
    
    user = tweet['user']['screen_name']
    message = str(minutessince) + " mins ago " + user + " -- " + "<a href=\"" + url + "\">" + message[0:100] + "</a> \n"
    return message


# scraps the github project to get those sweet memes. Will chose one randomly and send it.
def get_url_meme():
    contents = requests.get("https://api.github.com/repos/rottenswap/memes/contents/memesFolder").json()
    potential_memes = []
    for file in contents:
        if ('png' in file['name'] or 'jpg' in file['name'] or 'jpeg' in file['name'] or 'mp4' in file['name']):
            potential_memes.append(file['download_url'])
    url = random.choice(potential_memes)
    return url


def bop(update: Update, context: CallbackContext):
    url = get_url_meme()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


# tutorial on how to increase the slippage.
def how_to_slippage(update: Update, context: CallbackContext):
    url = "https://i.imgur.com/TVFhZML.png"
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


# Get the supply cache from etherscan. Uses the ETH_API_KEY passed as an env variable.
def get_supply_cap(update: Update, context: CallbackContext):
    rotAddr = 'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress=0xD04785C4d8195e4A54d9dEc3a9043872875ae9E2&apikey=' + etherscan_api_key
    maggotAddr = 'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress=0x163c754eF4D9C03Fc7Fa9cf6Dd43bFc760E6Ce89&apikey=' + etherscan_api_key
    decimals = 1000000000000000000
    request_rot = round(int(requests.post(rotAddr).json()['result']) / decimals)
    request_maggot = round(int(requests.post(maggotAddr).json()['result']) / decimals)
    number_rot = locale.format_string("%d", request_rot, grouping=True)
    number_maggots = locale.format_string("%d", request_maggot, grouping=True)
    message = "It's <b>ROTTING</b> around here! There are <pre>" + str(number_rot) + "</pre> ROTS and <pre>" + str(
        number_maggots) + "</pre> MAGGOTS"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')


# scraps /biz/ and returns a list of tuple (threadId, body, title) of threads matching the regex ^rot |rot$| rot |rotten|rotting
def get_biz_threads():
    url = 'https://a.4cdn.org/biz/catalog.json'
    json = requests.get(url).json()
    threads_ids = []
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
                # if(("rot" or "$rot" or "rotten" or "rotting") in (sub.lower() or com.lower())):
                if re_4chan.search(com.lower()) or re_4chan.search(sub.lower()):
                    id = thread['no']
                    threads_ids.append((id, com, sub))
    return threads_ids


# sends the current biz threads
def get_biz(update: Update, context: CallbackContext):
    threadsIds = get_biz_threads()

    baseUrl = "boards.4channel.org/biz/thread/"
    message = """Plz go bump the /biz/ threads:
"""
    for thread_id in threadsIds:
        excerpt = thread_id[2] + " | " + thread_id[1]
        message += baseUrl + str(thread_id[0]) + " -- " + excerpt[0: 100] + "[...] \n"
    if not threadsIds:
        chat_id = update.message.chat_id
        meme_url = get_url_meme()
        print("sent reminder 4chan /biz/")
        meme_caption = "There hasn't been a Rotten /biz/ thread for a while. Plz go make one https://boards.4channel.org/biz/, here's a meme, go make one."
        context.bot.send_photo(chat_id=chat_id, photo=meme_url, caption=meme_caption)
    else:
        chat_id = update.message.chat_id
        context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)


# sends the astrotools chart of the $ROT token
def chart(update: Update, context: CallbackContext):
    test = "https://app.astrotools.io/pair-explorer/0x5a265315520696299fa1ece0701c3a1ba961b888"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=test, disable_web_page_preview=True)


# sends the astrotools chart of the $MAGGOT token
def chart_maggot(update: Update, context: CallbackContext):
    test = "https://app.astrotools.io/pair-explorer/0x46ba95ff4f4cd9353eadde43bee519fa50886e72"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=test, disable_web_page_preview=True)


# uniswap page
def get_uniswap(update: Update, context: CallbackContext):
    test = """<b>$ROT</b> -> https://app.uniswap.org/#/swap?inputCurrency=0xd04785c4d8195e4a54d9dec3a9043872875ae9e2
<b>$MAGGOT</b> -> https://app.uniswap.org/#/swap?inputCurrency=0x163c754ef4d9c03fc7fa9cf6dd43bfc760e6ce89"""
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=test, parse_mode='html')


# tutorial on how to stake
def stake_command(update: Update, context: CallbackContext):
    text = """<b>How to stake/farm ROT :</b> 

1. Buy on Uniswap : https://app.uniswap.org/#/swap?inputCurrency=0xd04785c4d8195e4a54d9dec3a9043872875ae9e2

2. Make sure to add the ROT contract number in your wallet so your wallet can show your ROT coins (metamask etc)

3. Buy/transfer eth

4. Add Liquidity ...
...
See the full instructions on https://pastebin.pl/view/raw/3db66672"""
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html')


last_time_since_check = 0


# callback function that sends a reminder if no /biz/ threads are rooting
def callback_4chan_thread(update: Update, context: CallbackContext):
    job = context.job
    global last_time_since_check
    biz = get_biz_threads()
    if not biz:
        meme_url = get_url_meme()
        last_time_since_check += 15
        print("sending 4chan reminder, no post for " + str(last_time_since_check))
        meme_caption = "There hasn't been a Rotten /biz/ thread in the last " + str(
            last_time_since_check) + " minutes. Plz go make one https://boards.4channel.org/biz/, here's a meme."
        context.bot.send_photo(chat_id=job.context, photo=meme_url, caption=meme_caption)
        # context.bot.send_message(chat_id=job.context, text='No /biz/ threads for a while. Let\'s go make one!')
    else:
        last_time_since_check = 0


def callback_timer(update: Update, context: CallbackContext):
    job = context.job
    context.bot.send_message(chat_id=update.message.chat_id, text='gotcha')
    job.run_repeating(callback_4chan_thread, 900, context=update.message.chat_id)


def query_tweets(easy=True):
    if easy:
        return twitter.search(q='$ROT rottenswap')
    else:
        return twitter.search(q='$ROT')


def filter_tweets(all_tweets):
    message = ""
    if all_tweets.get('statuses'):
        count = 0
        tweets = all_tweets['statuses']
        for tweet in tweets:
            if "RT " not in tweet['text']:
                if count < how_many_tweets:
                    message = message + format_tweet(tweet)
                    count = count + 1
    return message


def get_last_tweets(update: Update, context: CallbackContext):
    results = query_tweets(False)
    message = "<b>Normies are tweeting about ROT, go comment/like/RT:</b>\n"
    rest_message = filter_tweets(results)
    if rest_message == "":
        print("empty tweets, fallback")
        results = query_tweets(False)
        rest_message = filter_tweets(results)
    full_message = message + rest_message
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=full_message, parse_mode='html', disable_web_page_preview=True)


### ADD MEME

def add_meme(update: Update, context: CallbackContext):
    print("received_image")

    try:
        caption = update['message']['caption']
        if caption == "/add_meme":
            try:
                image = context.bot.getFile(update.message.photo[0])
                file_id = str(image.file_id)
                print ("file_id: " + file_id)
                tmp_path = MEME_GIT_REPO + '/memesFolder/' + file_id + ".png"
                image.download(tmp_path)
                hash = calculate_hash(tmp_path)
                is_present = check_file_already_present(hash)
                if not is_present:
                    filename = hash + '.jpg'
                    copy_file_to_git_meme_folder(tmp_path, filename)
                    add_file_to_git(filename)
                    chat_id = update.message.chat_id
                    context.bot.send_message(chat_id=chat_id, text="Got it boss!")
                else:
                    chat_id = update.message.chat_id
                    context.bot.send_message(chat_id=chat_id, text="Image already registered")
            except IndexError:
                error_msg = "Adding image failed: no image provided. Make sure to send it as a file and not an image."
                chat_id = update.message.chat_id
                context.bot.send_message(chat_id=chat_id, text=error_msg)
    except KeyError:
        a = 1



def copy_file_to_git_meme_folder(path, hash_with_extension):
    shutil.copyfile(path, MEME_GIT_REPO + '/memesFolder/' + hash_with_extension)

def calculate_hash(path_to_image):
    return str(imagehash.average_hash(Image.open(path_to_image)))

def add_file_to_git(filename):
    index = repo.index
    index.add(MEME_GIT_REPO + "/memesFolder/" + filename)
    index.commit("adding dank meme " + filename)
    origin = repo.remote('origin')
    origin.push()


# Returns True if the file is already present in the MEME_GIT_REPO directory
def check_file_already_present(hash):
    found = False
    for file in os.listdir(MEME_GIT_REPO + '/memesFolder/'):
        filename = os.fsdecode(file)
        filename_no_extension = filename.split(".")[0]
        if filename_no_extension == hash:
            found = True
    return found


def main():
    updater = Updater('1240870832:AAGFH0uk-vqk8de07pQV9OAQ1Sk9TN8auiE', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('rotme', bop))
    dp.add_handler(CommandHandler('rottedChart', chart))
    dp.add_handler(CommandHandler('maggotChart', chart_maggot))
    dp.add_handler(CommandHandler('rotfarmingguide', stake_command))
    dp.add_handler(CommandHandler('howtoslippage', how_to_slippage))
    dp.add_handler(CommandHandler('getuniswap', get_uniswap))
    dp.add_handler(CommandHandler('supplycap', get_supply_cap))
    dp.add_handler(CommandHandler('4biz', get_biz))
    dp.add_handler(CommandHandler('twitter', get_last_tweets))
    dp.add_handler(MessageHandler(Filters.photo, add_meme))
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
add_meme - Add a meme to the common memes folder
"""

