import datetime
import logging
from telegram.ext import Updater, CommandHandler
import requests
from bs4 import BeautifulSoup
import config
import os

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
    for tag in [['city', 'title'], ['traffic', 'hint', True], ['sunrise', 'sun_rise'], ['sunset', 'sunset']]:
        if len(tag) == 3:
            fc[tag[0]] = soup.find(tag[1]).text.lower()
        else:
            fc[tag[0]] = soup.find(tag[1]).text
    for time in [['morning_temp', 'утро'], ['day_temp', 'день'],  ['evening_temp', 'вечер'], ['night_temp', 'ночь']]:
        try:
            fc[time[0]] = soup.find('day_part', {'type': time[1]}).find('temperature').text
        except AttributeError:
            fc[time[0]] = soup.find('day_part', {'type': time[1]}).find('temperature_from').text
            fc[time[0]] += ' ' + soup.find('day_part', {'type': time[1]}).find('temperature_to').text
    return fc


def check_posted(text):
    with open('last_posted.txt', 'r') as f:
        if text == f.read():
            return True
        else:
            return False


def write_posted(text):
    with open('last_posted.txt', 'w') as f:
        f.write(text)


def get_downtown_digest(html):
    # TODO: not less than 3 news
    soup = BeautifulSoup(html, 'lxml')
    dd_list = soup.find_all('item')
    post_text = '*Дайджест {}:*\n'.format(config.digest_name)
    for item in dd_list:
        if check_posted(item.find('title').text):
            dd_list = dd_list[:dd_list.index(item)]
            break
    if len(dd_list) <= 1:
        return None
    count = 1
    for item in dd_list[::-1]:
        title = item.find('title').text
        link = item.find('guid').text
        post_text += ('{}) [{}]({})\n'.format(count, title, link))
        count += 1
        write_posted(title)
    return post_text


def post_downtown_digest(bot, update):
    dd = get_downtown_digest(get_html(config.digest_url))
    if not dd:
        return
    bot.send_message(config.post_channel, dd, parse_mode='Markdown')


def post_yandex_digest(bot, update):
    pass


def post_forecast(bot, update, job):
    fc = get_forecast(get_html(config.forecast_url))
    common_text = 'Пробки: *{}*.\nВосход солнца: *{}*, заход: *{}*'.format(fc['traffic'], fc['sunrise'], fc['sunset'])
    t_morning = '\nt° утром: *{}*\nt° днем: *{}*'.format(fc['morning_temp'], fc['day_temp'])
    t_evening = '\nt° вечером: *{}*\nt° ночью: *{}*'.format(fc['evening_temp'], fc['night_temp'])
    if job.context == 'morning':
        post_text = 'Доброе утро, {}!\n\n'.format(fc['city']) + common_text + t_morning + t_evening
    else:
        post_text = 'Добрый вечер, {}!\n\n'.format(fc['city']) + common_text + t_evening + t_morning
    bot.send_message(config.post_channel, post_text, parse_mode='Markdown')


def post_forecast_now(bot, update):
    # TODO: make adaptive
    fc = get_forecast(get_html(config.forecast_url))
    common_text = 'Пробки: *{}*.\nВосход солнца: *{}*, заход: *{}*'.format(fc['traffic'], fc['sunrise'], fc['sunset'])
    t_morning = '\nt° утром: *{}*\nt° днем: *{}*'.format(fc['morning_temp'], fc['day_temp'])
    t_evening = '\nt° вечером: *{}*\nt° ночью: *{}*'.format(fc['evening_temp'], fc['night_temp'])
    post_text = 'Доброе утро, {}!\n\n'.format(fc['city']) + common_text + t_morning + t_evening
    bot.send_message(config.post_channel, post_text, parse_mode='Markdown')


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
    dp.add_handler(CommandHandler("forecast", post_forecast, context='morning'))

    # log all errors
    dp.add_error_handler(error)
    job_queue = updater.job_queue
    job_morning = job_queue.run_repeating(post_forecast, 86400, name='mforecast', context='morning')
    job_evening = job_queue.run_daily(post_forecast, time=datetime.time(hour=17), name='eforecast', context='evening')
    job_dgst = job_queue.run_repeating(post_downtown_digest, 14400, first=0, name='digest')
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
