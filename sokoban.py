#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import sys
import time
import curses
import glob

from devices import Devices


MAZE_HERO       = '@'
MAZE_SPACE      = ' '
MAZE_WALL       = '#'
MAZE_BOX        = 'B'
MAZE_SHELF      = '*'
MAZE_SHELF_BOX  = 'X'       # the shelf with box


class Move:
    STOP = 0
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4


class Maze:
    COLORING = {
        MAZE_HERO:      ('☻', Devices.COLOR_YELLOW,  Devices.COLOR_BLACK),
        MAZE_SPACE:     (' ', Devices.COLOR_WHITE,   Devices.COLOR_BLACK),
        MAZE_WALL:      ('░', Devices.COLOR_MAGENTA, Devices.COLOR_MAGENTA),
        MAZE_BOX:       ('⣿', Devices.COLOR_BLUE,    Devices.COLOR_BLACK), # ✪ 🌳 █
        MAZE_SHELF:     ('♦', Devices.COLOR_GREEN,   Devices.COLOR_BLACK),
        MAZE_SHELF_BOX: ('♦', Devices.COLOR_BLUE,    Devices.COLOR_GREEN), # ✪ 🌳 █
    }

    def __init__(self, fpath, devices):
        self.devices = devices
        self.maze = []
        self.width = 0
        self.height = 0
        self.max_x = self.devices.get_screen_width()
        self.max_y = self.devices.get_screen_height()
        self.hero_x, self.hero_y = None, None
        self.shelves, self.boxes, self.shelfbox = 0, 0, 0
        self.start_x, self.start_y = 0, 0
        self.load(fpath)

    def load(self, fpath):
        # load maze into a list as strings
        self.width, self.height = 0, 0
        str_maze = []
        for line in open(fpath, 'r', encoding='utf-8'):
            line = line.rstrip()
            if not line:
                continue
            self.height += 1
            self.width = max(self.width, len(line))
            if self.height > self.max_y or self.width > self.max_x:
                raise Exception("Maze file '%s': doesn't fit into screen sizes %dx%d, line no=%d" % \
                                (fpath, self.max_x, self.max_y, self.height))
            str_maze.append(line)
        # init empty maze
        self.maze = [None] * self.height
        # convert maze from string format into 2-dimensional array
        for y in range(len(str_maze)):
            row = str_maze[y]
            self.maze[y] = [MAZE_SPACE] * self.width
            for x in range(len(row)):
                c = row[x]
                if c == MAZE_HERO:
                    self.hero_x = x
                    self.hero_y = y
                    c = MAZE_SPACE
                elif c == MAZE_SHELF:
                    self.shelves += 1
                elif c == MAZE_BOX:
                    self.boxes += 1
                elif c == MAZE_SHELF_BOX:
                    self.shelfbox += 1
                    self.shelves += 1
                    self.boxes += 1

                self.maze[y][x] = c
        # check if we found a hero and number of shelves is appropriate to boxes
        if self.hero_x is None:
            raise Exception("Maze file '%s': No hero found" % fpath)
        if self.shelves == 0:
            raise Exception("Maze file '%s': There is no any shelf in the map" % fpath)
        if self.shelves != self.boxes:
            raise Exception("Maze file '%s': Number of shelves '*' is not equal to number of boxes '#'" % fpath)
        self._calc_start_xy()

    def _calc_start_xy(self):
        # calc screen's starting position
        self.start_x = (self.max_x - self.width) // 2
        self.start_y = (self.max_y - self.height) // 2

    def print(self):
        x = 0
        for i in range(self.width):
            y = 0
            for j in range(self.height):
                self.print_item(y, x, self.maze[j][i])
                y += 1
            x += 1

        self.print_item(self.hero_y, self.hero_x, MAZE_HERO)
        self.devices.refresh_screen()

    def print_item(self, y, x, maze_item):
        default = (maze_item, Devices.COLOR_WHITE, Devices.COLOR_BLACK)
        c, fg, bg = Maze.COLORING.get(maze_item, default)
        self.devices.print(self.start_y+y, self.start_x+x, c, fg, bg)

    def move_hero(self, move):
        dx, dy = 0, 0
        if move == Move.LEFT:
            dx = -1
        elif move == Move.RIGHT:
            dx = 1
        elif move == Move.UP:
            dy = -1
        elif move == Move.DOWN:
            dy = 1

        nx, ny = self.hero_x+dx, self.hero_y+dy
        if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height:
            return
        ahead = self.maze[ny][nx]

        nx2, ny2 = nx+dx, ny+dy
        ahead2 = None
        if nx2 >= 0 and nx2 < self.width and ny2 >= 0 and ny2 < self.height:
            ahead2 = self.maze[ny2][nx2]

        if ahead == MAZE_WALL:
            return
        elif ahead == MAZE_SPACE or ahead == MAZE_SHELF:
            pass
        elif ahead == MAZE_BOX:
            if ahead2 == MAZE_SPACE:
                self.maze[ny][nx] = MAZE_SPACE
                self.maze[ny2][nx2] = MAZE_BOX
            elif ahead2 == MAZE_SHELF:
                self.maze[ny][nx] = MAZE_SPACE
                self.maze[ny2][nx2] = MAZE_SHELF_BOX
                self.shelfbox += 1
            else:
                return
        elif ahead == MAZE_SHELF_BOX and (ahead2 == MAZE_SPACE or ahead2 == MAZE_SHELF):
            self.maze[ny][nx] = MAZE_SHELF
            if ahead2 == MAZE_SPACE:
                self.maze[ny2][nx2] = MAZE_BOX
                self.shelfbox -= 1
            elif ahead2 == MAZE_SHELF:
                self.maze[ny2][nx2] = MAZE_SHELF_BOX
        else:
            return

        self.hero_x, self.hero_y = nx, ny
        self.print()

    def set_screen_size(self, max_y, max_x):
        self.max_y = max_y
        self.max_x = max_x
        self._calc_start_xy()


