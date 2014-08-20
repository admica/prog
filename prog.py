#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Progress Inspector'''

__author__ = 'admica <crazychickenhead@hotmail.com>'
__doc__ = 'Progress'

import gtk
import os
import pango
from threading import Thread
import subprocess
import logging, logging.handlers
from socket import socketpair, AF_UNIX, SOCK_STREAM
import gobject
import datetime
from time import sleep

class Prog(object):

    # window dims without details
    WIDTH = 1024
    HEIGHT = 112

    # window dims with details
    WIDTH_BIG = 1024
    HEIGHT_BIG = 1024

    # seconds to wait after command completion before closing automatically
    WAIT_QUIT = 3

    # number of event lines to remember
    SCROLLBACK = 1000

    # strings to watch for to increment the progressbar
    MARKERS = [ '100%','99%','98%','97%','96%','95%','94%','93%','92%','91%','90%',
                '99%','98%','97%','96%','95%','94%','93%','92%','91%','90%',
                '89%','88%','87%','86%','85%','84%','83%','82%','81%','80%',
                '79%','78%','77%','76%','75%','74%','73%','72%','71%','70%',
                '69%','68%','67%','66%','65%','64%','63%','62%','61%','60%',
                '59%','58%','57%','56%','55%','54%','53%','52%','51%','50%',
                '49%','48%','47%','46%','45%','44%','43%','42%','41%','40%',
                '39%','38%','37%','36%','35%','34%','33%','32%','31%','30%',
                '29%','28%','27%','26%','25%','24%','23%','22%','21%','20%',
                '19%','18%','17%','16%','15%','14%','13%','12%','11%','10%',
                '9%', '8%', '7%', '6%', '5%', '4%', '3%' ,'2%', '1%', '0%']

    # socket window chunk size
    PACKET_SIZE = 1024

    def __init__(self, opts):
        self.running = True
        self.logo = os.path.join(os.getcwd(), 'logo.png')

        self._setup_colors()

        self.win = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.win.set_title(' '.join(opts))
        self.win.set_position(gtk.WIN_POS_CENTER)
        self.win.set_size_request(self.WIDTH, self.HEIGHT)
        self.win.set_icon(gtk.gdk.pixbuf_new_from_file(self.logo))

        vbox = gtk.VBox(spacing=1)
        self.win.add(vbox)

        pbox = gtk.HBox()
        self.pbar = self._setup_pbar()
        pbox.add(self.pbar)#pack_start(self.pbar, False, False, 55)

        events = self.init_events()

        bbox = gtk.HBox()
        button = gtk.Button('Details')
        button.connect('released', self.button_cb, events)
        bbox.pack_start(button, False, False, 1)

        vbox.pack_start(pbox, False, False, 3)
        vbox.pack_start(bbox, False, False, 1)

        # show gui without events
        self.win.show_all()

        # add events after show all to avoid having to individually show all but events
        vbox.pack_start(events)

        # create sockets
        self.pipe_r, pipe_out_pass = socketpair(AF_UNIX, SOCK_STREAM)
        pipe_w, pipe_in_pass = socketpair(AF_UNIX, SOCK_STREAM)

        # spawn subprocess
        self.p = subprocess.Popen(opts, bufsize=0, stdin=pipe_in_pass, stdout=pipe_out_pass, close_fds=True)

        # watch for subproc output
        gobject.io_add_watch(self.pipe_r, gobject.IO_IN|gobject.IO_HUP, self.receiver)


    def button_cb(self, button, events):
        """button click callback"""
        events.show_all()        
        gobject.idle_add(self._resize)

    def _resize(self):
        self.win.set_size_request(self.WIDTH_BIG, self.HEIGHT_BIG)
        self.win.set_position(gtk.WIN_POS_CENTER)
        return False


    def pbar_update(self, mark, value):
        """progress bar gui update"""
        self.pbar.set_text(mark)
        self.pbar.set_value(value)
        return False


    def receiver(self, fd_ignore, condition):
        try:
            raw = self.pipe_r.recv(1024)
            if len(raw) == 0:
                self.running = False
                if gtk.events_pending:
                    gtk.main_iteration()
                sleep(self.WAIT_QUIT)
                self._quit()

            # progress if marker in raw
            for mark in self.MARKERS:
                if mark in raw:
                    value = int(mark[:-1])
                    gobject.idle_add(self.pbar_update, mark, value)
                    break

            for line in raw.split('\n'):
                self.events('INFO', raw)

        except Exception as e:
            self.running = False
            if gtk.events_pending:
                gtk.main_iteration()
            sleep(self.WAIT_QUIT)
            self._quit()

        # gobject
        return True


    def get_date(self):
        '''return formatted date string'''
        return datetime.datetime.now().strftime("%H:%M:%S")
        

    def events(self, level, raw):
        """log messages go to event frame as fast as they can be processed"""
        msg = "%s %s %s\n" % (self.get_date(), level, str(raw).strip())

        # enforce length
        if self.events_buff.get_line_count() > self.SCROLLBACK:
            start = self.events_buff.get_iter_at_line(0)
            end = self.events_buff.get_iter_at_line(1)
            self.events_buff.delete(start, end)

        self.events_buff.insert_with_tags_by_name(self.events_buff.get_end_iter(), msg, level)

        # scroll to bottom of events log
        self.events_textview.scroll_to_iter(self.events_buff.get_end_iter(), 0)
        # move cursor to the end
        self.events_buff.place_cursor(self.events_buff.get_end_iter())

        # gobject run once
        return False


    def _setup_pbar(self):
        """create progress bar object"""
        pbar = gtk.ProgressBar()
        pbar.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        pbar.set_size_request(self.WIDTH, 70)
        pbar.set_fraction(0)
        pbar.set_text('Initializing...')

        return pbar


    def init_events(self):
        """create events window"""
        frame = gtk.Frame()
        frame.set_border_width(0)
        frame.set_size_request(self.WIDTH-10, self.HEIGHT-10)

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.events_buff = gtk.TextBuffer()
        self.setup_textbuffer_tags(self.events_buff)

        self.events_textview = gtk.TextView(self.events_buff)
        self.events_textview.set_size_request(self.WIDTH-10, self.HEIGHT-10)
        self.events_textview.set_cursor_visible(False)
        self.events_textview.set_editable(False)

        self.events_textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.white))
        self.events_textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse(self.black))

        # combine
        frame.add(scroll)
        scroll.add(self.events_textview)

        return frame


    def _setup_colors(self):
        # color scheme
        self.lt_red    = '#ee3333'
        self.lt_orange = '#f0a053'
        self.lt_blue   = '#4090ee'
        self.lt_green  = '#88ee88'
        self.lt_purple = '#cc99ff'
        self.lt_pink   = '#ffa3e0'
        self.red = '#ee0000'
        self.orange = '#ee7400'
        self.blue = '#1030ee'
        self.green = '#00cc00'
        self.purple = '#9933ff'
        self.pink = '#ff66cc'
        self.dk_red    = '#9b1111'
        self.dk_orange = '#a64b00'
        self.dk_blue   = '#051a9b'
        self.dk_green  = '#005600'
        self.dk_purple = '#4c1a80'
        self.dk_pink   = '#b2478f'

        self.white = '#ffffff'
        self.black = '#000000'
        self.grey = '#777777'
        self.yellow = '#ffee00'
        self.brown = '#773300'

        self.lt_grey = '#bbbbbb'
        self.dk_grey = '#333333'


    def setup_textbuffer_tags(self, buff):
        tag_table = buff.get_tag_table()

        tag = tag_table.lookup('*')
        if not tag:
            tag = gtk.TextTag('*')
        tag.set_property('foreground', self.grey)
        tag.set_property('background', self.black)
        tag.set_property('style', pango.STYLE_NORMAL)
        try:
            tag_table.add(tag)
        except ValueError:
            pass

        tag = tag_table.lookup('INFO')
        if not tag:
            tag = gtk.TextTag('INFO')
        tag.set_property('foreground', self.white)
        tag.set_property('background', self.black)
        tag.set_property('style', pango.STYLE_NORMAL)
        try:
            tag_table.add(tag)
        except ValueError:
            pass

        tag = tag_table.lookup('CRITICAL')
        if not tag:
            tag = gtk.TextTag('CRITICAL')
        tag.set_property('foreground', self.black)
        tag.set_property('background', self.orange)
        tag.set_property('style', pango.STYLE_NORMAL)
        try:
            tag_table.add(tag)
        except ValueError:
            pass

        tag = tag_table.lookup('ERROR')
        if not tag:
            tag = gtk.TextTag('ERROR')
        tag.set_property('foreground', self.white)
        tag.set_property('background', self.red)
        tag.set_property('style', pango.STYLE_NORMAL)
        tag.set_property('weight', pango.WEIGHT_BOLD)
        try:
            tag_table.add(tag)
        except ValueError:
            pass

        tag = tag_table.lookup('WARN')
        if not tag:
            tag = gtk.TextTag('WARN')
        tag.set_property('foreground', self.black)
        tag.set_property('background', self.yellow)
        tag.set_property('style', pango.STYLE_NORMAL)
        tag.set_property('weight', pango.WEIGHT_BOLD)
        try:
            tag_table.add(tag)
        except ValueError:
            pass

        tag = tag_table.lookup('WARNING')
        if not tag:
            tag = gtk.TextTag('WARNING')
        tag.set_property('foreground', self.black)
        tag.set_property('background', self.yellow)
        tag.set_property('style', pango.STYLE_NORMAL)
        tag.set_property('weight', pango.WEIGHT_BOLD)
        try:
            tag_table.add(tag)
        except ValueError:
            pass


    def _quit(self, **args):
        if gtk.events_pending:
            gtk.main_iteration()
        try:
            gtk.main_quit()
        except:
            pass
        sys.exit(0)


if __name__ == '__main__':

    import signal
    import sys

    def signal_handler(signum, stackframe):
        try:
            gtk.main_quit()
        except:
            pass
        sys.exit(1)

    try:
        signal.signal(signal.SIGINT, signal_handler)
    except ValueError:
        signal.signal(signal.CTRL_C_EVENT, signal_handler)

    args = sys.argv[1:]
    if not len(args):
        print "Usage: %s <command arguments>"
        sys.exit(1)

    gtk.gdk.threads_init()
    p = Prog(args)

    gtk.gdk.threads_enter()
    gtk.main()
    gtk.gdk.threads_leave()

    sys.exit(0)
