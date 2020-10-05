from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter, \
    CallbackContext, Filters
from telegram import Update
from twython import Twython, TwythonError
from graphqlclient import GraphQLClient
from PIL import Image
from git import Repo
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.pyplot
import csv
import requests
import imagehash
import shutil
import time
import re
import random
import locale
import os
import json
from bot_util import RepeatedTimer
from images import Ocr
import plotly.graph_objects as go
import pprint

# ENV FILES
etherscan_api_key = os.environ.get('ETH_API_KEY')
APP_KEY = os.environ.get('TWITTER_API_KEY')
APP_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
MEME_GIT_REPO = os.environ.get('MEME_GIT_REPO')
TMP_FOLDER = os.environ.get('TMP_MEME_FOLDER')
BASE_PATH = os.environ.get('BASE_PATH')

test_error_token = "Looks like you need to either: increase slippage (see /howtoslippage) and/or remove the decimals from the amount of ROT you're trying to buy"

# Graph QL requests
req_graphql_rot = '''{token(id: "0xd04785c4d8195e4a54d9dec3a9043872875ae9e2") {derivedETH}}'''
req_graphql_maggot = '''{
swaps(
    first: 1, 
    where: { pair: "0x5cfd4ee2886cf42c716be1e20847bda15547c693" } 
    orderBy: timestamp, 
    orderDirection: desc) 
    {transaction 
      {id timestamp}
      id
      pair {
        token0 
            {id symbol}
        token1 
            {id symbol}}
         amount0In 
         amount0Out 
         amount1In 
         amount1Out  
 }}'''
req_graphql_usdt = '''{token(id: "0xdac17f958d2ee523a2206206994597c13d831ec7") {derivedETH}}'''
graphql_client = GraphQLClient('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2')

# log_file
price_file_path = BASE_PATH + 'rot/log_files/price_hist.txt'
supply_file_path = BASE_PATH + 'rot/log_files/supply_hist.txt'
chart_price_file_path = BASE_PATH + 'rot/log_files/chart_price.png'
chart_supply_file_path = BASE_PATH + 'rot/log_files/chart_supply.png'
candels_file_path = BASE_PATH + 'rot/log_files/chart_candles.png'

locale.setlocale(locale.LC_ALL, 'en_US')

# API PROPOSAL
api_proposal_url = 'https://rotapi.xyz/governance/getProposals'
last_proposal_received_id = -1
telegram_governance_url = 't.me/rottengovernance'
rotten_main_chat_id = -1001382715556
last_time_checked_price_chart = round(time.time())
last_time_checked_price_candles = round(time.time())
last_time_checked_price_supply = round(time.time())
last_time_checked_4chan = round(time.time())
last_time_checked_twitter = round(time.time())

re_4chan = re.compile(r'^rot |rot$| rot |rotten|rotting')

twitter = Twython(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_SECRET_TOKEN)

how_many_tweets = 5

## CONTRACT
rot_contract = '0xD04785C4d8195e4A54d9dEc3a9043872875ae9E2'
maggot_contract = '0x163c754eF4D9C03Fc7Fa9cf6Dd43bFc760E6Ce89'

# messages
rot_101_text = '''<br>ROT IN A NUTSHELL

$ROT is a deflationary token. 
In each $ROT transaction 2.5% is burned into $MAGGOTS. 

> IF the transaction is BUY:
The 2.5% will be converted into MAGGOTS and deposited into your wallet.

> IF the transaction is SELL:
The 2.5% will be converted into MAGGOTS and deposited in the $MAGGOT warehouse. Basically, when you sell, 2.5% of $ROT is burned, but you don't get $MAGGOT.

> DEFLATION VS. INFLATION
$ROT is a deflationary token. Pools generate 100 new ROTs in each block.If there are enough buy/sell transactions of $ROT, even if 100ROT/block are created, it will still be deflationary. 

If there are enough buy/sell transactions of $ROT, even if 100ROT/block are created, $ROT will still be deflationary. 

If there were not enough transactions, $ROT would increase its amount. 

The $MAGGOTS are inflationary. These tokens are initially worthless but now have some value due to the liquidity of the pools. $MAGGOT is usually used to stake the ROT-MAGGOT pair or to exchange them for $ROT, but you can do with them whatever you want.'''

