#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pafy
import tkinter
import threading
import time
import codecs
import sys
from random import shuffle
from os import chdir, getcwd
from vlc import Instance, State
from tkinter import messagebox
from requests import get
from bs4 import BeautifulSoup

class SmolPlayer(threading.Thread):
    def __init__(self):
        super(SmolPlayer, self).__init__()
        directory = getcwd()
        chdir(directory)
        self.ticker = 0
        self.paused = False
        self.nowPlaying = ''
        self.songPosition = 0
        self.player = ''
        self.volume = 50
        self.showVideo = False
        self.run = True
        self.window = tkinter.Tk()
        self.window.title('SmolPlayer')
        self.window.configure(background = 'black')
        self.width, self.height = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.geometry('%dx%d+%d+%d' % (800, 700, self.width // 2 - 400, self.height // 2 - 340))
        self.window.resizable(False, False)

        tkinter.Button(self.window, text = 'Pause', width=10, command = self.pause).place(x=125,y=5)
        tkinter.Button(self.window, text = 'Add', width=5, command = self.add).place(x=685,y=72)
        tkinter.Button(self.window, text = 'Next', width=5, command = self.add_next).place(x=685,y=102)
        tkinter.Button(self.window, text = 'Shuffle', width=10, command = self.shuffle).place(x=295,y=5)
        tkinter.Button(self.window, text = 'Clear', width=10, command = self.clear).place(x=380,y=5)

        self.showVideoCheck = tkinter.Checkbutton(self.window, text='Show Video (WIP)', bg='black', fg='pink', highlightbackground='black', command = self.allow_video)
        self.showVideoCheck.place(x=678, y=30)
        self.playButton = tkinter.Button(self.window, text = 'Play', width=10, command = self.start)
        self.playButton.place(x=40,y=5)
        self.skipButton = tkinter.Button(self.window, text = 'Skip', width=10, command = self.skip)
        self.skipButton.place(x=210,y=5)
        self.deletButton = tkinter.Button(self.window, text = 'Delete', width=5, command = self.delete_song)
        self.deletButton.place(x=685,y=132)
        self.volumeScale = tkinter.Scale(self.window, from_=100, to=0, orient='vertical', bg='black', fg = 'pink', borderwidth=0, highlightbackground='black', length=497, command= self.set_volume)
        self.volumeScale.place(x=690,y=165)
        self.volumeScale.set(50)
        self.musicScrubber = tkinter.Scale(self.window, from_=0.0, to=1.0, resolution=0.0001, orient='horizontal', bg='black', width=5, fg = 'black', borderwidth=0, highlightbackground='black', length=635)
        self.musicScrubber.place(x=38,y=40)
        self.queueBox = tkinter.Listbox(self.window, width=105, height=37, font = ("Ariel", 8))
        self.queueBox.place(x=40,y=105)
        self.urlEntry = tkinter.Entry(self.window, width=105, font = ("Ariel", 8))
        self.urlEntry.place(x=40,y=75)
        self.durationLabel = tkinter.Label(self.window, text = '00:00:00', bg = 'black', fg = 'pink', font = ("Ariel", 8))
        self.durationLabel.place(x=680,y=52)
        self.nowPlayingLabel = tkinter.Label(self.window, text = 'Now Playing:', bg = 'black', fg = 'pink', font = ("Ariel", 8))
        self.nowPlayingLabel.place(x=37, y=35)

        self.musicScrubber.bind('<ButtonRelease-1>', lambda x: self.set_scrubber(self.musicScrubber.get()))
        self.urlEntry.bind('<Return>', self.add)
        self.urlEntry.bind('<ButtonRelease-3>', self.paste)
        self.queueBox.bind('<Delete>', self.delete_song)

        self.refresh()
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def start(self):
        if self.paused == True:
            self.paused = False
            self.player.set_pause(0)
            self.playButton.config(state='disabled')
        else:
            t1 = threading.Thread(target=self.play)
            t1.start()

    def play(self):
        with open('urllist.txt', 'r') as f:
            url = f.readline().strip()
        if url:
            try:
                video = pafy.new(url)
                best = video.getbest()
                playurl = best.url
                if self.showVideo == False:
                    vInstance = Instance('--novideo')
                else:
                    vInstance = Instance()
                self.player = vInstance.media_player_new()
                media = vInstance.media_new(playurl)
                self.player.set_media(media)
                self.player.play()
                self.player.audio_set_volume(int(self.volume))
                self.nowPlaying = video.title
                self.durationLabel.config(text = video.duration)
                h, m, s = video.duration.split(':')
                duration = int(h) * 3600 + int(m) * 60 + int(s)
                ticker = 1 / duration
                try:
                    self.nowPlayingLabel.config(text=f'Now Playing: {self.nowPlaying}')
                    with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                        f.write(self.nowPlaying + '   ')
                except:
                    self.nowPlaying = self.nowPlaying.encode('unicode_escape')
                    self.nowPlayingLabel.config(text=f'Now Playing: {self.nowPlaying}')
                    with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                        f.write(str(self.nowPlaying) + '   ')
                self.update()
                self.playButton.config(state='disabled')
                time.sleep(3)
                self.songPosition = self.player.get_position()
                while self.player.get_state() == State.Playing or self.player.get_state() == State.Paused:
                    if self.paused == False:
                        self.songPosition += ticker
                        self.musicScrubber.set(self.songPosition)
                        time.sleep(1)
                    if self.run == False:
                        self.player.stop()
                        sys.exit()
                self.songPosition = 0
                self.musicScrubber.set(self.songPosition)
                self.player.stop()
                self.play()
            except Exception as error:
                tkinter.messagebox.showwarning(title='Warning', message=error)
                self.update()
                self.play()
        else:
            self.playButton.config(state='normal')
            self.nowPlayingLabel.config(text=f'Now Playing:')
            with open('nowPlaying.txt', 'w', encoding='utf-8') as f:
                f.write('No songs playing. Donate to have your song played on stream.   ')

    def shuffle(self):
        with open('songlist.txt', 'r', encoding='utf-8') as f:
            songs = f.readlines()
        with open('urllist.txt', 'r', encoding='utf-8') as f:
            urls = f.readlines()
        combined = list(zip(songs, urls))
        shuffle(combined)
        songs[:], urls[:] = zip(*combined)
        with open('songlist.txt', 'w', encoding='utf-8') as f:
            for song in songs:
                f.write(song)
        with open('urllist.txt', 'w') as f:
            for url in urls:
                f.write(url)
        self.refresh()

    def allow_video(self):
        self.showVideo = not self.showVideo

    def pause(self):
        if self.player.get_state() == State.Playing:
            self.player.set_pause(1)
            self.paused = True
            self.playButton.config(state='normal')
        else:
            pass

    def set_volume(self, amount):
        try:
            self.player.audio_set_volume(int(amount))
            self.volume = amount
        except:
            pass

    def set_scrubber(self, amount):
        self.player.set_position(amount)
        self.songPosition = amount

    def skip(self):
        self.player.stop()
        self.paused = False

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
                            data.insert(0, f'{url}\n')
                            data = ''.join(data)
                        with open("urllist.txt", "w") as f:
                            f.write(data)
                        with open("songlist.txt", "r", encoding='utf-8') as f:
                            data = f.readlines()
                            data.insert(0, f'{vid.string.strip()}\n')
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
                    data.insert(0, f'{url}\n')
                    data = ''.join(data)
                with open("urllist.txt", "w") as f:
                    f.write(data)
                with open("songlist.txt", "r", encoding='utf-8') as f:
                    data = f.readlines()
                    data.insert(0, f'{title}\n')
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
                        data.insert(0, f'{url}\n')
                        data = ''.join(data)
                    with open("urllist.txt", "w") as f:
                        f.write(data)
                    with open("songlist.txt", "r", encoding='utf-8') as f:
                        data = f.readlines()
                        data.insert(0, f'{title}\n')
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
            messagebox.showwarning("SmolPlayer", "Song from playlist. If you wanted to add a playlist please use the playlist page url instead.")
            url = url[:43]
            return url


    def delete_song(self, event=None):
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


    def paste(self, event=None):
        try:
            self.clipboard = self.window.clipboard_get()
            self.urlEntry.insert(0, self.clipboard)
            self.window.clipboard_clear()
            self.add()
        except:
            pass

    def clear(self):
        self.queueBox.delete(0, 'end')
        with open("songlist.txt", "w", encoding="utf-8") as f:
            f.write('')
        with open("urllist.txt", "w") as f:
            f.write('')

    def stopped(self):
        while self._stop_event.is_set() == False:
            continue

    def on_closing(self):
        try:
            self.run = False
            self.player.set_pause(0)
            self.window.destroy()
        except:
            self.window.destroy()

if __name__ == '__main__':
    SmolPlayer()
