import tkinter
import urllib.request
import youtube_dl
import requests
import os
import threading
import time
import codecs
from mutagen.mp3 import MP3
from pygame import mixer
from bs4 import BeautifulSoup

ticker = 0
paused = False
nowPlaying = ''

def clean_up():
    directory = os.getcwd()
    folder = os.listdir(directory)
    for file in folder:
        if file.endswith('.mp3'):
            os.remove(file)

def update():
    with open("urllist.txt", "r") as f:
        data = f.read().splitlines(True)
    with open("urllist.txt", "w") as f:
        f.writelines(data[1:])
    with codecs.open("songlist.txt", "r", encoding='utf-8') as f:
        data = f.read().splitlines(True)
    with codecs.open("songlist.txt", "w", encoding='utf-8') as f:
        f.writelines(data[1:])
    refresh()

def refresh():
    f = codecs.open("songlist.txt", "r", encoding="utf-8")
    songlist = f.read()
    songTextBox.delete('1.0', 'end')
    songTextBox.insert('end', songlist)
    f.close()

def clear():
    songTextBox.delete('1.0', 'end')
    file = open("songlist.txt", "w", encoding="utf-8")
    file.write('')
    file.close()
    file = open("urllist.txt", "w")
    file.write('')
    file.close()

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
        volume = int(volumeScale.get())/100
        mixer.music.set_volume(volume)
        mixer.music.load(f'song{ticker}.mp3')
        mixer.music.play()
        nowPlayingLabel.config(text= f'Now Playing: {nowPlaying}')
        file = open("nowplaying.txt", "w", encoding='utf-8')
        file.write(nowPlaying)
        file.close()
        try:
            os.remove(f'song{ticker - 1}.mp3')
        except:
            pass
        playButton.config(state='disabled')
        t2 = threading.Thread(target=scrubber)
        t2.start()
    except:
        with open("urllist.txt", "r") as f:
            url = f.readline().strip()
        if url:
            start()
        else:
            playButton.config(state='normal')
            print('No songs in queue')

def scrubber():
    global ticker
    song = MP3(f'song{ticker}.mp3')
    total = song.info.length
    total = round(total)
    musicScrubber.config(to=total)
    mins, secs = divmod(total, 60)
    mins = round(mins)
    secs = round(secs)
    timeformat = '{:02d}:{:02d}'.format(mins, secs)
    durationLabel.config(text = timeformat)
    update()
    ticker += 1
    t3 = threading.Thread(target=download)
    t3.start()
    while mixer.music.get_busy():
        time.sleep(1)
        amount = mixer.music.get_pos()
        amount = amount // 1000
        musicScrubber.set(amount)
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
    try:
        if url:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                meta = ydl.extract_info(url, download=True)
                title = meta['title']
                nowPlaying = title
                skipButton.config(state='normal')
        else:
            skipButton.config(state='normal')
            paused = False
            while mixer.music.get_busy():
                time.sleep(5)
                with open("urllist.txt", "r") as f:
                    url = f.readline().strip()
                if url:
                    download()
                    break
                else:
                    pass
            playButton.config(state='normal')

    except:
        update()
        t3 = threading.Thread(target=download)
        t3.start()

def add(event=None):
    url = urlTextBox.get()
    urlTextBox.delete(0, 'end')
    ydl_opts = {}
    if url.startswith('https://www.youtube.com/'):
        if 'playlist' in url:
            playlist = requests.get(url).text
            soup = BeautifulSoup(playlist, 'html.parser')
            domain = 'https://www.youtube.com'
            for link in soup.find_all("a", {"dir": "ltr"}):
                href = link.get('href')
                if href.startswith('/watch?'):
                    address = (domain + href)
                    address = address.split('&list')[0]
                    file = open("urllist.txt", "a")
                    file.write(address + '\n')
                    file.close()
                    file = open("songlist.txt", "a", encoding='utf-8')
                    file.write(f'{link.string.strip()} \n')
                    file.close()
            refresh()
        else:
            file = open("urllist.txt", "a")
            file.write(url + '\n')
            file.close()
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                meta = ydl.extract_info(url, download=False)
                title = meta['title']
                file = open("songlist.txt", "a", encoding='utf-8')
                file.write(f'{title} \n')
                file.close()
                refresh()
    else:
        print('Not a valid youtube link')

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

window = tkinter.Tk()
width = window.winfo_screenwidth()
height = window.winfo_screenheight()
window.title('Smol Player')
window.configure(background = 'black')
musicScrubber = tkinter.Scale(window, from_=0, to=100, orient='horizontal', bg='black', width=5, fg = 'black', borderwidth=0, highlightbackground='black', length=635)
musicScrubber.place(x=38,y=40)
playButton = tkinter.Button(window, text = 'Play', width=10, command = start)
playButton.place(x=40,y=5)
tkinter.Button(window, text = 'Pause', width=10, command = pause).place(x=125,y=5)
skipButton = tkinter.Button(window, text = 'Skip', width=10, command = skip)
skipButton.place(x=210,y=5)
tkinter.Button(window, text = 'Add', width=5, command = add).place(x=685,y=72)
tkinter.Button(window, text = 'Clear', width=10, command = clear).place(x=295,y=5)
volumeScale = tkinter.Scale(window, from_=100, to=0, orient='vertical', bg='black', fg = 'pink', label='Volume', borderwidth=0, highlightbackground='black', length=558, command=set_vol)
volumeScale.place(x=690,y=105)
volumeScale.set(25)
songTextBox = tkinter.Text(window, width=105, height=40, font = ("Ariel", 8))
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