url_website = 'rottenswap.org'
url_uniswap_rot = 'https://app.uniswap.org/#/swap?inputCurrency=0xd04785c4d8195e4a54d9dec3a9043872875ae9e2'
url_uniswap_maggot = 'https://app.uniswap.org/#/swap?inputCurrency=0x163c754ef4d9c03fc7fa9cf6dd43bfc760e6ce89'
url_uniswap_pool_rot_eht = 'https://app.uniswap.org/#/add/ETH/0xD04785C4d8195e4A54d9dEc3a9043872875ae9E2'
url_uniswap_pool_rot_maggot = 'https://app.uniswap.org/#/add/0x163c754eF4D9C03Fc7Fa9cf6Dd43bFc760E6Ce89/0xD04785C4d8195e4A54d9dEc3a9043872875ae9E2'
url_etherscan_rot = 'https://etherscan.io/token/0xd04785c4d8195e4a54d9dec3a9043872875ae9e2'
url_etherscan_maggot = 'https://etherscan.io/token/0x163c754ef4d9c03fc7fa9cf6dd43bfc760e6ce89'
url_astrotools_rot = 'https://app.astrotools.io/pair-explorer/0x5a265315520696299fa1ece0701c3a1ba961b888'
url_dextools_rot = 'https://www.dextools.io/app/uniswap/pair-explorer/0x5a265315520696299fa1ece0701c3a1ba961b888'
url_coingecko_rot = 'https://www.coingecko.com/en/coins/rotten'
url_livecoinwatch_rot = 'https://www.livecoinwatch.com/price/Rotten-ROT'
url_twitter_rottenswap = 'https://twitter.com/rottenswap'
url_reddit_rottenswap = 'https://www.reddit.com/r/RottenSwap/'
url_coinmarketcap = 'https://coinmarketcap.com/currencies/rotten/'
url_merch_site1 = 'https://rottenswag.com/'
url_merch_site2 = 'https://rottenmerch.launchcart.store/shop'


def create_href_str(url, message):
    return "<a href=\"" + url + "\">" + message + "</a>"


links = '<b>Website:</b> ' + create_href_str(url_website, 'rottenswap.org') + '\n' \
        + '<b>Uniswap:</b> ' + create_href_str(url_uniswap_rot, "$ROT") + " " + create_href_str(url_uniswap_maggot,
                                                                                                '$MAGGOT') + '\n' \
        + '<b>Pools:</b> ' + create_href_str(url_uniswap_pool_rot_eht, 'ROT-ETH') + ' ' + create_href_str(
    url_uniswap_pool_rot_maggot, 'ROT-MAGGOT') + '\n' \
        + '<b>Etherscan:</b> ' + create_href_str(url_etherscan_rot, '$ROT') + " " + create_href_str(
    url_etherscan_maggot, '$MAGGOT') + '\n' \
        + '<b>Charts:</b> ' + create_href_str(url_astrotools_rot, 'Astrotools') + ' ' + create_href_str(
    url_dextools_rot, 'DexTools') + ' ' \
        + create_href_str(url_coingecko_rot, 'CoinGecko') + ' ' + create_href_str(url_livecoinwatch_rot,
                                                                                  'LiveCoinWatch') + ' ' + create_href_str(
    url_coinmarketcap, 'CoinMarketCap') + '\n' \
        + '<b>Social medias: </b>' + create_href_str(url_twitter_rottenswap, 'Twitter') + ' ' + create_href_str(
    url_reddit_rottenswap, 'Reddit') + '\n' \
        + '<b>Merch: </b>' + create_href_str(url_merch_site1, 'RottenSwag') + ' ' + create_href_str(url_merch_site2,
                                                                                                    'RottenMerch') + '\n' \
        + '<b>Telegram groups:</b> @rottengovernance @rottenhelpgroup @RottenHalloween @RottenNFTs @ROTGamblingDapp'

# GIT INIT
repo = Repo(MEME_GIT_REPO)
assert not repo.bare
repo.config_reader()  # get a config reader for read-only access
with repo.config_writer():  # get a config writer to change configuration
    pass  # call release() to be sure changes are written and locks are released
assert not repo.is_dirty()  # check the dirty state


# UTIL
def format_tweet(tweet):
    tweet_id = tweet['id_str']
    url = "twitter.com/anyuser/status/" + tweet_id
    message = tweet['text'].replace("\n", "").split('https')[0].replace('#', '').replace('@', '')

    time_tweet_creation = tweet['created_at']
    new_datetime = datetime.strptime(time_tweet_creation, '%a %b %d %H:%M:%S +0000 %Y')
    current_time = datetime.utcnow()
    diff_time = current_time - new_datetime
    minutessince = int(diff_time.total_seconds() / 60)

    user = tweet['user']['screen_name']
    message_final = "<a href=\"" + url + "\"><b>" + str(
        minutessince) + " mins ago</b> | " + user + "</a> -- " + message + "\n"
    return message_final


