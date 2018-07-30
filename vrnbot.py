import datetime
import logging
from telegram.ext import Updater, CommandHandler
import requests
from bs4 import BeautifulSoup

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

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


def post_downtown_digest(bot, update):
    pass


def post_yandex_digest(bot, update):
    pass


def post_forecast(bot, update):
    fc = get_forecast(get_html('https://export.yandex.ru/bar/reginfo.xml?region=193'))
    post_text = 'Доброе утро, {}!\n\n'.format(fc['city'])
    post_text += 'Сегодня {}.\n'.format(fc['traffic'])
    post_text += 'Восход солнца: *{}*, заход: *{}*'.format(fc['sunrise'], fc['sunset'])
    post_text += '\nt° утром: *{}*'.format(fc['morning_temp'])
    post_text += '\nt° днем: *{}*'.format(fc['day_temp'])
    post_text += '\nt° вечером: *{}*'.format(fc['evening_temp'])
    post_text += '\nt° ночью: *{}*'.format(fc['night_temp'])
    bot.send_message('@vrn_news', post_text, parse_mode='Markdown')


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("316755740:AAFk_rJg20gk7sMonMpxSkFAKiJTz6noZmY",
                      request_kwargs={'proxy_url': 'socks5h://81.2.244.181:7007',
                                      'urllib3_proxy_kwargs': {
                                                                'username': 'tgsocks',
                                                                'password': 'tgpass',
                                                                }
                                      })

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("forecast", post_forecast))

    # log all errors
    dp.add_error_handler(error)
    job_queue = updater.job_queue
    job = job_queue.run_daily(post_forecast, time=datetime.time(hour=9), name='forecast')
    #job_dgst = job_queue.run_daily(post_downtown_digest, time=datetime.time(hour=19), first=0, name='digest')
    updater.start_polling()
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
