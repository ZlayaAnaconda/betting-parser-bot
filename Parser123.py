import asyncio
import os
import sqlite3
import sys
import time
from contextlib import suppress
import telebot
from playwright.async_api import async_playwright
import datetime as dt
from requests import ReadTimeout
from bcolors import bcolors
from config import chat_id, token, koefikus, find_TB, find_koef, time_start
from datetime import datetime, timedelta

bot = telebot.TeleBot(token)


async def parser(browser):
    try:
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://1xstavka.ru/line/football/", timeout=0)
        i = 0
        await page.wait_for_selector('//*[@id="games_content"]/div/div[2]/div/div/div[1]')
        while True:
            try:
                i += 1
                await (
                    await page.query_selector(f'//*[@id="games_content"]/div/div[2]/div/div/div[{i}]')).text_content()

            except AttributeError:
                break
        i -= 1
        lst = []
        for k in range(1, i + 1):
            j = 1
            while True:
                try:
                    j += 1
                    try:
                        await (await page.query_selector(
                            f'//*[@id="games_content"]/div/div[2]/div/div/div[{k}]/div[{j}]/div[2]')).text_content()
                    except AttributeError:

                        await (await page.query_selector(
                            f'//*[@id="games_content"]/div/div[2]/div/div/div[{k}]/div[{j}]/div')).text_content()
                except AttributeError:
                    break
            lst.append(j - 2)
        j = lst
        for n in range(1, i + 1):
            for m in range(2, j[n - 1] + 1):
                game = {
                    'Турнир': await (await page.query_selector(
                        f'//*[@id="games_content"]/div/div[2]/div/div/div[{n}]/div[1]/div/div[3]/a')).text_content()
                }
                try:
                    selector = f'//*[@id="games_content"]/div/div[2]/div/div/div[{n}]/div[{m}]/div[2]/div/a/span'
                    text = ''.join(
                        (await (await page.query_selector(selector)).text_content()).split(
                            '\n' + ' ' * 20)).split('\n' + ' ' * 17)
                except AttributeError:
                    selector = f'//*[@id="games_content"]/div/div[2]/div/div/div[{n}]/div[{m}]/div[1]/div/a/span'
                    try:
                        text = ''.join(
                            (await (await page.query_selector(selector)).text_content()).split(
                                '\n' + ' ' * 20)).split('\n' + ' ' * 17)
                    except AttributeError:
                        continue

                if text[0] == 'Хозяева' or not text[0]:
                    continue
                await (await page.query_selector(selector)).click()
                selector = '//*[@id="games_content"]/div/div/div/div/div/div/div/div[2]/div/div[2]/div'
                await page.wait_for_selector(selector, timeout=0)# зашел на игру
                print("fdsf")

                game['Хозяева'] = (await (await page.query_selector(selector + '/div')).text_content()).strip('\n ')
                game['Гости'] = (await (await page.query_selector(selector + '/div[3]')).text_content()).strip('\n ')
                # //*[@id="games_content"] = /html/body/div[3]/div[1]/div[2]/div/div/div[3]/div
                selector = ('//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div[1]/div[2]'
                            '/div[2]/div/div[2]/div[1]/div/div')
                for k in range(2, 7):
                    try:
                        dct = []
                        text = await (await page.query_selector(selector + f'/div[{k}]')).text_content()
                        old_text = text
                        text = ' '.join(text.split('\n'))
                        while old_text != text:
                            old_text = text
                            text = ' '.join(text.split('  '))
                        text = text[11:].split(' : ')
                        dct.append(int(text[0].strip(' ')[text[0].strip(' ').rfind(' ') + 1:]))
                        dct.append(int(text[1].strip(' ')[:text[1].strip(' ').find(' ')]))
                        game[f'Матч {k - 1} хозяев против других команд'] = dct
                    except AttributeError:
                        break

                for h in range(9, 15):
                    try:
                        dct = []
                        text = await (await page.query_selector(selector + f'/div[{h}]')).text_content()
                        old_text = text
                        text = ' '.join(text.split('\n'))
                        while old_text != text:
                            old_text = text
                            text = ' '.join(text.split())
                        text = text[11:].split(' : ')
                        dct.append(int(text[0].strip(' ')[text[0].strip(' ').rfind(' ') + 1:]))
                        dct.append(int(text[1].strip(' ')[:text[1].strip(' ').find(' ')]))
                        game[f'Матч {h - 8} между командами предстоящего матча'] = dct
                    except AttributeError:
                        break
                selector = ('//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div[1]/div[2]'
                            '/div[2]/div/div[2]/div[2]/div/div')
                for k in range(2, 7):
                    try:
                        dct = []
                        text = await (await page.query_selector(selector + f'/div[{k}]')).text_content()
                        old_text = text
                        text = ' '.join(text.split('\n'))
                        while old_text != text:
                            old_text = text
                            text = ' '.join(text.split('  '))
                        text = text[11:].split(' : ')
                        dct.append(int(text[0].strip(' ')[text[0].strip(' ').rfind(' ') + 1:]))
                        dct.append(float(text[1].strip(' ')[:text[1].strip(' ').find(' ')]))
                        game[f'Матч {k - 1} гостей против других команд'] = dct
                    except AttributeError:
                        break
                coefficients = []
                for k in range(1, 50, 2):
                    selector = (f'#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > '
                                f'div:nth-child({k})')
                    try:
                        total = (await (await page.query_selector(selector)).text_content()).split('\n           ')
                        tb = {
                            'ТБ': float(total[0].split()[0]),
                            'Кэф': float(total[1]),
                        }
                        coefficients.append(tb)
                    except (AttributeError, ValueError):
                        break
                if not coefficients:
                    for k in range(1, 50, 2):
                        selector = (f'#allBetsTable > div:nth-child(1) > div:nth-child(3) > div > div.bets.betCols2 > '
                                    f'div:nth-child({k})')
                        try:
                            total = (await (await page.query_selector(selector)).text_content()).split('\n           ')
                            tb = {
                                'ТБ': float(total[0].split()[0]),
                                'Кэф': float(total[1]),
                            }
                            coefficients.append(tb)
                        except (AttributeError, ValueError):
                            break
                game['Коэффициенты'] = coefficients
                # //*[@id="games_content"] = /html/body/div[3]/div[1]/div[2]/div/div/div[3]/div

                date = (await (await page.query_selector(
                    '//*[@id="games_content"]'
                    '/div/div/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div[1]/div[2]/div[1]/div')).text_content()).strip(
                    '\n\t ')
                game['Дата'] = date
                game['url'] = page.url
                yield game
                await page.go_back(timeout=0)
        await context.close()
        await context.close()
        await context.close()
        await context.close()
    except Exception as ex:
        print(ex)