# scraps the github project to get those sweet memes. Will chose one randomly and send it.
def get_url_meme():
    contents = requests.get("https://api.github.com/repos/rottenswap/memes/contents/memesFolder").json()
    potential_memes = []
    for file in contents:
        if ('png' in file['name'] or 'jpg' in file['name'] or 'jpeg' in file['name'] or 'mp4' in file['name']):
            potential_memes.append(file['download_url'])
    url = random.choice(potential_memes)
    return url


def send_meme_to_chat(update: Update, context: CallbackContext):
    url = get_url_meme()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


# tutorial on how to increase the slippage.
def how_to_slippage(update: Update, context: CallbackContext):
    url = "https://i.imgur.com/TVFhZML.png"
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


def get_supply_cap_raw(contract_addr):
    base_addr = 'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress=' + contract_addr + '&apikey=' + etherscan_api_key
    decimals = 1000000000000000000
    supply_cap = round(int(requests.post(base_addr).json()['result']) / decimals)
    return supply_cap


# convert int to nice string: 1234567 => 1.234.567
def number_to_beautiful(nbr):
    return locale.format_string("%d", nbr, grouping=True)


# Get the supply cache from etherscan. Uses the ETH_API_KEY passed as an env variable.
def get_supply_cap(update: Update, context: CallbackContext):
    number_rot = number_to_beautiful(get_supply_cap_raw(rot_contract))
    number_maggots = number_to_beautiful(get_supply_cap_raw(maggot_contract))
    message = "It's <b>ROTTING</b> around here! There are <pre>" + str(number_rot) + "</pre> ROTS and <pre>" + str(
        number_maggots) + "</pre> MAGGOTS"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')


# scraps /biz/ and returns a list of tuple (threadId, body, title) of threads matching the regex ^rot |rot$| rot |rotten|rotting
def get_biz_threads():
    url = 'https://a.4cdn.org/biz/catalog.json'
    response_json = requests.get(url).json()
    threads_ids = []
    for page in response_json:
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
    global last_time_checked_4chan
    chat_id = update.message.chat_id
    new_time = round(time.time())
    if new_time - last_time_checked_4chan > 60:
        last_time_checked_4chan = new_time
        threads_ids = get_biz_threads()

        base_url = "boards.4channel.org/biz/thread/"
        message = """Plz go bump the /biz/ threads:
"""
        for thread_id in threads_ids:
            excerpt = thread_id[2] + " | " + thread_id[1]
            message += base_url + str(thread_id[0]) + " -- " + excerpt[0: 100] + "[...] \n"
        if not threads_ids:
            meme_url = get_url_meme()
            print("sent reminder 4chan /biz/")
            meme_caption = "There hasn't been a Rotten /biz/ thread for a while. Plz go make one https://boards.4channel.org/biz/, here's a meme, go make one."
            context.bot.send_photo(chat_id=chat_id, photo=meme_url, caption=meme_caption)
        else:
            context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text='Only checking 4chan/twitter/charts once per minute. Don\'t spam.')


# sends the main links
def get_links(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=links, disable_web_page_preview=True, parse_mode='html')


# tutorial on how to stake
def stake_command(update: Update, context: CallbackContext):
    text = """<b>How to stake/farm ROT :</b> 

1. Buy on Uniswap : https://app.uniswap.org/#/swap?inputCurrency=0xd04785c4d8195e4a54d9dec3a9043872875ae9e2

2. Make sure to add the ROT contract number in your wallet so your wallet can show your ROT coins (metamask etc)

3. Buy/transfer eth

4. Add Liquidity ...
...
See the full instructions on https://medium.com/@rotted_ben/how-to-stake-on-rottenswap-5c71bdf57390"""
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode='html', disable_web_page_preview=True)


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
    print("CHAT ID:" + str(update.message.chat_id))
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
    global last_time_checked_twitter
    chat_id = update.message.chat_id
    new_time = round(time.time())
    if new_time - last_time_checked_twitter > 60:
        last_time_checked_twitter = new_time
        try:
            results = query_tweets(False)
        except TwythonError:
            time.sleep(0.5)
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
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text='Only checking 4chan/twitter/charts once per minute. Don\'t spam.')


def download_image(update: Update, context: CallbackContext):
    image = context.bot.getFile(update.message.photo[-1])
    file_id = str(image.file_id)
    print("file_id: " + file_id)
    img_path = MEME_GIT_REPO + '/memesFolder/' + file_id + ".png"
    image.download(img_path)
    return img_path


