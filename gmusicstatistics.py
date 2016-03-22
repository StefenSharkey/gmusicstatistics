#!/usr/bin/env python
# coding=utf-8

"""
gmusicstatistics

Copyright © 2016 Stefen Sharkey

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from __future__ import division
from collections import OrderedDict
from gmusicapi import Mobileclient
from PyQt4 import QtCore, QtGui

import json
import os
import sys


# NOTE: Debug mode makes processing VERY slow.
debug = False

create_file = False

gmusicstatistics_version = "0.1"
gmusicstatistics_build_date = "March 22, 2016"

api = Mobileclient()

genre_plays = OrderedDict([('Genre', []), ('Total Plays', []), ('Total Time', [])])
genre_name = []
genre_total_plays = []
genre_total_time = []

artist_plays = OrderedDict([('Artist', []), ('Total Plays', []), ('Total Time', [])])
artist_name = []
artist_total_plays = []
artist_total_time = []

album_plays = OrderedDict([('Artist', []), ('Album', []), ('Total Plays', []), ('Total Time', [])])
album_artist = []
album_name = []
album_total_plays = []
album_total_time = []

song_plays = OrderedDict([('Artist', []), ('Album', []), ('Song', []), ('Total Plays', []), ('Total Time', [])])
song_artist = []
song_album = []
song_name = []
song_total_plays = []
song_total_time = []


class GoogleMusicStatistics(QtGui.QMainWindow):
    # String containing all the songs.
    songs = ''

    # Pretty-printed string containing all the songs.
    songs_pprint = ''

    # Total time listened to music.
    time_listened_total = 0

    data = OrderedDict({})

    gui = QtGui.QApplication(sys.argv)
    main_widget = QtGui.QWidget()
    main_layout = QtGui.QVBoxLayout()
    scroll = QtGui.QScrollArea()
    scroll_layout = QtGui.QVBoxLayout()
    scroll_table = QtGui.QTableWidget()
    scroll_contents = QtGui.QWidget()
    scroll_contents_layout = QtGui.QVBoxLayout()
    text = QtGui.QLabel()

    def __init__(self, data):
        super(GoogleMusicStatistics, self).__init__()

        self.data = data
        self.menu = self.menuBar()
        self.music_dict = MusicDict(data)

        if create_file:
            self.file = self.init_file()

        self.init_ui()
        self.init_search()
        self.fill_all_arrays()
        self.fill_table(data)

    @staticmethod
    def init_file():
        if os.path.isfile('songlist.json'):
            os.remove('songlist.json')

        return open('songlist.json', 'w')

    def init_ui(self):
        self.setCentralWidget(self.main_widget)

        self.main_widget.setLayout(self.main_layout)
        self.main_layout.addWidget(self.scroll)
        self.main_layout.addWidget(self.text)

        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)

        self.scroll.setLayout(self.scroll_layout)

        self.scroll_contents.setLayout(self.scroll_contents_layout)

        self.setWindowTitle('Google Play Music Statistics')
        self.init_menu()
        self.center()
        self.show()

    def init_menu(self):
        menu_file = self.menu.addMenu('&File')
        menu_view = self.menu.addMenu('&View')
        menu_about = self.menu.addMenu('&Help')

        menu_play_types = QtGui.QMenu()
        play_types_group = QtGui.QActionGroup(self)

        # File menu
        action_quit = QtGui.QAction('&Exit', self,
                                    shortcut='Ctrl+W',
                                    statusTip='Exit application',
                                    triggered=self.close)

        # View menu
        action_play_types = QtGui.QAction('&Play Types', self)
        action_play_types.setMenu(menu_play_types)

        action_play_types_genres = QtGui.QAction('&Genres', self)
        action_play_types_genres.setCheckable(True)
        action_play_types_genres.setActionGroup(play_types_group)
        if self.music_dict.get_music_dict() == genre_plays:
            self.scroll_table.clearSelection()
            action_play_types_genres.setChecked(True)
        QtCore.QObject.connect(action_play_types_genres, QtCore.SIGNAL('triggered()'),
                               lambda: self.fill_table(genre_plays))

        action_play_types_artists = QtGui.QAction('&Artists', self)
        action_play_types_artists.setCheckable(True)
        action_play_types_artists.setActionGroup(play_types_group)
        if self.music_dict.get_music_dict() == artist_plays:
            self.scroll_table.clearSelection()
            action_play_types_artists.setChecked(True)
        QtCore.QObject.connect(action_play_types_artists, QtCore.SIGNAL('triggered()'),
                               lambda: self.fill_table(artist_plays))

        action_play_types_albums = QtGui.QAction('&Albums', self)
        action_play_types_albums.setCheckable(True)
        action_play_types_albums.setActionGroup(play_types_group)
        if self.music_dict.get_music_dict() == album_plays:
            self.scroll_table.clearSelection()
            action_play_types_albums.setChecked(True)
        QtCore.QObject.connect(action_play_types_albums, QtCore.SIGNAL('triggered()'),
                               lambda: self.fill_table(album_plays))

        action_play_types_songs = QtGui.QAction('&Songs', self)
        action_play_types_songs.setCheckable(True)
        action_play_types_songs.setActionGroup(play_types_group)
        if self.music_dict.get_music_dict() == song_plays:
            self.scroll_table.clearSelection()
            action_play_types_songs.setChecked(True)
        QtCore.QObject.connect(action_play_types_songs, QtCore.SIGNAL('triggered()'),
                               lambda: self.fill_table(song_plays))

        # Help menu
        action_about = QtGui.QAction('&About', self,
                                     statusTip="Show the application's About box",
                                     triggered=self.about)

        action_about_qt = QtGui.QAction('&About Qt', self,
                                        statusTip="Show the Qt library's About box",
                                        triggered=QtGui.qApp.aboutQt)

        menu_file.addAction(action_quit)

        menu_view.addMenu(menu_play_types)
        menu_play_types.addAction(action_play_types_genres)
        menu_play_types.addAction(action_play_types_artists)
        menu_play_types.addAction(action_play_types_albums)
        menu_play_types.addAction(action_play_types_songs)

        menu_about.addAction(action_about)
        menu_about.addAction(action_about_qt)

    def about(self):
        message = ("<h3><b>gmusicstatistics %s</b></h3>"
                   "<b>Build Date:</b> %s"
                   "<br />Developed by Stefen Sharkey"
                   "<br /><a href=\"https://github.com/Stefenatefun/gmusicstatistics\">GitHub</a>" %
                   (gmusicstatistics_version, gmusicstatistics_build_date))
        QtGui.QMessageBox.about(self, "About gmusicstatistics", message)

    def init_search(self):
        for song in api.get_all_songs(False, False):
            # TODO: Figure out a way that doesn't involve manually replacing chars.
            temp = self.str_to_json(song, single_to_double=True)

            if debug:
                print(temp + ",")

            self.add_all_plays(temp)

            self.songs += temp + ',\n'

            # Pretty-prints the song entry.
            temp = json.dumps(json.loads(temp, encoding='utf8'), indent=4, encoding='utf8')

            # Adds the time played from current song to total time.
            self.time_listened_total += self.add_total_plays(temp)

            if create_file:
                self.songs_pprint += temp + ',\n'

        if create_file:
            self.file.write(self.songs_pprint)
            self.file.close()

        self.text.setText(self.format_time(seconds=self.time_listened_total))

    @staticmethod
    def fill_all_arrays():
        genre_plays['Genre'] = genre_name
        genre_plays['Total Plays'] = genre_total_plays
        genre_plays['Total Time'] = genre_total_time

        artist_plays['Artist'] = artist_name
        artist_plays['Total Plays'] = artist_total_plays
        artist_plays['Total Time'] = artist_total_time

        album_plays['Artist'] = album_artist
        album_plays['Album'] = album_name
        album_plays['Total Plays'] = album_total_plays
        album_plays['Total Time'] = album_total_time

        song_plays['Artist'] = song_artist
        song_plays['Album'] = song_album
        song_plays['Song'] = song_name
        song_plays['Total Plays'] = song_total_plays
        song_plays['Total Time'] = song_total_time

    def fill_table(self, data):
        data.update([('Total Time (HH:MM:SS)', self.fill_formatted_total_time(data['Total Time']))])

        if debug:
            print(data['Total Time'])
            print(data.keys())

        self.scroll_table = QtGui.QTableWidget(len(data[data.keys()[0]]), len(data))
        self.scroll.setWidget(self.scroll_table)
        self.scroll_table.clearContents()
        self.scroll_table.setHorizontalHeaderLabels(data.keys())

        # for index, time in enumerate(data['Total Time']):
        #     data['Total Time'][index] = self.millis_to_seconds(int(time), truncate=True)

        for x, key in enumerate(data.keys()):
            if debug:
                print(unicode(x) + ' ' + unicode(key))

            for y, value in enumerate(data[key]):
                if debug:
                    print(unicode(y) + ' ' + unicode(value))
                genre = TableWidgetItem(unicode(value), value)
                self.scroll_table.setItem(y, x, genre)

        self.scroll_table.setSortingEnabled(True)
        self.scroll_table.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.scroll_table.resizeColumnsToContents()

    def fill_formatted_total_time(self, data):
        assert type(data) is list
        new_data = []

        for index, time in enumerate(data):
            if debug:
                print(data)
            new_data.append(self.format_time(seconds=time))

        return new_data

    def add_total_plays(self, songs):
        # Creates a JSON database of the current song.
        song = json.loads(songs, encoding='utf8')

        # Multiplies play count by the duration in milliseconds.
        return song['playCount'] * self.millis_to_seconds(int(song['durationMillis']))

    def add_all_plays(self, song):
        # Creates a JSON database of the current song.
        song = json.loads(song, encoding='utf8')

        # Creates entry for required info if it doesn't exist.
        if not genre_name.__contains__(song['genre']):
            genre_name.append(song['genre'])
        if not artist_name.__contains__(song['artist']):
            artist_name.append(song['artist'])
        if not album_name.__contains__(song['album']):
            album_name.append(song['album'])
        # if not song_name.__contains__(song['title']):
        song_name.append(song['title'])

        # Indexes.
        index_genre = genre_name.index(song['genre'])
        index_artist = artist_name.index(song['artist'])
        index_album = album_name.index(song['album'])
        index_song = len(song_name) - 1

        # Writes the total play count.
        if not len(genre_total_plays) == len(genre_name):
            genre_total_plays.append(0)
        genre_total_plays[index_genre] += int(song['playCount'])

        if not len(artist_total_plays) == len(artist_name):
            artist_total_plays.append(0)
        artist_total_plays[index_artist] += int(song['playCount'])

        if not len(album_total_plays) == len(album_name):
            album_total_plays.append(0)
        album_total_plays[index_album] += int(song['playCount'])

        if not len(song_total_plays) == len(song_name):
            song_total_plays.append(0)
        song_total_plays[index_song] += int(song['playCount'])

        # Writes the total time played.
        if not len(genre_total_time) == len(genre_total_plays):
            genre_total_time.append(0)
        genre_total_time[index_genre] += int(song['playCount']) * self.millis_to_seconds(int(song['durationMillis']))

        if not len(artist_total_time) == len(artist_total_plays):
            artist_total_time.append(0)
        artist_total_time[index_artist] += int(song['playCount']) * self.millis_to_seconds(int(song['durationMillis']))

        if not len(album_total_time) == len(album_total_plays):
            album_total_time.append(0)
        album_total_time[index_album] += int(song['playCount']) * self.millis_to_seconds(int(song['durationMillis']))

        if not len(song_total_time) == len(song_total_plays):
            song_total_time.append(0)
        song_total_time[index_song] += int(song['playCount']) * self.millis_to_seconds(int(song['durationMillis']))

        # Artist for album view.
        if not len(album_artist) == len(album_total_time):
            album_artist.append(song['artist'])

        # Artist and album for song view.
        if not len(song_artist) == len(song_total_time):
            song_artist.append(song['artist'])
        if not len(song_album) == len(song_artist):
            song_album.append(song['album'])

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtGui.QApplication.desktop()
        center_point = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def format_time(self, hours=int, minutes=int, seconds=int, millis=int):
        if debug:
            print(type(millis))
            print(millis)
            print(type(seconds))

        if ((type(hours) is type or hours == 0) and (type(minutes) is type or minutes == 0) and
                (type(seconds) is type or seconds == 0) and (type(millis) is type or millis == 0)):
            return "00:00:00"

        if type(millis) is not type and millis > 0:
            if type(seconds) is type:
                seconds = 0

            seconds += self.millis_to_seconds(millis)

        minutes_formatted, seconds_formatted = divmod(seconds, 60)
        hours_formatted, minutes_formatted = divmod(minutes_formatted, 60)
        time_formatted = "%02d:%02d:%02d" % (hours_formatted, minutes_formatted, seconds_formatted)

        if debug:
            print(time_formatted)

        return time_formatted

    @staticmethod
    def millis_to_seconds(millis, truncate=True):
        seconds = millis / 1000
        return int(seconds) if truncate else seconds

    @staticmethod
    def str_to_json(string, single_to_double=False):
        string = str(string)

        if single_to_double:
            string = string.replace('"', "'")

        return (string.replace("\\'", "'")
                .replace("{u'", '{"')
                .replace(": u'", ': "')
                .replace(': u"', ': "')
                .replace(", u'", ', "')
                .replace("[u'", '["')
                .replace("':", '":')
                .replace("',", '",')
                .replace("'}", '"}')
                .replace("']", '"]')
                .replace('\\u00fc', 'ü')
                .replace('\\u0142a', 'ł')
                .replace('\\u0107', 'ć')
                .replace('\\u0119', 'ę')
                .replace('\\u0144', 'ń')
                .replace('\\xa1', '¡')
                .replace('\\xb0', '°')
                .replace('\\xb4', '`')  # TODO: Consider making this a standard apostrophe.
                .replace('\\xc6', 'Æ')
                .replace('\\xe3', 'ã')
                .replace('\\xe4', 'ä')
                .replace('\\xe5', 'å')
                .replace('\\xe6', 'æ')
                .replace('\\xe7', 'ç')
                .replace('\\xe9', 'é')
                .replace('\\xf1', 'ñ')
                .replace('\\xf3w', 'ó')
                .replace('\\xf6', 'ö')
                .replace('\\xfc', 'ü')
                .replace('\\xff', 'ÿ')
                .replace(': False', ': "False"')
                .replace(': True', ': "True"'))


class MusicDict:
    music_play_type = OrderedDict({})

    def __init__(self, data):
        self.music_play_type = data

    def get_music_dict(self):
        return self.music_play_type

    def get_descriptor(self):
        if self.music_play_type == genre_plays:
            return 'genre'
        elif self.music_play_type == artist_plays:
            return 'artist'
        elif self.music_play_type == album_plays:
            return 'album'
        elif self.music_play_type == song_plays:
            return 'title'
        else:
            sys.exit('Descriptor not found.')

    def get_descriptor_array(self):
        if self.music_play_type == genre_plays:
            return genre_name
        elif self.music_play_type == artist_plays:
            return artist_name
        elif self.music_play_type == album_plays:
            return album_name
        elif self.music_play_type == song_plays:
            return song_name
        else:
            sys.exit('Descriptor array not found.')

    def get_total_plays_array(self):
        if self.music_play_type == genre_plays:
            return genre_total_plays
        elif self.music_play_type == artist_plays:
            return artist_total_plays
        elif self.music_play_type == album_plays:
            return album_total_plays
        elif self.music_play_type == song_plays:
            return song_total_plays
        else:
            sys.exit('Total plays array not found.')

    def get_total_time_array(self):
        if self.music_play_type == genre_plays:
            return genre_total_time
        elif self.music_play_type == artist_plays:
            return artist_total_time
        elif self.music_play_type == album_plays:
            return album_total_time
        elif self.music_play_type == song_plays:
            return song_total_time
        else:
            sys.exit('Total time array not found.')


class TableWidgetItem(QtGui.QTableWidgetItem):
    def __init__(self, text, sort_key):
        QtGui.QTableWidgetItem.__init__(self, text, QtGui.QTableWidgetItem.UserType)
        self.sort_key = sort_key

    def __lt__(self, other):
        return self.sort_key < other.sort_key


class LoginWindow(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.app = QtGui.QApplication(sys.argv)
        self.layout = QtGui.QVBoxLayout()
        username = QtGui.QWidget()
        username_layout = QtGui.QHBoxLayout()
        username_label = QtGui.QLabel('Username')
        self.username_text = QtGui.QLineEdit()
        password = QtGui.QWidget()
        password_layout = QtGui.QHBoxLayout()
        password_label = QtGui.QLabel('Password')
        self.password_text = QtGui.QLineEdit()
        self.error_message = QtGui.QLabel()
        button = QtGui.QWidget()
        button_layout = QtGui.QHBoxLayout()
        self.button_okay = QtGui.QPushButton('Okay')
        self.button_cancel = QtGui.QPushButton('Cancel')

        self.password_text.setEchoMode(QtGui.QLineEdit.Password)

        username.setLayout(username_layout)
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_text)

        password.setLayout(password_layout)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_text)

        self.error_message.setStyleSheet('QLabel { color: red; }')

        button.setLayout(button_layout)
        button_layout.addWidget(self.button_okay)
        button_layout.addWidget(self.button_cancel)

        QtCore.QObject.connect(self.button_okay, QtCore.SIGNAL('clicked()'), self.button_clicked)
        QtCore.QObject.connect(self.button_cancel, QtCore.SIGNAL('clicked()'), self.button_clicked)

        self.layout.addWidget(username)
        self.layout.addWidget(password)
        self.layout.addWidget(self.error_message)
        self.layout.addWidget(button)
        self.setLayout(self.layout)

        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.setSizeGripEnabled(False)
        self.setWindowTitle('Login to Google')
        self.show()
        self.app.exec_()

    def button_clicked(self):
        if self.sender() == self.button_okay:
            if not api.login(str(self.username_text.text()), str(self.password_text.text()),
                             Mobileclient.FROM_MAC_ADDRESS):
                self.error_message.setText('Username and/or password incorrect.')
            else:
                self.done(0)
        elif self.sender() == self.button_cancel:
            sys.exit()


def main():
    LoginWindow()
    app = QtGui.QApplication(sys.argv)
    GoogleMusicStatistics(genre_plays)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