def find_coef(game):
    result = {
        'Турнир': game['Турнир'],
        'Дата': game['Дата'],
        'Хозяева': game['Хозяева'],
        'Гости': game['Гости'],
    }
    for dct in game['Коэффициенты']:
        tb = dct['ТБ']
        coef = dct['Кэф']
        tb_1, tb_2, tb_3 = 0, 0, 0
        try:
            for i in range(1, 6):
                m_1 = game[f'Матч {i} хозяев против других команд']
                if m_1[0] >= tb or m_1[1] >= tb:
                    tb_1 += 20
                m_2 = game[f'Матч {i} между командами предстоящего матча']
                if m_2[0] >= tb or m_2[1] >= tb:
                    tb_2 += 20
                m_3 = game[f'Матч {i} гостей против других команд']
                if m_3[0] >= tb or m_3[1] >= tb:
                    tb_3 += 20
        except KeyError:
            return None
        avg = (tb_1 + tb_2 + tb_3) / 3
        if avg >= find_TB and coef >= find_koef and tb != float(2) and tb != float(1):
            result['ТБ'] = tb
            print(tb)
            result['Кэф'] = coef
            return result
    return None


async def get_nice_games(browser):
    async for game in parser(browser):
        result = find_coef(game)
        if result:
            result['url'] = game['url']
            print(result)
            yield result