class GameHandler:
    def __init__(self, devices, mazes_dir, start_level):
        self.devices = devices
        self.mazes_fnames = sorted(glob.glob(mazes_dir + '/*'))
        self.current_maze = start_level - 1
        if len(self.mazes_fnames) == 0:
            raise Exception('There is no any maze in dir "%s"' % mazes_dir)
        self.init_current_maze()
        self.kb2move = {
            curses.KEY_LEFT:  Move.LEFT,
            curses.KEY_RIGHT: Move.RIGHT,
            curses.KEY_UP:    Move.UP,
            curses.KEY_DOWN:  Move.DOWN,
        }

    def init_current_maze(self):
        self.maze = Maze(self.mazes_fnames[self.current_maze], self.devices)
        self.print_game_situation()

    def print_game_situation(self):
        self.devices.clear_screen()
        self.maze.print()
        self.print_score()

    def print_score(self):
        self.devices.print(0, 2, 'MAP %d  ::  BOXES %d  ::  SHELVES %d  ::  READY %d  ' % \
                           (self.current_maze+1, self.maze.boxes, self.maze.shelves, self.maze.shelfbox))
        self.devices.print(self.devices.get_screen_height()-1, 2, '<Q> EXIT  ::  <R> RESTART THE LEVEL')

    def check_game_situation(self):
        if self.maze.shelfbox == self.maze.shelves:
            time.sleep(0.2)
            self.print_window("YOU'VE SOLVED THE MAP!")
            self.current_maze += 1
            if self.current_maze < len(self.mazes_fnames):
                self.print_window("> GOING TO MAP %d! <" % (self.current_maze+1))
                self.init_current_maze()
            else:
                self.print_window("-- YOU'VE PASSED ALL THE LEVELS! WELL DONE!!! --")
                return False

    def print_window(self, msg):
        fg, bg = Devices.COLOR_BLUE, Devices.COLOR_WHITE
        win_width = len(msg) + 4
        win_height = 5
        x = (self.devices.get_screen_width() - win_width) // 2
        y = (self.devices.get_screen_height() - win_height) // 2
        for i in range(win_height):
            self.devices.print(i+y, x, ' '*win_width, fg, bg)
        self.devices.print(y+win_height//2, x+2, msg, fg, bg)
        return self.devices.get_key(blocking=True)

    def ask_to_restart(self):
        return self.print_window('RESTART THE LEVEL? (Y/N)') == 121     # 'y'

    def ask_to_exit(self):
        return self.print_window('EXIT THE GAME? (Y/N)') == 121             # 'y'

    def on_keyboard(self, dev, kb):
        move = self.kb2move.get(kb, None)
        if move is not None:
            self.maze.move_hero(move)
            self.print_score()
            if self.check_game_situation() == False:
                return False    # exit from loop
        elif kb == 114:         # 'r'
            if self.ask_to_restart():
                self.init_current_maze()
            else:
                self.print_game_situation()
        elif kb == 113:         # 'q'
            if self.ask_to_exit():
                return False    # exit from loop
            else:
                self.print_game_situation()

    def on_screen_resize(self, dev, h, w):
        self.maze.set_screen_size(h, w)
        self.print_game_situation()


def main():
    start_level = 1
    if len(sys.argv) > 1:
        start_level = int(sys.argv[1])

    try:
        dev = Devices()
        game_handler = GameHandler(dev, './mazes', start_level)
        dev.main_loop(on_keyboard=game_handler.on_keyboard, on_screen_resize=game_handler.on_screen_resize)

    except:
        dev.__del__()
        raise

    return 0


if __name__ == '__main__':
    sys.exit( main() )
