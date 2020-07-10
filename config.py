import os

token = os.environ['TOKEN_NEWS_BOT']
post_channel = os.environ['POST_CHANNEL']
forecast_url = os.environ['FORECAST_URL']
# covid_url = os.environ['COVID_URL']
digest_url = os.environ['DIGEST_URL']
digest_name = os.environ['DIGEST_NAME']
proxy_url = os.environ['PROXY_URL']
proxy_login = os.environ['PROXY_LOGIN']
proxy_password = os.environ['PROXY_PASSWORD']
morning_post = int(os.environ.get('MORNING_POST'))
evening_post = int(os.environ.get('EVENING_POST'))
ya_name = os.environ['YA_NAME']
ya_link = os.environ['YA_LINK']
morning_news = int(os.environ['MORNING_NEWS'])
noon_news = int(os.environ['NOON_NEWS'])
evening_news = int(os.environ['EVENING_NEWS'])
db_name = os.environ['DBNAME']