def get_written_matches():
    connection = sqlite3.connect('data')
    cur = connection.cursor()
    games = cur.execute('SELECT * FROM matches').fetchall()
    cur.close()
    connection.commit()
    return games


def write_match(game: dict, message_id, url):
    connection = sqlite3.connect('data')
    cur = connection.cursor()
    with suppress(sqlite3.OperationalError):
        cur.execute('INSERT INTO matches VALUES (?, ?, ?)',
                    (', '.join([str(i) for i in list(game.values())[:-1]]), message_id, url))
    cur.close()
    connection.commit()


async def second_starter(browser):
    print(214321)
    try:
        print('Запустили функцию БД')
        con = sqlite3.connect('data')
        cur = con.cursor()
        games = cur.execute('SELECT * FROM matches').fetchall()
        for game in games:
            game = list(game)
            print(game)
            print('Это игра из базы', game)
            # noinspection PyUnresolvedReferences
            game[0] = game[0].split(', ')
            print(game)
            # noinspection PyTypeChecker
            game_date = dt.datetime.strptime(game[0][1], '%d.%m.%Y %H:%M')
            now_date = dt.datetime.now()
            con = sqlite3.connect('data')
            print('Текущая дата', now_date, 'Дата игры', game_date)
            time_stop = now_date - game_date
            rich = time_stop - timedelta(seconds=1800)
            chitos = timedelta(seconds=0)
            print(rich)
            if rich > chitos:
                cur = con.cursor()
                cur.execute('DELETE FROM matches')
                cur.close()
                con.commit()
                print("Игра уже началась ")
            elif now_date >= game_date:
                print('Пошли сюда')
                print(game)
                url = game[2]
                name = game[0]
                print(name)
                print(name)
                print(url)
                print("пес")
                message_id = game[1]
                tournament = game[0][0]
                context = await browser.new_context()
                page = await context.new_page()
                time.sleep(time_start)  #####
                await page.goto(url, timeout=0)
                time.sleep(10)
                status_game = game[0][0]
                gamenew = game[0][4]
                turnir = game[0][0]
                player_1 = game[0][2]
                player_2 = game[0][3]

                new_gamenew = float(gamenew)
                new_koefikus = float(koefikus)
                print(new_gamenew)

                time.sleep(10)
                try:
                    try:
                        selector_TB = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(1) > span.bet_type"
                        TB = await (await page.query_selector(selector_TB)).text_content()
                        new_TB = TB.replace("Б", "")
                    except Exception as ex:
                        print(ex)
                except Exception as ex:
                    print(ex)
                print(f"ТБ ЛОМАЛСЯ {new_TB}")
                print(game_date)
                time_now_new = dt.datetime.now()
                print(time_now_new)
                time_send = (time_now_new - game_date).seconds
                itog_send = time_send / 60
                print(itog_send)
                formatted_number = format(itog_send, ".2f")
                print(formatted_number)
                new_s = formatted_number.replace('.', '′')
                print(new_s)

                send_time = round(itog_send, 0)
                send_in_group = int(send_time)
                print("123124")

                print("Да")
                new_TB_vau = float(new_TB)
                print("Белка")
                print(new_TB_vau)
                print(type(new_TB_vau))

                if new_gamenew == 0.5:  # надо дать значение "TB"
                    print("0,5 21321312")
                    if new_TB_vau == 0.5:

                        selector_koef = '#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > ' \
                                        'div:nth' \
                                        '-child(1) > span.koeff'
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        print("сосика")
                        if new_koef >= new_koefikus:
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊  {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("сосика")
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print(
                                "0,5 коэф не подошел")  # Если 1 Тб 0.5 то приводит в действие если 1 тб выше то нам не подходит изначально по условию
                    else:
                        cur = con.cursor()
                        cur.execute('DELETE FROM matches')
                        print("Нету подходящих вариантов")

                if new_gamenew == 1.5:  # надо дать значение "TB"
                    print("1.5 123213")
                    if new_TB_vau == 0.5:
                        print("wau321")

                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(5) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊  {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел000")
                    elif new_TB_vau == 1:
                        print("wau123")
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(3) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊  {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел321")
                    elif new_TB_vau == 1.5:
                        con = sqlite3.connect('data')
                        cur = con.cursor()
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(1) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊  {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел654")
                    else:
                        print("Не подходит")
                        cur = con.cursor()
                        cur.execute('DELETE FROM matches')

                if new_gamenew == 2.5:  # надо дать значение "TB"
                    print("2,5 213123123")
                    if new_TB_vau == 0.5:
                        print("0,5 213123123")
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(9) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            print("соси4ка")
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊 1.85 {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')

                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел")
                    if new_TB_vau == 1:
                        print("1 213123123")
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(7) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊 1.85 {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел")

                    if new_TB_vau == 1.5:
                        print("1,5 213123123")
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(5) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            print("сосика")
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊 1.85 {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел")
                    if new_TB_vau == 2:
                        print("2 213123123")
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(3) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊 1.85 {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел")
                    if new_TB_vau == 2.5:
                        print("2,5 213123123")
                        selector_koef = "#allBetsTable > div:nth-child(2) > div:nth-child(2) > div > div.bets.betCols2 > div:nth-child(1) > span.koeff > i"
                        koef = await (await page.query_selector(selector_koef)).text_content()
                        new_koef = float(koef)
                        if new_koef >= new_koefikus:
                            print("oeoe")
                            bot.send_message(chat_id, f'⚽️ Football\n'
                                                      f'⚙️  {turnir}\n'
                                                      '\n'
                                                      f'{player_1}  🆚 {player_2}\n'
                                                      '\n'
                                                      f'📊 1.85 {koef}\n'
                                                      f'🥅 ТБ {new_gamenew}ТБ\n'
                                                      f'\n'
                                                      f'⏳ЛАЙВ 🔥')
                            cur.execute('DELETE FROM matches')
                        else:
                            cur = con.cursor()
                            cur.execute('DELETE FROM matches')
                            print("1,5 коэф не подошел")
                    else:
                        cur = con.cursor()
                        cur.execute('DELETE FROM matches')
                        print("Нету подходящих вариантов")
                else:
                    print("Хуйня какая то ")
                    cur = con.cursor()
                    cur.execute('DELETE FROM matches')
                    cur.close()
                    con.commit()
                    await context.close()

                print(game)
                cur = con.cursor()
                cur.execute('DELETE FROM matches')
                cur.close()
                con.commit()
                await context.close()
    except Exception as ex:
        print(ex)

        await asyncio.sleep(20)


async def find_match(owner, guest, browser, game):
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto('https://1xstavka.ru/live/football', timeout=0)
    i = 0
    await page.wait_for_selector('//*[@id="games_content"]/div/div[1]/div/div/div[1]')

    while True:
        try:
            i += 1
            await (await page.query_selector(f'//*[@id="games_content"]/div/div[1]/div/div/div[{i}]')).text_content()
        except AttributeError:
            break
    i -= 1
    for k in range(1, i + 1):
        j = 1
        while True:
            try:
                j += 1
                text = await (await page.query_selector(
                    f'//*[@id="games_content"]'
                    f'/div/div[1]/div/div/div[{k}]/div[{j}]/div/div[1]/div/div[1]/a')).text_content()
                if owner in text and guest in text:
                    await (await page.query_selector(
                        f'//*[@id="games_content"]'
                        f'/div/div[1]/div/div/div[{k}]/div[{j}]/div/div[1]/div/div[1]/a')).click()
                    await match_reader(browser, owner, guest, page.url, game)
                    return
            except AttributeError:
                break
    await context.close()


async def match_reader(browser, owner: str, guest: str, url: str, game):
    message_id = game[1]
    game = {
        'Турнир': game[0][0],
        'Хозяева': owner,
        'Гости': guest,
        'ТБ': game[0][4],
        'Кэф': game[0][5]
    }
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(url, timeout=0)
    await page.wait_for_selector('//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div['
                                 '2]/div[1]/div[1]/ul/li[3]/div')
    con = sqlite3.connect('data')
    cur = con.cursor()
    if int((await (await page.query_selector(
            '//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div'
            '/div[2]/div/div[2]/div[2]/div[1]/div[1]/ul/li[3]/div')).text_content()).strip('\n\t ').split(':')[
               0]) <= 20:
        score = [0, 0]
        score[0] = await (
            await page.query_selector('//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div/div[2]/div/div['
                                      '2]/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[1]')).text_content()
        score[1] = await (
            await page.query_selector('//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div/div[2]/div/div['
                                      '2]/div[2]/div[1]/div[2]/div/div[1]/div[2]/div[2]')).text_content()
        time = (await (await page.query_selector(
            '//*[@id="games_content"]/div/div/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div['
            '2]/div[1]/div[1]/ul/li[3]/div')).text_content()).strip('\n\t ')
        text = ('⚽️ Football\n'
                '⚙️ {}\n'
                '\n'
                '{} 🆚 {}\n'
                '\n'
                '🥅 {}ТБ\n'
                '📊 {}\n'
                '\n'
                'Матч начался!\n'
                '\n'
                'Счёт {}:{}\n'
                '\n'
                '🕘 {}').format(
            game['Турнир'], game['Хозяева'], game['Гости'], game['ТБ'], game['Кэф'], score[0], score[1], time)
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        except telebot.apihelper.ApiTelegramException:
            while cur.execute('SELECT * FROM matches WHERE message_id = ?', (message_id,)).fetchone():
                cur.execute('DELETE FROM matches WHERE message_id = ?', (message_id,))
    else:
        while cur.execute('SELECT * FROM matches WHERE message_id = ?', (message_id,)).fetchone():
            cur.execute('DELETE FROM matches WHERE message_id = ?', (message_id,))
    cur.close()
    con.commit()
    await context.close()


async def main_starter(browser):
    async for game in get_nice_games(browser):
        flag = False
        for i in get_written_matches():
            i = list(i)
            # print(i)
            try:
                i[0] = i[0].split(', ')
                if (game['Хозяева'], game['Гости']) == (i[0][2], i[0][3]):
                    # print('старая игра')
                    flag = True
                    break
            except:
                print('Не нашли в базе')
                pass
        if not flag:
            text = ('''
⚽️ Football
⚙️ {}

{} 🆚 {}

🥅 {}ТБ
📊 {}

🕘 {}''').format(
                game['Турнир'], game['Хозяева'], game['Гости'], game['ТБ'], game['Кэф'], game['Дата'])
            write_match(game, 1, game['url'])
            # message = bot.send_message(chat_id, text)

    await asyncio.sleep(0)


async def main():
    # noinspection PyBroadException
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, timeout=0)
        while True:
            await asyncio.gather(main_starter(browser),second_starter(browser))
            time.sleep(2)  # сколько отдыхает после парса


async def main_parser():
    # noinspection PyBroadException
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, timeout=0)
        while True:
            await asyncio.gather(main_starter(browser))
            time.sleep(1000)  # сколько отдыхает после парса


async def second_main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False, timeout=0)
        while True:
            await asyncio.gather(second_starter(browser))
            time.sleep(60) # отдых после проверки


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Бот запущен")
    print(bcolors.OKGREEN + 'Запуск парса матчей...' + bcolors.ENDC)
    asyncio.run(main())


@bot.message_handler(commands=['start_second'])
def start_message(message):
    bot.send_message(message.chat.id, "Проверка матчей запущена")
    print(bcolors.OKGREEN + 'Запуск парса матчей...' + bcolors.ENDC)
    asyncio.run(second_main())

@bot.message_handler(commands=['start_parser'])
def start_main(message):
    bot.send_message(message.chat.id, "Парсер активирован ")
    print(bcolors.OKGREEN + 'Запуск парса матчей...' + bcolors.ENDC)
    asyncio.run(main_parser())








if __name__ == '__main__':
    print(bcolors.OKGREEN + 'Бот запущен' + bcolors.ENDC)
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except (ConnectionError, ReadTimeout):
        sys.stdout.flush()
        os.execv(sys.argv[0], sys.argv)
    else:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