# ADD MEME or PERFORM OCR to see if request to increase slippage
def handle_new_image(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    try:
        caption = update['message']['caption']
        if caption == "/add_meme":
            try:
                tmp_path = download_image(update, context)
                img_hash = calculate_hash(tmp_path)
                is_present = check_file_already_present(img_hash)
                if not is_present:
                    filename = img_hash + '.jpg'
                    copy_file_to_git_meme_folder(tmp_path, filename)
                    add_file_to_git(filename)
                    context.bot.send_message(chat_id=chat_id, text="Got it boss!")
                else:
                    context.bot.send_message(chat_id=chat_id, text="Image already registered")
            except IndexError:
                error_msg = "Adding image failed: no image provided. Make sure to send it as a file and not an image."
                context.bot.send_message(chat_id=chat_id, text=error_msg)
        else:
            try:
                tmp_path = download_image(update, context)
                ocr = Ocr(tmp_path)
                text_in_ocr = ocr.start_ocr().replace('\n', ' ')
                print("recognized text = " + text_in_ocr)
                if ('transaction cannot succeed' and 'one of the tokens' in text_in_ocr) or ('transaction will not succeed' and 'price movement or' in text_in_ocr):
                    context.bot.send_message(chat_id=chat_id, text=test_error_token)
            except IndexError:
                pass
    except KeyError:
        try:
            tmp_path = download_image(update, context)
            ocr = Ocr(tmp_path)
            text_in_ocr = ocr.start_ocr().replace('\n', ' ')
            print("recognized text = " + text_in_ocr)
            if ('transaction cannot succeed' and 'one of the tokens' in text_in_ocr) or ('transaction will not succeed' and 'price movement or' in text_in_ocr):
                context.bot.send_message(chat_id=chat_id, text=test_error_token)
        except IndexError:
            pass


def copy_file_to_git_meme_folder(path, hash_with_extension):
    shutil.copyfile(path, MEME_GIT_REPO + '/memesFolder/' + hash_with_extension)


def calculate_hash(path_to_image):
    return str(imagehash.average_hash(Image.open(path_to_image)))


def add_file_to_git(filename):
    index = repo.index
    index.add(MEME_GIT_REPO + "/memesFolder/" + filename)
    index.commit("adding dank meme " + filename)
    origin = repo.remote('origin')
    origin.push(force=True)


# Returns True if the file is already present in the MEME_GIT_REPO directory
def check_file_already_present(meme_hash):
    found = False
    for file in os.listdir(MEME_GIT_REPO + '/memesFolder/'):
        filename = os.fsdecode(file)
        filename_no_extension = filename.split(".")[0]
        if filename_no_extension == meme_hash:
            found = True
    return found


# REMOVE MEME
def delete_meme(update: Update, context: CallbackContext):
    query_received = update.message.text.split(' ')
    if len(query_received) == 3:
        print("someone wants to delete a meme")
        password = query_received[1]
        if password == "adbe5443-3bed-4230-a2e7-a94c8a8401ef":
            print("password correct")
            to_delete = query_received[2]
            if check_file_already_present(to_delete):
                print("meme found")
                filename = to_delete + '.jpg'
                index = repo.index
                index.remove(MEME_GIT_REPO + "/memesFolder/" + filename)
                index.commit("adding dank meme " + filename)
                origin = repo.remote('origin')
                origin.push(force=True)
                os.remove(MEME_GIT_REPO + "/memesFolder/" + filename)
                print("deleting meme " + to_delete)
                chat_id = update.message.chat_id
                context.bot.send_message(chat_id=chat_id, text="removed" + filename)


# graphql queries

def get_price_rot_raw():
    resp_rot = graphql_client.execute(req_graphql_rot)
    resp_usdt = graphql_client.execute(req_graphql_usdt)

    json_resp_rot = json.loads(resp_rot)
    json_resp_usdt = json.loads(resp_usdt)

    eth_per_rot = float(json_resp_rot['data']['token']['derivedETH'])
    eth_per_usdt = float(json_resp_usdt['data']['token']['derivedETH'])

    dollar_per_rot = eth_per_rot / eth_per_usdt

    return (eth_per_rot, dollar_per_rot)


# return the amount of maggot per rot
def get_ratio_rot_per_maggot(last_swaps_maggot_rot_pair):
    pprint.pprint(last_swaps_maggot_rot_pair['data'])
    pprint.pprint(last_swaps_maggot_rot_pair['data']['swaps'])
    pprint.pprint(last_swaps_maggot_rot_pair['data']['swaps'][0])
    interesting_part = last_swaps_maggot_rot_pair['data']['swaps'][0]
    last_swaps_amount_maggot_in = float(interesting_part['amount0In'])
    last_swaps_amount_maggot_out = float(interesting_part['amount0Out'])
    last_swaps_amount_rot_in = float(interesting_part['amount1In'])
    last_swaps_amount_rot_out = float(interesting_part['amount1Out'])
    # check which direction the transaction took place. For that, if amount1In = 0, it was maggot -> rot
    transaction_direction_maggot_to_rot = (last_swaps_amount_rot_in == 0)
    if transaction_direction_maggot_to_rot:
        return last_swaps_amount_rot_out / last_swaps_amount_maggot_in
    else:
        return last_swaps_amount_rot_in / last_swaps_amount_maggot_out


def get_price_maggot_raw():
    resp_maggot = graphql_client.execute(req_graphql_maggot)

    rot_per_maggot = get_ratio_rot_per_maggot(json.loads(resp_maggot))

    (eth_per_rot, dollar_per_rot) = get_price_rot_raw()

    dollar_per_maggot = rot_per_maggot / dollar_per_rot
    eth_per_maggot = eth_per_rot / rot_per_maggot

    return eth_per_maggot, dollar_per_maggot, rot_per_maggot


def get_price_maggot(update: Update, context: CallbackContext):
    (eth_per_maggot, dollar_per_maggot, rot_per_maggot) = get_price_maggot_raw()

    supply_cap_maggot = get_supply_cap_raw(maggot_contract)
    supply_cat_pretty = number_to_beautiful(supply_cap_maggot)
    market_cap = number_to_beautiful(int(float(supply_cap_maggot) * dollar_per_maggot))

    message = "<pre>ETH: Ξ" + str(eth_per_maggot)[0:10] \
              + "\nUSD: $" + str(dollar_per_maggot)[0:10] \
              + "\nROT: R" + str(rot_per_maggot)[0:10] \
              + "\nsupply cap: " + supply_cat_pretty \
              + "\nmarket cap: $" + market_cap + "</pre>"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')


def get_price_rot(update: Update, context: CallbackContext):
    (eth_per_rot, dollar_per_rot) = get_price_rot_raw()

    supply_cap_rot = get_supply_cap_raw(rot_contract)
    supply_cat_pretty = number_to_beautiful(supply_cap_rot)
    market_cap = number_to_beautiful(int(float(supply_cap_rot) * dollar_per_rot))

    message = "<pre>ETH: Ξ" + str(eth_per_rot)[0:10] \
              + "\nUSD: $" + str(dollar_per_rot)[0:10] \
              + "\nsupply cap: " + supply_cat_pretty \
              + "\nmarket cap: $" + market_cap + "</pre>"
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')


def log_current_price_rot_per_usd():
    global price_file_path
    (eth_per_rot, dollar_per_rot) = get_price_rot_raw()
    with open(price_file_path, "a") as price_file:
        time_now = datetime.now()
        date_time_str = time_now.strftime("%m/%d/%Y,%H:%M:%S")
        message_to_write = date_time_str + " " + str(dollar_per_rot) + "\n"
        price_file.write(message_to_write)


def log_current_supply():
    global supply_file_path
    number_rot = get_supply_cap_raw(rot_contract)
    number_maggots = get_supply_cap_raw(maggot_contract)
    with open(supply_file_path, "a") as supply_file:
        time_now = datetime.now()
        date_time_str = time_now.strftime("%m/%d/%Y,%H:%M:%S")
        message_to_write = date_time_str + " " + str(number_rot) + " " + str(number_maggots) + "\n"
        supply_file.write(message_to_write)


def get_help(update: Update, context: CallbackContext):
    message = "Technical issues? A question? Need help? Join the guys at @rottenhelpgroup."
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message)


