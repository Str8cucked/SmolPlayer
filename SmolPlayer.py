#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter
import youtube_dl
import os
import threading
import time
import codecs
import contextlib
from requests import get
from mutagen.mp3 import MP3
from bs4 import BeautifulSoup
with contextlib.redirect_stdout(None):
    from pygame import mixer

ticker = 0
paused = False
nowPlaying = ''
songPosition = 0

def set_scrub(amount):
    global songPosition
    mixer.music.rewind()
    mixer.music.set_pos(amount)
    songPosition = amount
    musicScrubber.set(songPosition)

def clean_up():
    directory = os.getcwd()
    folder = os.listdir(directory)
    for file in folder:
        if file.endswith('.mp3'):
            os.remove(file)

def update():
    with open("urllist.txt", "r") as f:
        data = f.readlines()
    with open("urllist.txt", "w") as f:
        f.writelines(data[1:])
    with codecs.open("songlist.txt", "r", encoding='utf-8') as f:
        data = f.readlines()
    with codecs.open("songlist.txt", "w", encoding='utf-8') as f:
        f.writelines(data[1:])
    refresh()

def refresh():
    with open("songlist.txt", "r", encoding='utf-8') as f:
        songlist = f.readlines()
        songTextBox.delete(0, 'end')
        for line in songlist:
            try:
                songTextBox.insert('end', line)
            except:
                song = line.encode('unicode_escape')
                songTextBox.insert('end', f'{song}\n')

def clear():
    songTextBox.delete(0, 'end')
    with open("songlist.txt", "w", encoding="utf-8") as f:
        f.write('')
    with open("urllist.txt", "w") as f:
        f.write('')

def pause():
    global paused
    if mixer.music.get_busy() == True:
        mixer.music.pause()
        paused = True
        playButton.config(state='normal')
    else:
        pass

def set_vol(val):
    volume = int(val)/100
    try:
        mixer.music.set_volume(volume)
    except:
        pass

def skip():
    global paused
    mixer.music.stop()
    paused = False

def play():
    global ticker
    global nowPlaying
    try:
        song = MP3(f'song{ticker}.mp3')
        mixer.init(frequency=song.info.sample_rate, size=16, channels=2, buffer=4096)
        total = song.info.length
        total = round(total)
        musicScrubber.config(to=total)
        mins, secs = divmod(total, 60)
        mins = round(mins)
        secs = round(secs)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        durationLabel.config(text = timeformat)
        volume = int(volumeScale.get())/100
        mixer.music.set_volume(volume)
        mixer.music.load(f'song{ticker}.mp3')
        mixer.music.play()
        try:
            nowPlayingLabel.config(text= f'Now Playing: {nowPlaying}')
            with open("nowplaying.txt", "w", encoding='utf-8') as f:
                f.write(nowPlaying)
        except:
            nowPlaying = nowPlaying.encode('unicode_escape')
            nowPlayingLabel.config(text= f'Now Playing: {nowPlaying}')
            with open("nowplaying.txt", "w", encoding='utf-8') as f:
                f.write(str(nowPlaying))
        playButton.config(state='disabled')
        t2 = threading.Thread(target=scrubber)
        t2.start()
    except:
        with open("urllist.txt", "r") as f:
            url = f.readline().strip()
        if url:
            t3 = threading.Thread(target=download)
            t3.start()
        else:
            playButton.config(state='normal')
            print('No songs in queue')

def scrubber():
    global ticker
    global songPosition
    global paused
    update()
    try:
        os.remove(f'song{ticker - 1}.mp3')
    except:
        pass
    ticker += 1
    t3 = threading.Thread(target=download)
    t3.start()
    while mixer.music.get_busy():
        if paused == False:
            songPosition += 1
            musicScrubber.set(songPosition)
            time.sleep(1)
    songPosition = 0
    mixer.quit()
    t1 = threading.Thread(target=play)
    t1.start()

