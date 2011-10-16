#!/usr/bin/env python
'''
File    : webilder_gnome_applet.py
Author  : Nadav Samet
Contact : thesamet@gmail.com
Date    : 2010 Jun 17

Description : Webilder panel applet for GNOME.
'''
from gi.repository import Gtk, GdkPixbuf
import pkg_resources

from webilder.base_applet import BaseApplet
from webilder.config import config
from webilder import AboutDialog
from webilder import config_dialog
from webilder import DownloadDialog
from webilder import __version__
from webilder import WebilderDesktop

import sys
import gnomeapplet
import gnome
from gi.repository import GObject


# Set this to False if you don't want the software to check
# for updates.
#
# No information, except of the version request itself is sent
# to Webilder's server.

class WebilderApplet(BaseApplet):
    """Implementation for Webilder GNOME panel applet."""
    def __init__(self, applet, _iid):
        BaseApplet.__init__(self)
        gnome.init('WebilderApplet', __version__)
        self.applet = applet
        self.tooltips = Gtk.Tooltips()
        self.tooltips.enable()
        self.evtbox = Gtk.EventBox()
        self.icon = GdkPixbuf.Pixbuf.new_from_file(
            pkg_resources.resource_filename(__name__, 'ui/camera48.png'))
        self.icon_green = GdkPixbuf.Pixbuf.new_from_file(
            pkg_resources.resource_filename(__name__, 'ui/camera48_g.png'))

        self.applet_icon = Gtk.Image()
        self.scaled_icon = self.icon.scale_simple(16, 16,
                GdkPixbuf.InterpType.BILINEAR)
        self.scaled_icon_green = self.icon_green.scale_simple(16, 16,
                GdkPixbuf.InterpType.BILINEAR)

        self.applet_icon.set_from_pixbuf(self.scaled_icon)
        self.evtbox.add(self.applet_icon)
        self.applet.add(self.evtbox)
        self.propxml = _("""
    <popup name="button3">
        <menuitem name="Item 1" verb="Browse" label="_Browse Collection" pixtype="stock"
pixname="gtk-directory"/>
        <menuitem name="Item 2" verb="NextPhoto" label="_Next Photo" pixtype="stock"
pixname="gtk-go-forward"/>
        <menuitem name="Item 3" verb="Leech" label="_Download Photos" pixtype="filename"
pixname="%s"/>
        <menuitem name="Item 6" verb="DeleteCurrent" label="_Delete Current" pixtype="stock" pixname="gtk-delete"/>
        <menuitem name="Item 4" verb="Pref" label="_Preferences" pixtype="stock"
pixname="gtk-preferences"/>
        <menuitem name="Item 5" verb="About" label="_About" pixtype="stock" pixname="gnome-stock-about"/>
        </popup>
    """) % pkg_resources.resource_filename(__name__, 'ui/camera16.png')

        self.applet.connect("change-size", self.on_resize_panel)
        self.applet.connect("button-press-event", self.on_button_press)

        self.verbs = [
            ( "Pref", self.preferences ),
            ( "About", self.about),
            ( "Browse", self.browse),
            ( "NextPhoto", self.next_photo),
            ( "Leech", self.leech),
            ( "DeleteCurrent", self.delete_current)]
        self.applet.setup_menu(self.propxml, self.verbs, None)
        self.applet.show_all()
        GObject.timeout_add(60*1000, self.timer_event)
        self.photo_browser = None
        self.download_dlg = None

    def set_tooltip(self, text):
        self.tooltips.enable()
        self.tooltips.set_tip(self.applet, text)

    def preferences(self, _object, _menu):
        """Opens the preferences dialog."""
        config_dialog.ConfigDialog().run_dialog(config)

    def about(self, _object, _menu):
        """Opens the about dialog."""
        AboutDialog.show_about_dialog(_('Webilder Applet'))

    def leech(self, _object, _menu):
        """Starts downloading photos."""
        def remove_reference(*_args):
            """Removes reference to the download dialog so we will not it is
            not running."""
            self.download_dlg = None

        if self.download_dlg:
            return
        self.download_dlg = DownloadDialog.DownloadProgressDialog(config)
        self.download_dlg.top_widget.connect('destroy', remove_reference)
        self.download_dlg.show()
        self.applet_icon.set_from_pixbuf(self.scaled_icon)
        self.tooltips.disable()

    def on_resize_panel(self, _widget, size):
        """Called when the panel is resized so we can scale our icon."""
        self.scaled_icon = self.icon.scale_simple(size - 4, size - 4,
            GdkPixbuf.InterpType.BILINEAR)
        self.scaled_icon_green = self.icon_green.scale_simple(size - 4,
                                                              size - 4,
            GdkPixbuf.InterpType.BILINEAR)
        self.applet_icon.set_from_pixbuf(self.scaled_icon)

    def on_button_press(self, _widget, event):
        """Called when the user clicks on the applet icon."""
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            return False
        elif event.type == Gdk.EventType.BUTTON_PRESS and event.button == 1:
            if not self.photo_browser:
                self.browse(None, None)
            else:
                toggle_window_visibility(self.photo_browser.top_widget)

    def browse(self, _object, _menu):
        """Opens the photo browser."""
        if not self.photo_browser:
            self.photo_browser = WebilderDesktop.WebilderDesktopWindow()
            self.photo_browser.top_widget.connect("destroy",
                                                  self.photo_browser_destroy)
        else:
            self.photo_browser.top_widget.show_all()

    def photo_browser_destroy(self, _event):
        """Called when the photo browser is closed."""
        self.photo_browser.destroy()
        self.photo_browser = None

def webilder_applet_factory(applet, iid):
    """Instantiates a webilder applet."""
    WebilderApplet(applet, iid)
    return True

def toggle_window_visibility(window):
    """Hides and show the photo browser."""
    visible = window.get_property('visible')
    if visible:
        window.hide()
    else:
        window.show_all()

def main():
    """Entrypoint for the panel applet."""
    Gdk.threads_init()

    if len(sys.argv) == 2 and sys.argv[1] == "run-in-window":
        print "here"
        main_window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        main_window.set_title(_("Webilder Applet Window"))
        main_window.connect("destroy", Gtk.main_quit)
        app = gnomeapplet.Applet()
        WebilderApplet(app, None)
        app.reparent(main_window)
        main_window.show_all()
        Gtk.main()
        sys.exit()
    else:
        gnomeapplet.bonobo_factory("OAFIID:GNOME_WebilderApplet_Factory",
                                 gnomeapplet.Applet.__gtype__,
                                 "webilder-hello", "0", webilder_applet_factory)
