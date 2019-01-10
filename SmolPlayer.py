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

class SmolPlayer():
    def __init__(self):
        self.ticker = 0
        self.paused = False
        self.nowPlaying = ''
        self.songPosition = 0
        self.window = tkinter.Tk()
        self.window.title('Smol Player')
        self.window.configure(background = 'black')
        self.width, self.height = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.geometry('%dx%d+%d+%d' % (800, 700, self.width // 2 - 400, self.height // 2 - 340))
        self.window.resizable(False, False)

        tkinter.Button(self.window, text = 'Pause', width=10, command = self.pause).place(x=125,y=5)
        tkinter.Button(self.window, text = 'Add', width=5, command = self.add).place(x=685,y=72)
        tkinter.Button(self.window, text = 'Next', width=5, command = self.add_next).place(x=685,y=102)
        tkinter.Button(self.window, text = 'Delete', width=5, command = self.delete_song).place(x=685,y=132)
        tkinter.Button(self.window, text = 'Clear', width=10, command = self.clear).place(x=295,y=5)

        self.playButton = tkinter.Button(self.window, text = 'Play', width=10, command = self.start)
        self.playButton.place(x=40,y=5)
        self.skipButton = tkinter.Button(self.window, text = 'Skip', width=10, command = self.skip)
        self.skipButton.place(x=210,y=5)
        self.volumeScale = tkinter.Scale(self.window, from_=100, to=0, orient='vertical', bg='black', fg = 'pink', borderwidth=0, highlightbackground='black', length=497, command= self.set_volume)
        self.volumeScale.place(x=690,y=165)
        self.volumeScale.set(25)
        self.musicScrubber = tkinter.Scale(self.window, from_=0, to=100, orient='horizontal', bg='black', width=5, fg = 'black', borderwidth=0, highlightbackground='black', length=635)
        self.musicScrubber.place(x=38,y=40)
        self.queueBox = tkinter.Listbox(self.window, width=105, height=37, font = ("Ariel", 8))
        self.queueBox.place(x=40,y=105)
        self.urlEntry = tkinter.Entry(self.window, width=105, font = ("Ariel", 8))
        self.urlEntry.place(x=40,y=75)
        self.durationLabel = tkinter.Label(self.window, text = '0:0', bg = 'black', fg = 'pink', font = ("Ariel", 8))
        self.durationLabel.place(x=680,y=52)
        self.nowPlayingLabel = tkinter.Label(self.window, text = 'Now Playing:', bg = 'black', fg = 'pink', font = ("Ariel", 8))
        self.nowPlayingLabel.place(x=37, y=35)

        self.musicScrubber.bind('<ButtonRelease-1>', lambda x: self.set_scrubber(self.musicScrubber.get()))
        self.urlEntry.bind('<Return>', self.add)
        self.urlEntry.bind('<ButtonRelease-3>', self.paste)

        self.clean_up()
        self.refresh()
        self.window.mainloop()

    def add(self, event=None):
        url = self.urlEntry.get()
        self.urlEntry.delete(0, 'end')
        if url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be') or url.startswith('https://m.youtube.com'):
            if 'playlist' in url:
                playlist = get(url).text
                soup = BeautifulSoup(playlist, 'lxml')
                for vid in soup.find_all('a', {'dir': 'ltr'}):
                    if '/watch' in vid['href']:
                        url = ('https://www.youtube.com' + vid['href']).split('&list')[0]
                        with open('urllist.txt', 'a') as f:
                            f.write(f'{url}\n')
                        with open('songlist.txt', 'a', encoding='utf-8') as f:
                            f.write(f'{vid.string.strip()}\n')
                self.refresh()
            else:
                url = self.check(url)
                webpage = get(url).text
                soup = BeautifulSoup(webpage, 'lxml')
                title = soup.title.string
                with open('urllist.txt', 'a') as f:
                    f.write(f'{url}\n')
                with open('songlist.txt', 'a', encoding='utf-8') as f:
                    f.write(f'{title}\n')
                self.refresh()
        else:
            query = url.replace(' ', '+')
            video = get(f'https://www.youtube.com/results?search_query={query}').text
            soup = BeautifulSoup(video, 'lxml')
            for vid in soup.find_all('a', {'class':'yt-uix-tile-link'}):
                if '/watch' in vid['href']:
                    url = 'https://www.youtube.com' + vid['href']
                    songTitle = vid['title']
                    url = self.check(url)
                    with open("urllist.txt", "a") as f:
                        f.write(f'{url}\n')
                    with open("songlist.txt", "a", encoding='utf-8') as f:
                        f.write(f'{songTitle}\n')
                    self.refresh()
                    break
                else:
                    pass

    def add_next(self):
        url = self.urlEntry.get()
        self.urlEntry.delete(0, 'end')
        if url.startswith('https://www.youtube.com/') or url.startswith('https://youtu.be') or url.startswith('https://m.youtube.com'):
            if 'playlist' in url:
                playlist = get(url).text
                soup = BeautifulSoup(playlist, 'lxml')
                for vid in soup.find_all('a', {'dir': 'ltr'}):
                    if '/watch' in vid['href']:
                        url = ('https://www.youtube.com' + vid['href']).split('&list')[0]
                        with open("urllist.txt", "r") as f:
                            data = f.readlines()
                            data.insert(1, f'{url}\n')
                            data = ''.join(data)
                        with open("urllist.txt", "w") as f:
                            f.write(data)
                        with open("songlist.txt", "r", encoding='utf-8') as f:
                            data = f.readlines()
                            data.insert(1, f'{vid.string.strip()}\n')
                            data = ''.join(data)
                        with open("songlist.txt", "w", encoding='utf-8') as f:
                            f.write(data)
                self.refresh()
            else:
                url = self.check(url)
                webpage = get(url).text
                soup = BeautifulSoup(webpage, 'lxml')
                title = soup.title.string
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
                self.refresh()
        else:
            query = url.replace(' ', '+')
            video = get(f'https://www.youtube.com/results?search_query={query}').text
            soup = BeautifulSoup(video, 'lxml')
            for vid in soup.find_all('a', {'class':'yt-uix-tile-link'}):
                if '/watch' in vid['href']:
                    url = 'https://www.youtube.com' + vid['href']
                    title = vid['title']
                    url = self.check(url)
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
                    self.refresh()
                    break
                else:
                    pass

    def update(self):
        with open("urllist.txt", "r") as f:
            data = f.readlines()
        with open("urllist.txt", "w") as f:
            f.writelines(data[1:])
        with codecs.open("songlist.txt", "r", encoding='utf-8') as f:
            data = f.readlines()
        with codecs.open("songlist.txt", "w", encoding='utf-8') as f:
            f.writelines(data[1:])
        self.refresh()

    def refresh(self):
        with open("songlist.txt", "r", encoding='utf-8') as f:
            songlist = f.readlines()
            self.queueBox.delete(0, 'end')
            for line in songlist:
                try:
                    self.queueBox.insert('end', line)
                except:
                    song = line.encode('unicode_escape')
                    self.queueBox.insert('end', f'{song}\n')

    def check(self, url):
        characters = len(url)
        if characters <= 43:
            return url
        else:
            url = url[:43]
            print('Video from playlist. Grabbing regular link. If you want to queue a playlist use the playlist page url.')
            return url

    def set_volume(self, amount):
        volume = int(amount)/100
        try:
            mixer.music.set_volume(volume)
        except:
            pass

    def set_scrubber(self, amount):
        mixer.music.rewind()
        mixer.music.set_pos(amount)
        self.musicScrubber.set(amount)
        self.songPosition = amount

    def delete_song(self):
        isBusy = self.check_mixer()
        selected = self.queueBox.curselection()
        if isBusy:
            selected = int(selected[0])
            if selected == 0:
                return
            else:
                selected = self.queueBox.curselection()
                self.queueBox.delete(selected)
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
        else:
            self.queueBox.delete(selected)
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

    def check_mixer(self):
        try:
            if mixer.music.get_busy():
                return True
            else:
                return False
        except:
            return False

    def paste(self, event=None):
        try:
            self.clipboard = self.window.clipboard_get()
            self.urlEntry.insert(0, self.clipboard)
            self.window.clipboard_clear()
            self.add()
        except:
            print('Clipboard Empty')

    def clear(self):
        isBusy = self.check_mixer()
        if isBusy:
            self.queueBox.delete(1, 'end')
            with open("urllist.txt", "r") as f:
                data = f.readline()
                data = ''.join(data)
            with open("urllist.txt", "w") as f:
                f.write(data)
            with open("songlist.txt", "r", encoding='utf-8') as f:
                data = f.readline()
                data = ''.join(data)
            with open("songlist.txt", "w", encoding='utf-8') as f:
                f.write(data)
        else:
            self.queueBox.delete(0, 'end')
            with open("songlist.txt", "w", encoding="utf-8") as f:
                f.write('')
            with open("urllist.txt", "w") as f:
                f.write('')

    def pause(self):
        if mixer.music.get_busy():
            mixer.music.pause()
            self.paused = True
            self.playButton.config(state='normal')
        else:
            pass

    def skip(self):
        mixer.music.stop()
        self.paused = False

    def clean_up(self):
        directory = os.getcwd()
        folder = os.listdir(directory)
        for file in folder:
            if file.endswith('.mp3'):
                os.remove(file)

    def start(self):
        if self.paused:
            self.paused = False
            mixer.music.unpause()
            self.playButton.config(state='disabled')
        else:
            self.download()
            t1 = threading.Thread(target=self.play)
            t1.start()

    def download(self):
        youtube_dl.utils.std_headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:64.0) Gecko/20100101 Firefox/64.0'
        ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'song{self.ticker}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'opts': ['--rm-cache-dir']
        }
        self.skipButton.config(state='disabled')
        with open('urllist.txt', 'r') as f:
            url = f.readline().strip()
        if url:
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    self.nowPlaying = info['title']
                    self.skipButton.config(state='normal')
            except:
                self.update()
                t3 = threading.Thread(target=self.download)
                t3.start()
        else:
            try:
                if mixer.music.get_busy():
                    self.skipButton.config(state='normal')
                while mixer.music.get_busy():
                    time.sleep(1)
                    with open('urllist.txt', 'r') as f:
                        url = f.readline().strip()
                    if url:
                        self.download()
                        break
                    else:
                        pass
                self.paused = False
                if mixer.music.get_busy() == False:
                    playButton.config(state='normal')
            except:
                pass

    def play(self):
        try:
            self.playButton.config(state='disabled')
            song = MP3(f'song{self.ticker}.mp3')
            songSampleRate = song.info.sample_rate
            songDuration = round(song.info.length)
            mins, secs = divmod(songDuration, 60)
            mins = round(mins)
            secs = round(secs)
            timeFormat = '{:02d}:{:02d}'.format(mins, secs)
            volume = int(self.volumeScale.get())/100
            self.durationLabel.config(text=timeFormat)
            self.musicScrubber.config(to=songDuration)
            mixer.init(frequency=songSampleRate, size=16, channels=2, buffer=4096)
            mixer.music.set_volume(volume)
            mixer.music.load(f'song{self.ticker}.mp3')
            mixer.music.play()
            try:
                self.nowPlayingLabel.config(text=f'Now Playing: {self.nowPlaying}')
                with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                    f.write(self.nowPlaying)
            except:
                self.nowPlaying = nowPlaying.encode('unicode_escape')
                self.nowPlayingLabel.config(text=f'Now Playing: {self.nowPlaying}')
                with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                    f.write(str(self.nowPlaying))
            t2 = threading.Thread(target=self.scrubber)
            t2.start()
        except:
            print('No songs in queue')
            self.playButton.config(state='normal')

    def scrubber(self):
        self.update()
        try:
            os.remove(f'song{self.ticker - 1}.mp3')
        except:
            pass
        self.ticker += 1
        t3 = threading.Thread(target=self.download)
        t3.start()
        while mixer.music.get_busy():
            if self.paused == False:
                self.songPosition += 1
                self.musicScrubber.set(self.songPosition)
                time.sleep(1)
        mixer.quit()
        self.songPosition = 0
        t1 = threading.Thread(target=self.play)
        t1.start()


if __name__ == '__main__':
    SmolPlayer()