def download():
    global ticker
    global nowPlaying
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': f'song{ticker}.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]}
    skipButton.config(state='disabled')
    with open("urllist.txt", "r") as f:
        url = f.readline().strip()
    if url:
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                meta = ydl.extract_info(url, download=True)
                title = meta['title']
                nowPlaying = title
                skipButton.config(state='normal')
        except:
            update()
            t3 = threading.Thread(target=download)
            t3.start()
    else:
        try:
            while mixer.music.get_busy():
                skipButton.config(state='normal')
                time.sleep(1)
                with open("urllist.txt", "r") as f:
                    url = f.readline().strip()
                if url:
                    download()
                    break
                else:
                    pass
            paused = False
            if mixer.music.get_busy() == False:
                playButton.config(state='normal')
        except:
            pass

def add(event=None):
    url = urlTextBox.get()
    urlTextBox.delete(0, 'end')
    if url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be') or url.startswith('https://m.youtube.com'):
        if 'playlist' in url:
            playlist = get(url).text
            soup = BeautifulSoup(playlist, 'lxml')
            domain = 'https://www.youtube.com'
            for link in soup.find_all('a', {'dir': 'ltr'}):
                href = link.get('href')
                if href.startswith('/watch?'):
                    address = (domain + href)
                    address = address.split('&list')[0]
                    with open("urllist.txt", "a") as f:
                        f.write(f'{address}\n')
                    with open("songlist.txt", "a", encoding='utf-8') as f:
                        f.write(f'{link.string.strip()}\n')
            refresh()
        else:
            url = check(url)
            with open("urllist.txt", "a") as f:
                f.write(f'{url}\n')
            webpage = get(url).text
            soup = BeautifulSoup(webpage, 'lxml')
            title = soup.title.string
            with open("songlist.txt", "a", encoding='utf-8') as f:
                f.write(f'{title}\n')
            refresh()
    else:
        query = url.replace(' ', '+')
        searchVideo = get(f'https://www.youtube.com/results?search_query={query}').text
        soup = BeautifulSoup(searchVideo, 'lxml')
        for vid in soup.findAll('a', {'class':'yt-uix-tile-link'}, limit=5):
            if '/watch?v=' in vid['href']:
                song = 'https://www.youtube.com' + vid['href']
                url = check(song)
                title = vid['title']
                with open("urllist.txt", "a") as f:
                    f.write(f'{url}\n')
                with open("songlist.txt", "a", encoding='utf-8') as f:
                    f.write(f'{title}\n')
                refresh()
                break
            else:
                pass

def add_next(event=None):
    url = urlTextBox.get()
    urlTextBox.delete(0, 'end')
    if url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be') or url.startswith('https://m.youtube.com'):
        if 'playlist' in url:
            playlist = get(url).text
            soup = BeautifulSoup(playlist, 'lxml')
            domain = 'https://www.youtube.com'
            for link in soup.find_all('a', {'dir': 'ltr'}):
                href = link.get('href')
                if href.startswith('/watch?'):
                    address = (domain + href)
                    address = address.split('&list')[0]
                    with open("urllist.txt", "r") as f:
                        data = f.readlines()
                        data.insert(1, f'{address}\n')
                        data = ''.join(data)
                    with open("urllist.txt", "w") as f:
                        f.write(data)
                    with open("songlist.txt", "r", encoding='utf-8') as f:
                        data = f.readlines()
                        data.insert(1, f'{link.string.strip()}\n')
                        data = ''.join(data)
                    with open("songlist.txt", "w", encoding='utf-8') as f:
                        f.write(data)
            refresh()
        else:
            url = check(url)
            with open("urllist.txt", "r") as f:
                data = f.readlines()
                data.insert(1, f'{url}\n')
                data = ''.join(data)
            with open("urllist.txt", "w") as f:
                f.write(data)
            webpage = get(url).text
            soup = BeautifulSoup(webpage, 'lxml')
            title = soup.title.string
            with open("songlist.txt", "r", encoding='utf-8') as f:
                data = f.readlines()
                data.insert(1, f'{title}\n')
                data = ''.join(data)
            with open("songlist.txt", "w", encoding='utf-8') as f:
                f.write(data)
            refresh()
    else:
        query = url.replace(' ', '+')
        searchVideo = get(f'https://www.youtube.com/results?search_query={query}').text
        soup = BeautifulSoup(searchVideo, 'lxml')
        for vid in soup.findAll('a', {'class':'yt-uix-tile-link'}, limit=5):
            if '/watch?v=' in vid['href']:
                song = 'https://www.youtube.com' + vid['href']
                url = check(song)
                title = vid['title']
                with open("urllist.txt", "r") as f:
                    data = f.readlines()
                    data.insert(1, f'{url}\n')
                    data = ''.join(data)
                with open("urllist.txt", "w") as f:
                    f.write(data)
                with open("songlist.txt", "r", encoding='utf-8') as f:
                    data = f.readlines()
                    data.insert(1, f'{title}\n')
                    data = ''.join(data)
                with open("songlist.txt", "w", encoding='utf-8') as f:
                    f.write(data)
                refresh()
                break
            else:
                pass