def get_fake_price(update: Update, context: CallbackContext):
    message = '''<pre>FOR LEGAL REASONS THAT'S FAKE PRICE
(ROT) RottenToken
ETH: Ξ0.01886294
USD: $6.66000000
24H:   66%
7D :  666%

Vol 24H = $6 666 666
1 ETH   = 53 ROT
Holders = 6666
Con.Adr = 0xd04...9e2
@allUniSwapListings</pre>'''
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')


# def check_new_proposal(update: Update, context: CallbackContext):
#     global last_proposal_received_id
#     global last_time_checked
#
#     new_time = round(time.time())
#     if new_time - last_time_checked > 60:
#         pass
# print("Checking for new proposals...")
# log_current_price_rot_per_usd()
# log_current_supply()
# last_time_checked = new_time
# response_json = requests.get(api_proposal_url).json()
# if response_json != "" or response_json is not None:
#     last_proposal = response_json[-1]
#     id_last_proposal = last_proposal['id']
#     if last_proposal_received_id == -1:  # check if the bot just initialized
#         last_proposal_received_id = id_last_proposal
#     else:
#         if id_last_proposal > last_proposal_received_id:
#             last_proposal_received_id = id_last_proposal
#             proposal_title = last_proposal['title']
#             description = last_proposal['description']
#             message = 'New proposal added: <b>' + proposal_title + '</b>\n' \
#                       + description + '\nGo vote at ' \
#                       + telegram_governance_url
#             print("New proposal found and sent")
#             context.bot.send_message(chat_id=rotten_main_chat_id, text=message, parse_mode='html')


