#!/usr/bin/env python

"""
Copyright 2016 Stefen Sharkey

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import os
import sys

import pandas as pd
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import qApp, QAction, QActionGroup, QApplication, QLabel, QMainWindow, QMenu, QMessageBox, \
    QScrollArea, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QAbstractScrollArea, QFileDialog
from gmusicapi import Mobileclient

# NOTE: Debug mode makes processing VERY slow.
debug = False

create_file = False

gmusicstatistics_version = "0.1.1"
gmusicstatistics_build_date = "May 29, 2020"

api = Mobileclient()

plays = dict([("Genre", dict([("Genre", []), ("Total Plays", []), ("Total Time", [])])),
              ("Artist", dict([("Artist", []), ("Total Plays", []), ("Total Time", [])])),
              ("Album", dict([("Artist", []), ("Album", []), ("Total Plays", []), ("Total Time", [])])),
              ("Song", dict([("Artist", []), ("Album", []), ("Song", []), ("Total Plays", []), ("Total Time", [])]))])


class GoogleMusicStatistics(QMainWindow):
    # String containing all the songs.
    songs = ""

    # Pretty-printed string containing all the songs.
    songs_pprint = ""

    # Total time listened to music.
    time_listened_total = 0

    active_table: str

    gui = QApplication(sys.argv)
    main_widget = QWidget()
    main_layout = QVBoxLayout()
    scroll = QScrollArea()
    scroll_layout = QVBoxLayout()
    scroll_table = QTableWidget()
    scroll_contents = QWidget()
    scroll_contents_layout = QVBoxLayout()
    text = QLabel()

    def __init__(self, data: dict, active_table: str):
        super(GoogleMusicStatistics, self).__init__()

        self.menu = self.menuBar()
        self.active_table = active_table

        if create_file:
            self.file = self.init_file()

        self.init_search()
        self.fill_table(data)

        self.scroll_table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.scroll_table.resizeColumnsToContents()
        self.init_ui()

    @staticmethod
    def init_file():
        if os.path.isfile("songlist.json"):
            os.remove("songlist.json")

        return open("songlist.json", "w")

    def init_ui(self):
        self.setCentralWidget(self.main_widget)

        self.main_widget.setLayout(self.main_layout)
        self.main_layout.addWidget(self.scroll)
        self.main_layout.addWidget(self.text)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidgetResizable(True)

        self.scroll.setLayout(self.scroll_layout)

        self.scroll_contents.setLayout(self.scroll_contents_layout)

        self.setWindowTitle("Google Play Music Statistics")
        self.init_menu()
        self.setMinimumSize(self.scroll_table.sizeHint())
        self.center()
        self.show()

    def init_menu(self):
        menu_file = self.menu.addMenu("&File")
        menu_view = self.menu.addMenu("&View")
        menu_about = self.menu.addMenu("&Help")

        menu_play_types = QMenu()
        play_types_group = QActionGroup(self)

        # File menu
        action_export_to_csv = QAction("&Export to CSV...", self,
                                       shortcut="Ctrl+S",
                                       statusTip="Export content to a CSV file.",
                                       triggered=lambda: self.export_to_csv())

        action_quit = QAction("&Exit", self,
                              shortcut="Ctrl+W",
                              statusTip="Exit application",
                              triggered=self.close)

        # View menu
        action_play_types = QAction("&Play Types", self)
        action_play_types.setMenu(menu_play_types)

        action_play_types_genres = QAction("&Genres", play_types_group,
                                           checkable=True,
                                           triggered=lambda: self.fill_table(plays["Genre"], "genre"))
        action_play_types_artists = QAction("&Artists", play_types_group,
                                            checkable=True,
                                            triggered=lambda: self.fill_table(plays["Artist"], "artist"))
        action_play_types_albums = QAction("&Albums", play_types_group,
                                           checkable=True,
                                           triggered=lambda: self.fill_table(plays["Album"], "album"))
        action_play_types_songs = QAction("&Songs", play_types_group,
                                          checkable=True,
                                          triggered=lambda: self.fill_table(plays["Song"], "song"))

        action_play_types_genres.setChecked(True)

        # Help menu
        action_about = QAction("&About", self,
                               statusTip="Show the application's About box",
                               triggered=self.about)

        action_about_qt = QAction("&About Qt", self,
                                  statusTip="Show the Qt library's About box",
                                  triggered=qApp.aboutQt)

        menu_file.addAction(action_export_to_csv)
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
                   "<br /><a href=\"https://github.com/StefenSharkey/gmusicstatistics\">GitHub</a>" %
                   (gmusicstatistics_version, gmusicstatistics_build_date))
        QMessageBox.about(self, "About gmusicstatistics", message)

    def init_search(self):
        for song in api.get_all_songs(incremental=False):
            temp = json.dumps(song)

            if debug:
                print(str(temp))

            self.add_all_plays(temp)

            self.songs += temp + ",\n"

            # Pretty-prints the song entry.
            temp = json.dumps(json.loads(temp), indent=4)

            # Adds the time played from current song to total time.
            self.time_listened_total += self.add_total_plays(temp)

            if create_file:
                self.songs_pprint += temp + ",\n"

        if create_file:
            self.file.write(self.songs_pprint)
            self.file.close()

        self.text.setText(self.format_seconds_to_time(self.time_listened_total))

    def fill_table(self, data: dict, active_table: str = None):
        if active_table is not None:
            self.active_table = active_table

        data.update([("Total Time (HH:MM:SS)", self.fill_formatted_total_time(data["Total Time"]))])

        if debug:
            print(data["Total Time"])
            print(data.keys())

        self.scroll_table = QTableWidget(len(data[list(data.keys())[0]]), len(data))
        self.scroll.setWidget(self.scroll_table)
        self.scroll_table.clearContents()
        self.scroll_table.setHorizontalHeaderLabels(data.keys())

        for x, key in enumerate(data.keys()):
            if debug:
                print(x, " ", key)

            for y, value in enumerate(data[key]):
                if debug:
                    print(y, " ", value)

                genre = TableWidgetItem(str(value), value)
                self.scroll_table.setItem(y, x, genre)

        self.scroll_table.setSortingEnabled(True)
        self.scroll_table.sortByColumn(0, Qt.AscendingOrder)
        self.scroll_table.resizeColumnsToContents()

    def fill_formatted_total_time(self, data):
        assert type(data) is list
        new_data = []

        for index, time in enumerate(data):
            if debug:
                print(data)
            new_data.append(self.format_seconds_to_time(time))

        return new_data

    def add_total_plays(self, songs):
        # Creates a JSON database of the current song.
        song = json.loads(songs)

        # Multiplies play count by the duration in milliseconds.
        try:
            return int(song["playCount"]) * self.millis_to_seconds(int(song["durationMillis"]))
        except KeyError:
            return 0

    def add_all_plays(self, song: str):
        # Creates a JSON database of the current song.
        song = json.loads(song)

        # Creates entry for required info if it doesn't exist.
        try:
            if not plays["Genre"]["Genre"].__contains__(song["genre"]):
                plays["Genre"]["Genre"].append(song["genre"])
        except KeyError:
            if not plays["Genre"]["Genre"].__contains__(""):
                plays["Genre"]["Genre"].append("")

        if not plays["Artist"]["Artist"].__contains__(song["artist"]):
            plays["Artist"]["Artist"].append(song["artist"])
        if not plays["Album"]["Album"].__contains__(song["album"]):
            plays["Album"]["Album"].append(song["album"])
        plays["Song"]["Song"].append(song["title"])

        # Indexes.
        index_genre = plays["Genre"]["Genre"].index(song["genre"] if "genre" in song else "")
        index_artist = plays["Artist"]["Artist"].index(song["artist"])
        index_album = plays["Album"]["Album"].index(song["album"])
        index_song = len(plays["Song"]["Song"]) - 1

        try:
            play_count = int(song["playCount"])
        except KeyError:
            play_count = 0

        # Writes the total play count.
        if not len(plays["Genre"]["Total Plays"]) == len(plays["Genre"]["Genre"]):
            plays["Genre"]["Total Plays"].append(0)
        plays["Genre"]["Total Plays"][index_genre] += play_count

        if not len(plays["Artist"]["Total Plays"]) == len(plays["Artist"]["Artist"]):
            plays["Artist"]["Total Plays"].append(0)
        plays["Artist"]["Total Plays"][index_artist] += play_count

        if not len(plays["Album"]["Total Plays"]) == len(plays["Album"]["Album"]):
            plays["Album"]["Total Plays"].append(0)
        plays["Album"]["Total Plays"][index_album] += play_count

        if not len(plays["Song"]["Total Plays"]) == len(plays["Song"]["Song"]):
            plays["Song"]["Total Plays"].append(0)
        plays["Song"]["Total Plays"][index_song] += play_count

        # Writes the total time played.
        if not len(plays["Genre"]["Total Time"]) == len(plays["Genre"]["Total Plays"]):
            plays["Genre"]["Total Time"].append(0)
        plays["Genre"]["Total Time"][index_genre] += play_count * self.millis_to_seconds(int(song["durationMillis"]))

        if not len(plays["Artist"]["Total Time"]) == len(plays["Artist"]["Total Plays"]):
            plays["Artist"]["Total Time"].append(0)
        plays["Artist"]["Total Time"][index_artist] += play_count * self.millis_to_seconds(int(song["durationMillis"]))

        if not len(plays["Album"]["Total Time"]) == len(plays["Album"]["Total Plays"]):
            plays["Album"]["Total Time"].append(0)
        plays["Album"]["Total Time"][index_album] += play_count * self.millis_to_seconds(int(song["durationMillis"]))

        if not len(plays["Song"]["Total Time"]) == len(plays["Song"]["Total Plays"]):
            plays["Song"]["Total Time"].append(0)
        plays["Song"]["Total Time"][index_song] += play_count * self.millis_to_seconds(int(song["durationMillis"]))

        # Artist for album view.
        if not len(plays["Album"]["Artist"]) == len(plays["Album"]["Total Time"]):
            plays["Album"]["Artist"].append(song["artist"])

        # Artist and album for song view.
        if not len(plays["Song"]["Artist"]) == len(plays["Song"]["Total Time"]):
            plays["Song"]["Artist"].append(song["artist"])
        if not len(plays["Song"]["Album"]) == len(plays["Song"]["Artist"]):
            plays["Song"]["Album"].append(song["album"])

    def export_to_csv(self):
        active_dict = ({
            "genre": plays["Genre"],
            "artist": plays["Artist"],
            "album": plays["Album"],
            "song": plays["Song"]
        }).get(self.active_table)

        file_name, temp = QFileDialog.getSaveFileName(self,
                                                      "Save Google Play Music Statistics",
                                                      "gmusicstatistics.csv",
                                                      "CSV (*.csv)")

        pd.DataFrame.from_dict(active_dict).to_csv(file_name, index=False)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QApplication.desktop()
        center_point = QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def format_seconds_to_time(self, seconds: int):
        if debug:
            print(seconds)

        if seconds == 0:
            return "00:00:00"

        minutes_formatted, seconds_formatted = divmod(seconds, 60)
        hours_formatted, minutes_formatted = divmod(minutes_formatted, 60)
        time_formatted = "%02d:%02d:%02d" % (hours_formatted, minutes_formatted, seconds_formatted)

        if debug:
            print(time_formatted)

        return time_formatted

    @staticmethod
    def millis_to_seconds(millis: int):
        return int(millis / 1000)


class TableWidgetItem(QTableWidgetItem):

    def __init__(self, text, sort_key: int):
        super().__init__(text)
        self.setFlags(self.flags() & ~Qt.ItemIsEditable)
        self.sort_key = sort_key

    def __lt__(self, other: QTableWidgetItem):
        return self.sort_key < other.sort_key


def main():
    if not api.oauth_login(api.FROM_MAC_ADDRESS):
        api.perform_oauth(open_browser=True)

    # LoginWindow()
    app = QApplication(sys.argv)
    ex = GoogleMusicStatistics(plays["Genre"], "genre")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