def check(url):
    characters = len(url)
    if characters <= 43:
        return url
    else:
        url = url[:43]
        print('Video from playlist. Grabbing regular link. If you want to queue a playlist open the playlist page and use that url.')
        return url

def start():
    global paused
    if paused == True:
        mixer.music.unpause()
        paused = False
        playButton.config(state='disabled')
    else:
        download()
        t1 = threading.Thread(target=play)
        t1.start()

def del_song():
    selected = songTextBox.curselection()
    songTextBox.delete(selected)
    selected = int(selected[0])
    with open("songlist.txt", "r", encoding='utf-8') as f:
        data = f.readlines()
        data.pop(selected)
        data = ''.join(data)
    with open("songlist.txt", "w", encoding='utf-8') as f:
        f.write(data)
    with open("urllist.txt", "r") as f:
        data = f.readlines()
        data.pop(selected)
        data = ''.join(data)
    with open("urllist.txt", "w") as f:
        f.write(data)

window = tkinter.Tk()
width = window.winfo_screenwidth()
height = window.winfo_screenheight()
window.title('Smol Player')
window.configure(background = 'black')
musicScrubber = tkinter.Scale(window, from_=0, to=100, orient='horizontal', bg='black', width=5, fg = 'black', borderwidth=0, highlightbackground='black', length=635)
musicScrubber.bind('<ButtonRelease-1>', lambda x: set_scrub(musicScrubber.get()))
musicScrubber.place(x=38,y=40)
playButton = tkinter.Button(window, text = 'Play', width=10, command = start)
playButton.place(x=40,y=5)
tkinter.Button(window, text = 'Pause', width=10, command = pause).place(x=125,y=5)
skipButton = tkinter.Button(window, text = 'Skip', width=10, command = skip)
skipButton.place(x=210,y=5)
tkinter.Button(window, text = 'Add', width=5, command = add).place(x=685,y=72)
tkinter.Button(window, text = 'Next', width=5, command = add_next).place(x=685,y=102)
tkinter.Button(window, text = 'Delete', width=5, command = del_song).place(x=685,y=132)
tkinter.Button(window, text = 'Clear', width=10, command = clear).place(x=295,y=5)
volumeScale = tkinter.Scale(window, from_=100, to=0, orient='vertical', bg='black', fg = 'pink', borderwidth=0, highlightbackground='black', length=497, command=set_vol)
volumeScale.place(x=690,y=165)
volumeScale.set(25)
songTextBox = tkinter.Listbox(window, width=105, height=37, font = ("Ariel", 8))
songTextBox.place(x=40,y=105)
urlTextBox = tkinter.Entry(window, width=105, font = ("Ariel", 8))
urlTextBox.place(x=40,y=75)
window.bind('<Return>', add)
durationLabel = tkinter.Label(window, text = '0:0', bg = 'black', fg = 'pink', font = ("Ariel", 8))
durationLabel.place(x=680,y=52)
nowPlayingLabel = tkinter.Label(window, text = 'Now Playing:', bg = 'black', fg = 'pink', font = ("Ariel", 8))
nowPlayingLabel.place(x=37, y=35)
window.geometry('%dx%d+%d+%d' % (800, 700, width // 2 - 400, height // 2 - 340))
window.resizable(False, False)

clean_up()
refresh()
window.mainloop()