def get_from_query(query_received):
    time_type = query_received[2]
    time_start = int(query_received[1])
    if time_start < 0:
        time_start = - time_start
    k_hours = 0
    k_days = 0
    if time_type == 'h' or time_type == 'H':
        k_hours = time_start
    if time_type == 'd' or time_type == 'D':
        k_days = time_start
    return time_type, time_start, k_hours, k_days


def strp_date(raw_date):
    return datetime.strptime(raw_date, '%m/%d/%Y,%H:%M:%S')


# util for get_chart_pyplot
def keep_dates(values_list):
    dates_str = []
    for values in values_list:
        dates_str.append(values[0])

    dates_datetime = []
    for date_str in dates_str:
        date_datetime = datetime.strptime(date_str, '%m/%d/%Y,%H:%M:%S')
        dates_datetime.append(date_datetime)
    return dates_datetime


def print_chart_price(dates_raw, price):
    dates = matplotlib.dates.date2num(dates_raw)
    cb91_green = '#47DBCD'
    plt.style.use('dark_background')
    matplotlib.rcParams.update({'font.size': 22})
    f = plt.figure(figsize=(16, 9))
    ax = f.add_subplot(111)
    ax.yaxis.set_major_formatter('${x:1.3f}')
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")
    ax.yaxis.grid(alpha=0.3, linestyle='--')

    plt.plot_date(dates, price, cb91_green)
    plt.gcf().autofmt_xdate()
    plt.savefig(chart_price_file_path, bbox_inches='tight', dpi=300)
    plt.close(f)


def print_chart_supply(dates_raw, supply_rot, supply_maggot):
    dates = matplotlib.dates.date2num(dates_raw)
    cb91_green = '#47DBCD'
    plt.style.use('dark_background')

    matplotlib.rcParams.update({'font.size': 22})
    f = plt.figure(figsize=(16, 9))

    ax = f.add_subplot(111)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plot1 = ax.plot_date(dates, supply_maggot, 'r', label='maggot')

    ax2 = ax.twinx()
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plot2 = ax2.plot_date(dates, supply_rot, cb91_green, label='rot')

    ax.set_ylabel("Maggot")
    ax2.set_ylabel("Rot")

    plots = plot1 + plot2
    labs = [l.get_label() for l in plots]
    ax.legend(plots, labs, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
              ncol=2, mode="expand", borderaxespad=0.)

    plt.gcf().autofmt_xdate()
    plt.savefig(chart_supply_file_path, bbox_inches='tight', dpi=300)
    plt.close(f)


