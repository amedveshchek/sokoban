# coding: utf-8

import curses
import time


class Devices:
    ''' Convenient curses-wrapper. '''
    COLOR_BLACK         = 0
    COLOR_RED           = 1
    COLOR_GREEN         = 2
    COLOR_ORANGE        = 3
    COLOR_BLUE          = 4
    COLOR_MAGENTA       = 5
    COLOR_CYAN          = 6
    COLOR_GREY          = 7
    COLOR_DARK_GREY     = 8
    COLOR_LIGHT_RED     = 9
    COLOR_LIGHT_GREEN   = 10
    COLOR_YELLOW        = 11
    COLOR_LIGHT_BLUE    = 12
    COLOR_LIGHT_MAGENTA = 13
    COLOR_LIGHT_CYAN    = 14
    COLOR_WHITE         = 15

    MOUSE_BUTTON1_PRESSED = curses.BUTTON1_PRESSED
    MOUSE_BUTTON2_PRESSED = curses.BUTTON2_PRESSED
    MOUSE_BUTTON3_PRESSED = curses.BUTTON3_PRESSED
    MOUSE_BUTTON4_PRESSED = curses.BUTTON4_PRESSED
    MOUSE_BUTTON1_RELEASED = curses.BUTTON1_RELEASED
    MOUSE_BUTTON2_RELEASED = curses.BUTTON2_RELEASED
    MOUSE_BUTTON3_RELEASED = curses.BUTTON3_RELEASED
    MOUSE_BUTTON4_RELEASED = curses.BUTTON4_RELEASED
    MOUSE_BUTTON1_CLICKED = curses.BUTTON1_CLICKED
    MOUSE_BUTTON2_CLICKED = curses.BUTTON2_CLICKED
    MOUSE_BUTTON3_CLICKED = curses.BUTTON3_CLICKED
    MOUSE_BUTTON4_CLICKED = curses.BUTTON4_CLICKED
    MOUSE_BUTTON1_DOUBLE_CLICKED = curses.BUTTON1_DOUBLE_CLICKED
    MOUSE_BUTTON2_DOUBLE_CLICKED = curses.BUTTON2_DOUBLE_CLICKED
    MOUSE_BUTTON3_DOUBLE_CLICKED = curses.BUTTON3_DOUBLE_CLICKED
    MOUSE_BUTTON4_DOUBLE_CLICKED = curses.BUTTON4_DOUBLE_CLICKED
    MOUSE_BUTTON1_TRIPLE_CLICKED = curses.BUTTON1_TRIPLE_CLICKED
    MOUSE_BUTTON2_TRIPLE_CLICKED = curses.BUTTON2_TRIPLE_CLICKED
    MOUSE_BUTTON3_TRIPLE_CLICKED = curses.BUTTON3_TRIPLE_CLICKED
    MOUSE_BUTTON4_TRIPLE_CLICKED = curses.BUTTON4_TRIPLE_CLICKED
    MOUSE_BUTTON_SHIFT = curses.BUTTON_SHIFT
    MOUSE_BUTTON_CTRL = curses.BUTTON_CTRL
    MOUSE_BUTTON_ALT = curses.BUTTON_ALT

    def __init__(self, start_immediately=True):
        if start_immediately:
            self.start()

    def __del__(self):
        self.stop()

    def start(self):
        '''
        _orig_ESCDELAY = ''
        try:
            _orig_ESCDELAY = os.environ['ESCDELAY']
        except KeyError:
            pass
        os.environ['ESCDELAY'] = str(0)  # Stop escape key from pausing game
        '''
        self.screen = curses.initscr()
        self.has_colors = curses.has_colors()
        if self.has_colors:
            curses.start_color()
        curses.noecho()             # Don't display kb-input
        curses.cbreak()             # Send characters immediately to getch() instead of storing them in buffer.
        curses.nonl()               # Allow to detect Enter-key press
        self.screen.keypad(True)    # Allow curses.KEY_LEFT/KEY_RIGHT/... keys
        self.hide_cursor()          # Hide cursor
        self.set_keyboard_delay(0)  # By default don't block keyboard
        self.screen_height, self.screen_width = self.screen.getmaxyx()
        # init color attrs
        default_attr = curses.color_pair(0)
        default_pair = curses.pair_number(default_attr)
        self.fore_color, self.back_color = curses.pair_content(default_pair)

        self.color_attrs = dict()   # dict{ (fg_color, bg_color) -> curses attr }
        self.color_attrs[(self.fore_color, self.back_color)] = default_attr
        self.next_color_pair = 1

    def stop(self):
        curses.nocbreak()
        self.screen.keypad(False)
        curses.echo()
        curses.endwin()

    def hide_cursor(self):
        curses.curs_set(0)

    def show_cursor(self):
        curses.curs_set(1)

    def put_cursor(self, y, x):
        self.screen.move(y, x)

    def get_screen_width(self):
        return self.screen_width

    def get_screen_height(self):
        return self.screen_height

    def beep(self):
        curses.beep()

    def set_fore_color(self, color):
        ''' Set default foreground color '''
        self.fore_color = color

    def set_back_color(self, color):
        ''' Set default background color '''
        self.back_color = color

    def _get_colors_attr(self, fore_color, back_color):
        attr = self.color_attrs.get((fore_color, back_color), None)
        if attr is None:
            curses.init_pair(self.next_color_pair, fore_color, back_color)
            attr = curses.color_pair(self.next_color_pair)
            self.color_attrs[(fore_color, back_color)] = attr
            self.next_color_pair += 1
            #curses.COLOR_PAIRS-1
        return attr

    def print(self, y, x, text, fore_color=None, back_color=None):
        if fore_color is None:
            fore_color = self.fore_color
        if back_color is None:
            back_color = self.back_color
        attr = self._get_colors_attr(fore_color, back_color)
        try:
            self.screen.addstr(y, x, text, attr)
        except:
            # ignore the case when the symbol at bottom-right position
            pass

    '''
    def change_color(self, y, x, length, fore_color, back_color)
        attr = self._get_colors_attr(fore_color, back_color)
        self.screen.chgat(y, x, length, attr)
    '''

    def refresh_screen(self):
        self.screen.refresh()

    def clear_screen(self):
        self.screen.clear()

    def set_keyboard_delay(self, timeout=-1):
        ''' Set key-read mode:
        Blocking mode: timeout < 0, get_key() will block the program.
        Non-blocking : timeout == 0, get_key() will be non-blocking.
        Timeout mode : timeout > 0, get_key() will wait for timeout milliseconds until exits with -1 code.
        '''
        self.screen.timeout(timeout)

    def get_key(self, blocking=None):
        '''
        In blocking mode (set_keyboard_delay(-1)) it will return int code of inputed key.
        In non-blocking mode (set_keyboard_delay(>=0)) it will return -1 if not key was stroked.
        Params:
            blocking    None|True|False, if True/False then enable/disable default blocking behaviour.
        '''
        if blocking is not None:
            self.set_keyboard_delay(int(not blocking) - 1)
        char = self.screen.getch()
        # Flush all input buffers. This throws away any typeahead that has been typed by 
        # the user and has not yet been processed by the program.
        curses.flushinp()
        return char


    def main_loop(self,
                  refresh_rate_sec=0.05,
                  on_keyboard=None,
                  on_mouse=None,
                  on_screen_resize=None,
                  on_idle=None):
        ''' Main loop to get events.
        Params:
            refresh_rate_sec                float, time to wait before to try to get the next event.
            on_keyboard(dev, keyboard_code) callable, handler of keyboard event.
            on_mouse(dev, y, x, bstate)     callable, (y,x) - mouse coo, bstate - int with bits of MOUSE_BUTTON_* values
            on_screen_resize(dev, h, w)     callable, (h,w) - new width and height of screen respectively
            on_idle(dev)                    callable, if no any action happened on this loop-iteration
        If any callback returns False, then loop stops.
        '''
        while True:
            self.set_keyboard_delay(0)      # set non-blocking mode for keyboard
            kb = self.get_key()

            if kb == curses.KEY_RESIZE:
                self.screen_height, self.screen_width = self.screen.getmaxyx()
                if on_screen_resize and on_screen_resize(self, self.screen_height, self.screen_width) == False:
                    break
            elif kb == curses.KEY_MOUSE:
                (id, x, y, z, bstate) = curses.getmouse()
                if on_mouse and on_mouse(self, y, x, bstate) == False:
                    break
            elif kb and kb >= 0:
                if on_keyboard and on_keyboard(self, kb) == False:
                    break
            else:
                if on_idle and on_idle(self) == False:
                    break

            time.sleep(refresh_rate_sec)


    def _test_colors(self):
        all_colors = [
            Devices.COLOR_BLACK,
            Devices.COLOR_RED,
            Devices.COLOR_GREEN,
            Devices.COLOR_ORANGE,
            Devices.COLOR_BLUE,
            Devices.COLOR_MAGENTA,
            Devices.COLOR_CYAN,
            Devices.COLOR_GREY,
            Devices.COLOR_DARK_GREY,
            Devices.COLOR_LIGHT_RED,
            Devices.COLOR_LIGHT_GREEN,
            Devices.COLOR_YELLOW,
            Devices.COLOR_LIGHT_BLUE,
            Devices.COLOR_LIGHT_MAGENTA,
            Devices.COLOR_LIGHT_CYAN,
            Devices.COLOR_WHITE,
        ]
        for x in range(len(all_colors)):
            for y in range(len(all_colors)):
                self.print(y, x, '$', fore_color=all_colors[x], back_color=all_colors[y])
                c = chr(y*16 + x)
                self.print(y, x+20, c, fore_color=Devices.COLOR_BLACK, back_color=Devices.COLOR_WHITE)
        self.print(len(all_colors), 0, 'known colors=%d, used color pairs=%d, maximum COLOR_PAIRS=%d' % \
                   (len(all_colors), len(self.color_attrs), curses.COLOR_PAIRS))
        self.print(len(all_colors)+2, 0, 'Press any key to exit...')
        self.refresh_screen()


if __name__ == '__main__':
    import sys

    devices = Devices()
    devices._test_colors()
    # devices.set_keyboard_delay(-1)        # set keyboard-blocking mode
    # devices.get_key()

    def on_keyboard(dev, kb):
        dev.beep()
        return False        # stop loop on any keyboard activity

    def on_mouse(dev, y, x, buttons_state):
        dev.print(11, 0, 'Mouse activity: yx=(%d, %d), buttons=%d    ' % (y, x, buttons_state))

    def on_screen_resize(dev, h, w):
        dev.print(20, 0, 'Screen size: height=%d x width=%d    ' % (h, w))

    devices.main_loop(on_keyboard=on_keyboard, on_mouse=on_mouse, on_screen_resize=on_screen_resize)
