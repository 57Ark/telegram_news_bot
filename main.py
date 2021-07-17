import logging
from aiogram import Bot, Dispatcher
import asyncio
from aiogram.types import ParseMode
from bs4 import BeautifulSoup
from requests.exceptions import Timeout
from selenium import webdriver
import datetime
from requests import get

bot = Bot(token='вставьте токен бота')
chat_id = 57575757  # id моего телеграмм канала (вставьте рабочий id)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)


# ----------------------------------------------------------------------------------------------------------------------
# фукции команд для общения с ботом в лс
@dp.message_handler(commands='start')
async def cmd_start(message):
    await bot.send_message(message.chat.id, "Привет!")


@dp.message_handler(content_types=['text'])
async def send_text(message):
    await bot.send_message(message.chat.id, "Я пока ничего не умею")


# функция админестрирования тг канала
async def manage_channel():
    await scrap_meduza()
    await scrap_dailystorm()


# ----------------------------------------------------------------------------------------------------------------------
# скраппер сайта Медузы
def check_meduza(inp):  # возвращает True если новость написали менее 3х минут назад
    my_set_sec = {'секунд', 'секунду', 'секунды', 'секунда'}
    my_set_min = {'минут', 'минуту', 'минуты', 'минута'}
    data = inp.split()
    if len(data) < 3:
        if data[0] in my_set_sec:
            return True
        if data[0] in my_set_min:
            return True
        return False
    if data[1] in my_set_sec:
        return True
    if data[1] in my_set_min and int(data[0]) <= 3:
        return True
    return False


async def scrap_meduza():
    news = []
    try:
        url = 'https://meduza.io/'
        driver = webdriver.Chrome('C:\Windows\chromedriver.exe')
        driver.get(url)
        html = driver.page_source
        html_soup = BeautifulSoup(html, "html.parser")
        # ждём полной загрузки страницы и получаем её

        links = html_soup.findAll('a', {'class': 'Link-root Link-isInBlockTitle'})  # получаем список новостей
        meta = html_soup.findAll('time', {"class": "Timestamp-module_root__coOvT"})
        # получаем данные о времени загрузки новости

        driver.quit()
        # закрываем браузер, он нам больше не нужен

        for i in range(0, 30):
            title = links[i].find('span', {"class": "BlockTitle-first"})  # получаем заголовок новости
            text = links[i].find('span', {'class': 'BlockTitle-second'})  # получаем подзаголовок новости
            time = meta[i].text  # получаем время выхода новости

            # обработка случаев, когда заголовок или подзаголовок пустые
            if title is None:
                title = ""
            else:
                title = title.text
            if text is None:
                text = ""
            else:
                text = text.text

            # обрабатываем время новости и запомиаем её, если она подходит
            flag = check_meduza(time)
            if flag:
                news.append("*" + title + "*" + "\n" + text + '\nhttps://meduza.io/' + links[i].get('href'))

        # если собрана хотя бы одна новость, то печатаем их
        if len(news) != 0:
            # await bot.send_message(chat_id, "Я нашел эти новости:")
            for new in news:
                print(new)
                await bot.send_message(chat_id, new, parse_mode=ParseMode.MARKDOWN)

    # обрабатываем ошибки
    except AttributeError or IndexError:
        pass
    except Timeout:
        print('Time out')
        pass


# ----------------------------------------------------------------------------------------------------------------------
# скраппер сайта Дейлишторм
def check_dailystorm(inp):  # возвращает True если новость написали менее 3х минут назад
    data = inp.split(":")
    now = datetime.datetime.now().time()
    hour, minute = int(data[0]), int(data[1])
    if hour == now.hour:
        if now.minute - minute < 3:
            return True
        return False
    if now.hour - hour == 1:
        if now.minute + 60 - minute < 3:
            return True
        return False
    if now.hour == 0 and hour == 23:
        if now.minute + 60 - minute < 3:
            return True
        return False
    return False


async def scrap_dailystorm():
    news = []
    try:
        url = 'https://dailystorm.ru/news'
        response = get(url)
        html_soup = BeautifulSoup(response.text, 'html.parser')
        # загружаем страницу

        meta = html_soup.findAll('span',
                                 {'class': 'news__list-item-date'})  # # получаем данные о времени загрузки новости
        new = html_soup.findAll('a', {"class": "news__list-item-link"})  # получаем список новостей

        for i in range(0, 10):
            time = meta[i].text  # получаем время выхода новости
            title = new[i].text  # получаем текст новости
            link = new[i].get('href')  # получаем ссылку на новость

            # обрабатываем время новости и запомиаем её, если она подходит
            flag = check_dailystorm(time)
            if flag:
                news.append("*" + title + "*" + '\ndailystorm.ru/news' + link)

        # если собрана хотя бы одна новость, то печатаем их
        if len(news) != 0:
            for new in news:
                print(new)
                await bot.send_message(chat_id, new, parse_mode=ParseMode.MARKDOWN)

    # обрабатываем ошибки
    except AttributeError or IndexError:
        pass
    except Timeout:
        print('Time out')
        pass


# ----------------------------------------------------------------------------------------------------------------------
# основная функция
async def main():
    polling_task = asyncio.create_task(dp.start_polling())
    while True:
        await manage_channel()
        await asyncio.sleep(180)  # запускаем цикл каждые 3 минуты

loop = asyncio.get_event_loop()
if __name__ == '__main__':
    loop.run_until_complete(main())
    loop.close()