def get_chart_price_pyplot(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    global last_time_checked_price_chart

    query_received = update.message.text.split(' ')
    if update.message.from_user.first_name == 'Ben':
        print("hello me")
        last_time_checked_price_chart = 1

    time_type, time_start, k_hours, k_days, query_ok, simple_query = check_query(query_received)

    if query_ok:
        new_time = round(time.time())
        if new_time - last_time_checked_price_chart > 60:
            if update.message.from_user.first_name != 'Ben':
                last_time_checked_price_chart = new_time
            list_time_price = []

            with open(price_file_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                for row in spamreader:
                    list_time_price.append((row[0], row[1]))

            now = datetime.utcnow()

            filtered_values = [x for x in list_time_price if
                               now - strp_date(x[0]) < timedelta(days=k_days, hours=k_hours)]

            dates_pure = keep_dates(filtered_values)
            price = [float(value[1]) for value in filtered_values]

            print_chart_price(dates_pure, price)

            if simple_query:
                caption = "Chart since the bot starting logging the price.\nCurrent price: <pre>$" + str(price[-1])[
                                                                                                     0:10] + "</pre>"
            else:
                caption = "Price of the last " + str(time_start) + str(time_type) + ".\nCurrent price: <pre>$" + str(
                    price[-1])[0:10] + "</pre>"

            context.bot.send_photo(chat_id=chat_id,
                                   photo=open(chart_price_file_path, 'rb'),
                                   caption=caption,
                                   parse_mode="html")
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text="Displaying charts only once every minute. Don't abuse this function")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Request badly formated. Please use /getchart time type (example: /getchart 3 h for the last 3h time range). Simply editing your message will not work, please send a new correctly formated message.")


def strp_date_candles(raw_date):
    return datetime.strptime(raw_date[:-3], '%m/%d/%Y,%H:%M')


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    things = []
    for i in range(0, len(lst) - 1, n):  # avoiding the last values as it can lead to some bugs
        second_part = [float(x[1]) for x in lst[i:i + n]]
        date = strp_date_candles(lst[i][0])
        things.append((date, second_part))
    return things


# date opening closing high low
def transform_to_candelstick_format(list_values, resolution):
    if len(list_values) > 600:
        subvalues = chunks(list_values, 4 * resolution * 2)
    else:
        subvalues = chunks(list_values, 4 * resolution)
    lst_dates = []
    lst_openings = []
    lst_closes = []
    lst_highs = []
    lst_lows = []
    for value_date_price in subvalues:
        prices = value_date_price[1]
        lst_dates.append(value_date_price[0])
        lst_highs.append(max(prices))
        lst_lows.append(min(prices))
        lst_openings.append(prices[0])
        if len(prices) >= 2:
            lst_closes.append(prices[-1])
        else:
            lst_closes.append(prices[0])
    return lst_dates, lst_openings, lst_closes, lst_highs, lst_lows


def print_candlelight(dates, openings, closes, highs, lows):
    fig = go.Figure(data=[go.Candlestick(x=dates,
                                         open=openings,
                                         high=highs,
                                         low=lows,
                                         close=closes)])
    fig.update_layout(
        autosize=False,
        width=1600,
        height=900,
        # title='Road to $.666',
        yaxis_title='ROT price (usdt)',
        xaxis_rangeslider_visible=False,
        yaxis_side="right",
        margin=go.layout.Margin(l=15, r=15, b=15, t=15)
    )
    fig.write_image(candels_file_path, scale=4)
    plt.close()


def check_query(query_received):
    query_ok, simple_query = True, False
    time_type, time_start, k_hours, k_days = 'd', 0, 0, 100
    if len(query_received) == 1:
        simple_query = True
    elif len(query_received) == 3:
        time_type, time_start, k_hours, k_days = get_from_query(query_received)
    else:
        query_ok = False
    return time_type, time_start, k_hours, k_days, query_ok, simple_query


def get_candlestick_pyplot(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    global last_time_checked_price_candles

    query_received = update.message.text.split(' ')
    if update.message.from_user.first_name == 'Ben':
        print("hello me")
        last_time_checked_price_candles = 1

    time_type, time_start, k_hours, k_days, query_ok, simple_query = check_query(query_received)

    if query_ok:
        new_time = round(time.time())
        if new_time - last_time_checked_price_candles > 60:
            if update.message.from_user.first_name != 'Ben':
                last_time_checked_price_candles = new_time
            list_time_price = []

            with open(price_file_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                for row in spamreader:
                    list_time_price.append((row[0], row[1]))

            now = datetime.utcnow()

            filtered_values = [x for x in list_time_price if
                               now - strp_date(x[0]) < timedelta(days=k_days, hours=k_hours)]
            resolution = 1
            (dates, openings, closes, highs, lows) = transform_to_candelstick_format(filtered_values, resolution)

            print_candlelight(dates, openings, closes, highs, lows)
            if simple_query:
                caption = "Candlestick chart since the bot starting logging the price.\nCurrent price: <pre>$" + str(
                    list_time_price[-1][1])[0:10] + "</pre>"
            else:
                caption = "Price of the last " + str(time_start) + str(time_type) + ".\nCurrent price: <pre>$" + str(
                    list_time_price[-1][1])[0:10] + "</pre>"

            context.bot.send_photo(chat_id=chat_id,
                                   photo=open(candels_file_path, 'rb'),
                                   caption=caption,
                                   parse_mode="html")
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text="Displaying charts only once every minute. Don't abuse this function")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Request badly formated. Please use /candlestick time type (example: /getchart 3 h for the last 3h time range). Simply editing your message will not work, please send a new correctly formated message.")


def get_chart_supply_pyplot(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    global last_time_checked_price_supply

    query_received = update.message.text.split(' ')
    if update.message.from_user.first_name == 'Ben':
        print("hello me")
        last_time_checked_price_supply = 1

    time_type, time_start, k_hours, k_days, query_ok, simple_query = check_query(query_received)

    if query_ok:
        new_time = round(time.time())
        if new_time - last_time_checked_price_supply > 60:
            if update.message.from_user.first_name != 'Ben':
                last_time_checked_price_supply = new_time
            list_time_supply = []

            with open(supply_file_path, newline='') as csvfile:
                spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
                for row in spamreader:
                    list_time_supply.append((row[0], row[1], row[2]))

            now = datetime.utcnow()

            filtered_values = [x for x in list_time_supply if
                               now - strp_date(x[0]) < timedelta(days=k_days, hours=k_hours)]

            dates_pure = keep_dates(filtered_values)
            supply_rot = [int(value[1]) for value in filtered_values]
            supply_maggot = [int(value[2]) for value in filtered_values]

            print_chart_supply(dates_pure, supply_rot, supply_maggot)
            current_rot_str = number_to_beautiful(supply_rot[-1])
            current_maggot_str = number_to_beautiful(supply_maggot[-1])
            if simple_query:
                caption = "Chart since the bot starting logging the supply.\nCurrent supply: \n<b>ROT:</b> <pre>" + current_rot_str + "</pre> \n<b>MAGGOT:</b> <pre>" + current_maggot_str + "</pre>"
            else:
                caption = "Supply of the last " + str(time_start) + str(
                    time_type) + ".\nCurrent supply: \n<b>ROT:</b> <pre>" + current_rot_str + "</pre> \n<b>MAGGOT:</b> <pre>" + current_maggot_str + "</pre>"

            context.bot.send_photo(chat_id=chat_id,
                                   photo=open(chart_supply_file_path, 'rb'),
                                   caption=caption,
                                   parse_mode="html")
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text="Displaying charts only once every minute. Don't abuse this function")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Request badly formated. Please use /getchartsupply time type (example: /getchart 3 h for the last 3h time range). Simply editing your message will not work, please send a new correctly formated message.")


def get_airdrop(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    message = '''<a href="https://twitter.com/RottenSwap/status/1311624434038509568">As promised, here are the #airdrop details:
- Follow us, like and RT this tweet (click me),
- Join our TelegramGroup http://t.me/rottenswap,
- Hold 7,500 $ROT tokens minimum at snapshot time (random time between 1st and 31st October),
- Fill the form:</a> <a href="https://docs.google.com/forms/d/1Zjb0m9tSpqkjG9qql6kuMNIBLU7_29kekDf4rVOrUS4">https://docs.google.com/forms/d/1Zjb0m9tSpqkjG9qql6kuMNIBLU7_29kekDf4rVOrUS4</a>'''
    context.bot.send_message(chat_id=chat_id,
                             text=message,
                             parse_mode='html',
                             disable_web_page_preview=True)


def main():
    updater = Updater('1240870832:AAGFH0uk-vqk8de07pQV9OAQ1Sk9TN8auiE', use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('rotme', send_meme_to_chat))
    dp.add_handler(CommandHandler('links', get_links))
    dp.add_handler(CommandHandler('rotfarmingguide', stake_command))
    dp.add_handler(CommandHandler('howtoslippage', how_to_slippage))
    dp.add_handler(CommandHandler('supplycap', get_supply_cap))
    dp.add_handler(CommandHandler('4biz', get_biz))
    dp.add_handler(CommandHandler('twitter', get_last_tweets))
    dp.add_handler(MessageHandler(Filters.photo, handle_new_image))
    dp.add_handler(CommandHandler('rot_price', get_price_rot))
    dp.add_handler(CommandHandler('maggot_price', get_price_maggot))
    dp.add_handler(CommandHandler('help', get_help))
    dp.add_handler(CommandHandler('fake_price', get_fake_price))
    dp.add_handler(CommandHandler('getChart', get_chart_price_pyplot))
    dp.add_handler(CommandHandler('getChartSupply', get_chart_supply_pyplot))
    dp.add_handler(CommandHandler('startBiz', callback_timer, pass_job_queue=True))
    dp.add_handler(CommandHandler('delete_meme_secret', delete_meme))
    dp.add_handler(CommandHandler('candlestick', get_candlestick_pyplot))
    dp.add_handler(CommandHandler('airdropinfo', get_airdrop))
    # dp.add_handler(MessageHandler(Filters.text, check_new_proposal, pass_job_queue=True))
    RepeatedTimer(15, log_current_price_rot_per_usd)
    RepeatedTimer(60, log_current_supply)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

commands = """
help - Technical issues? A question? Need help?
rotme - Give me a random meme
links - Main links
rotfarmingguide - Guide to $ROT farming
howtoslippage - How to increase slippage
supplycap - How ROTTED are we
4biz - List biz thread
twitter - List twitter threads
add_meme - Add a meme to the common memes folder
getchart - Display a (simple) price chart
getchartsupply - Display a graph of the supply cap
candlestick - Candlestick chart 
airdropinfo - Info about the airdrop
"""
