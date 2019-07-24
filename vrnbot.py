import datetime
import logging
from telegram.ext import Updater, CommandHandler
import requests
from bs4 import BeautifulSoup
import config
import os
from db_connect import write_to_base, check_item_exist, get_news, make_posted, db_trash

# Logging functions
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO,
                    filename='log.txt')

logger = logging.getLogger(__name__)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def get_html(url):
    r = requests.get(url)
    return r.text


def get_forecast(html):
    soup = BeautifulSoup(html, 'lxml')
    fc = dict()
    for tag in [['city', 'title'], ['traffic', 'hint', 'level'], ['sunrise', 'sun_rise'], ['sunset', 'sunset']]:
        if len(tag) == 3:
            fc[tag[0]] = []
            fc[tag[0]].append(soup.find(tag[1]).text.lower())
            fc[tag[0]].append(int(soup.find(tag[2]).text))
        else:
            fc[tag[0]] = soup.find(tag[1]).text
    for time in [['morning_temp', 'утро'], ['day_temp', 'день'],  ['evening_temp', 'вечер'], ['night_temp', 'ночь']]:
        try:
            fc[time[0]] = soup.find('day_part', {'type': time[1]}).find('temperature').text
        except AttributeError:
            fc[time[0]] = soup.find('day_part', {'type': time[1]}).find('temperature_from').text
            fc[time[0]] += ' ' + soup.find('day_part', {'type': time[1]}).find('temperature_to').text
    return fc


def post_forecast(bot, job):
    fc = get_forecast(get_html(config.forecast_url))
    if [2, 3, 4].count(fc['traffic'][1]):
        level = 'балла'
    elif fc['traffic'][1] == 1:
        level = 'балл'
    else:
        level = 'баллов'
    common_text = 'Пробки: *{} {}* ({})\nВосход солнца: *{}*, заход: *{}*'.format(fc['traffic'][1], level,
                                                                                  fc['traffic'][0], fc['sunrise'],
                                                                                  fc['sunset'])
    t_morning = '\nt° утром: *{}*\nt° днем: *{}*'.format(fc['morning_temp'], fc['day_temp'])
    t_evening = '\nt° вечером: *{}*\nt° ночью: *{}*'.format(fc['evening_temp'], fc['night_temp'])
    if job.context == 'morning':
        post_text = 'Доброе утро, {}!\n\n'.format(fc['city']) + common_text + t_morning + t_evening
    else:
        post_text = 'Добрый вечер, {}!\n\n'.format(fc['city']) + common_text + t_evening + t_morning
    bot.send_message(config.post_channel, post_text, parse_mode='Markdown')


def post_news(bot, update):
    post_text = str()
    news = get_news()
    if news:
        post_text = '*Дайджест {}:*\n'.format(config.digest_name)
        counter = 1
        for n in news:
            post_text += '{}) '.format(counter) + n[0] + '\n'
            counter += 1
            make_posted(n[0])
    post_text += '\n{}\n'.format(config.ya_name)
    counter = 1
    for news in get_yandex_news(config.ya_link):
        post_text += '{}) '.format(counter) + news + '\n'
        counter += 1
    bot.send_message(config.post_channel, post_text, parse_mode='Markdown')


def get_yandex_news(url):
    soup = BeautifulSoup(get_html(url), 'lxml')
    news = soup.find_all('h2', class_='story__title')[0:5]
    text = []
    for n in news:
        title = n.find('a').text
        link = config.ya_link[0:22] + n.find('a')['href']
        text.append(('[{}]({})'.format(title, link)))
    return text


def spider(bot, update):
    soup = BeautifulSoup(get_html(config.digest_url), 'lxml')
    dd_list = soup.find_all('item')
    for item in dd_list[::-1]:
        title = item.find('title').text
        link = item.find('guid').text
        item_text = ('[{}]({})'.format(title, link))
        if not check_item_exist(item_text):
            write_to_base(item_text)


def main():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(config.token,
                      request_kwargs={'proxy_url': config.proxy_url,
                                      'urllib3_proxy_kwargs': {
                                                                'username': config.proxy_login,
                                                                'password': config.proxy_password,
                                                                }
                                      })

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram

    # log all errors
    dp.add_error_handler(error)
    job_queue = updater.job_queue
    # Forecast jobs
    job_morning = job_queue.run_daily(post_forecast, time=datetime.time(hour=config.morning_post), context='morning')
    job_evening = job_queue.run_daily(post_forecast, time=datetime.time(hour=config.evening_post))
    # News jobs: crawler and poster
    job_dgst_crawler = job_queue.run_repeating(spider, interval=1800, first=0)
    job_dgst_morning = job_queue.run_daily(post_news, time=datetime.time(hour=config.morning_news))
    job_dgst_noon = job_queue.run_daily(post_news, time=datetime.time(hour=config.noon_news))
    job_dgst_evening = job_queue.run_daily(post_news, time=datetime.time(hour=config.evening_news))
    # Trash job
    job_trash = job_queue.run_daily(db_trash, time=datetime.time(hour=config.noon_news))
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
