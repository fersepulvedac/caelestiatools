#!/usr/bin/env python

import gi
import glob
import json
import os
import re
import subprocess

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

HYPR_CONFIG = os.path.expanduser("~/.config/hypr/hyprland.conf")
CONFIG = os.path.expanduser("~/.config/hypr/hyprland/keybinds.conf")
CAELESTIA_CONFIG = os.path.expanduser("~/.config/caelestia/shell.json")
SCHEME_CONFIG = os.path.expanduser("~/.config/hypr/scheme/current.conf")
SCHEME_DIR = os.path.dirname(SCHEME_CONFIG)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_GIF_DIR = os.path.join(APP_DIR, "sessiongif")
MEDIA_GIF_DIR = os.path.join(APP_DIR, "mediagif")
SESSION_GIF_EXTENSIONS = (".gif",)
PREVIEW_LOGICAL_W = 56
PREVIEW_LOGICAL_H = 41
PREVIEW_DECODE_SCALE = 3
# Launcher note: this app is registered with
# ~/.local/share/applications/com.hypr.bindviewer.desktop.
# Keep that desktop entry updated instead of creating duplicate launchers.
BIND_TYPES = [
    "bind",
    "binde",
    "bindi",
    "bindin",
    "bindl",
    "bindle",
    "bindm",
    "bindr",
]

THEME_FALLBACKS = {
    "background": "#131317",
    "surface": "#131317",
    "surfaceContainer": "#201f23",
    "surfaceContainerHigh": "#2a292e",
    "surfaceContainerHighest": "#353438",
    "onSurface": "#e5e1e7",
    "onSurfaceVariant": "#c8c5d1",
    "outline": "#918f9a",
    "outlineVariant": "#47464f",
    "primary": "#c2c1ff",
    "onPrimary": "#2a2a60",
    "primaryContainer": "#7171ac",
    "tertiary": "#f5b2e0",
}

KEY_LABELS = {
    "mouse:272": "Clic izquierdo",
    "mouse:273": "Clic derecho",
    "mouse:274": "Clic central",
    "mouse:275": "Boton lateral atras",
    "mouse:276": "Boton lateral adelante",
    "mouse:277": "Boton extra",
    "mouse_up": "Rueda arriba",
    "mouse_down": "Rueda abajo",
    "catchall": "Cualquier tecla",
}

CSS_COLORS = """
@define-color background {background};
@define-color surface {surface};
@define-color surface_container {surfaceContainer};
@define-color surface_container_high {surfaceContainerHigh};
@define-color surface_container_highest {surfaceContainerHighest};
@define-color on_surface {onSurface};
@define-color on_surface_variant {onSurfaceVariant};
@define-color outline {outline};
@define-color outline_variant {outlineVariant};
@define-color primary {primary};
@define-color on_primary {onPrimary};
@define-color primary_container {primaryContainer};
@define-color tertiary {tertiary};
"""

CSS = """
window {
    background: @background;
    color: @on_surface;
    font-family: Inter, "SF Pro Display", "Cantarell", sans-serif;
}

.app-shell {
    padding: 24px;
}

.topbar {
    background: linear-gradient(135deg, alpha(@surface_container_high, 0.92), alpha(@surface_container, 0.78));
    border: 1px solid alpha(@outline_variant, 0.70);
    border-radius: 24px;
    box-shadow: 0 24px 60px alpha(black, 0.30);
    margin-bottom: 18px;
    padding: 18px;
}

.app-mark {
    background: linear-gradient(135deg, @primary, @tertiary);
    border-radius: 16px;
    color: @on_primary;
    font-size: 15px;
    font-weight: 900;
    min-height: 48px;
    min-width: 48px;
}

.title {
    color: @on_surface;
    font-size: 28px;
    font-weight: 800;
}

.subtitle {
    color: @on_surface_variant;
    font-size: 13px;
}

.counter {
    background: alpha(@primary, 0.16);
    border: 1px solid alpha(@primary, 0.42);
    border-radius: 999px;
    color: @primary;
    font-size: 12px;
    font-weight: 700;
    padding: 8px 13px;
}

.session-image-button {
    background: alpha(@surface_container_highest, 0.74);
    border: 1px solid alpha(@outline_variant, 0.72);
    border-radius: 16px;
    color: @on_surface;
    font-size: 12px;
    font-weight: 800;
    min-height: 38px;
    padding: 0 13px;
}

.session-image-button:hover {
    background: alpha(@primary, 0.16);
    border-color: alpha(@primary, 0.52);
    color: @primary;
}

.session-gallery {
    background: alpha(@surface_container, 0.72);
    border: 1px solid alpha(@outline_variant, 0.58);
    border-radius: 22px;
    margin-bottom: 18px;
    padding: 14px;
}

.session-gallery:last-child {
    margin-bottom: 0;
}

.session-gallery-title {
    color: @on_surface;
    font-size: 16px;
    font-weight: 800;
}

.session-gallery-copy {
    color: @on_surface_variant;
    font-size: 12px;
}

.tab-bar {
    background: alpha(@surface_container, 0.78);
    border: 1px solid alpha(@outline_variant, 0.55);
    border-radius: 999px;
    margin-bottom: 18px;
    padding: 5px;
}

.tab-button {
    background: transparent;
    border: none;
    border-radius: 999px;
    color: @on_surface_variant;
    font-size: 13px;
    font-weight: 700;
    min-height: 36px;
    padding: 0 18px;
    transition: background 160ms ease, color 160ms ease;
}

.tab-button:hover {
    background: alpha(@primary, 0.10);
    color: @on_surface;
}

.tab-button:checked {
    background: linear-gradient(135deg, @primary, @tertiary);
    color: @on_primary;
    box-shadow: 0 6px 18px alpha(@primary, 0.32);
}

.tab-button:checked:hover {
    background: linear-gradient(135deg, @primary, @tertiary);
    color: @on_primary;
}

.tab-button image {
    -gtk-icon-size: 16px;
}

.tab-stack {
    background: transparent;
}

.tab-page {
    background: transparent;
}

.session-gif-grid {
    background: transparent;
}

.session-gif-card {
    background: alpha(@surface_container_high, 0.68);
    border: 1px solid alpha(@outline_variant, 0.62);
    border-radius: 18px;
    color: @on_surface;
    min-width: 74px;
    padding: 8px;
}

.session-gif-card:hover {
    background: alpha(@primary, 0.14);
    border-color: alpha(@primary, 0.52);
}

.session-gif-card.selected {
    background: alpha(@primary, 0.22);
    border-color: alpha(@primary, 0.86);
}

.session-gif-card.selected-media {
    background: alpha(@tertiary, 0.18);
    border-color: alpha(@tertiary, 0.72);
}

.session-gif-preview {
    background: alpha(black, 0.16);
    border-radius: 14px;
    margin-bottom: 7px;
}

.session-gif-name {
    color: @on_surface;
    font-size: 12px;
    font-weight: 700;
}

.search-box {
    background: alpha(@surface_container_highest, 0.72);
    border: 1px solid alpha(@outline_variant, 0.72);
    border-radius: 18px;
    color: @on_surface;
    min-height: 46px;
    padding: 0 14px;
}

.search-box:focus {
    background: alpha(@surface_container_highest, 0.90);
    border-color: alpha(@primary, 0.76);
}

.bind-list {
    background: transparent;
}

.bind-list row {
    background: transparent;
    margin: 0 0 12px 0;
}

.bind-list row:hover .bind-card {
    background: alpha(@surface_container_highest, 0.74);
    border-color: alpha(@primary, 0.42);
}

.bind-card {
    background: alpha(@surface_container, 0.80);
    border: 1px solid alpha(@outline_variant, 0.58);
    border-radius: 20px;
    padding: 14px;
}

.card-accent {
    background: linear-gradient(180deg, @primary, @tertiary);
    border-radius: 999px;
    min-width: 4px;
}

.key-chip {
    background: alpha(@primary, 0.14);
    border: 1px solid alpha(@primary, 0.34);
    border-radius: 12px;
    color: @primary;
    font-size: 12px;
    font-weight: 800;
    min-width: 34px;
    padding: 7px 10px;
}

.plus {
    color: @outline;
    font-weight: 800;
}

.action {
    color: @on_surface;
    font-size: 15px;
    font-weight: 700;
}

.dispatcher {
    color: @on_surface_variant;
    font-size: 12px;
}

.run-button {
    background: alpha(@primary, 0.16);
    border: 1px solid alpha(@primary, 0.40);
    border-radius: 999px;
    color: @primary;
    min-height: 38px;
    min-width: 38px;
    padding: 0;
}

.run-button:hover {
    background: alpha(@primary, 0.26);
    border-color: alpha(@primary, 0.72);
}

.run-button image {
    color: @primary;
}

.empty-title {
    color: @on_surface;
    font-size: 18px;
    font-weight: 800;
}

.empty-copy {
    color: @on_surface_variant;
}

scrollbar {
    background: transparent;
}

scrollbar slider {
    background: alpha(@outline, 0.38);
    border-radius: 999px;
    min-width: 6px;
}

scrollbar slider:hover {
    background: alpha(@primary, 0.46);
}
"""


class BindViewer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.hypr.bindviewer")
        self.binds = []
        self.query = ""
        self.count_label = None
        self.listbox = None
        self.css_provider = None
        self.scheme_file_monitor = None
        self.scheme_dir_monitor = None
        self.theme_reload_source = None
        self.session_image_button = None
        self.media_image_button = None
        self.session_gif_buttons = {}
        self.media_gif_buttons = {}
        self.tab_stack = None
        self.tab_buttons = {}

    def do_activate(self):
        self.install_css()
        self.watch_scheme()
        self.binds = self.load_binds()
        os.makedirs(MEDIA_GIF_DIR, exist_ok=True)

        window = Gtk.ApplicationWindow(application=self)
        window.set_title("Atajos de Caelestia")
        window.set_default_size(860, 620)

        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        shell.add_css_class("app-shell")

        shell.append(self.create_header())
        shell.append(self.create_tab_bar())
        shell.append(self.create_tab_stack())

        window.set_child(shell)
        window.present()

    def install_css(self):
        self.css_provider = Gtk.CssProvider()
        self.reload_css()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def reload_css(self):
        if self.css_provider is None:
            return

        css = CSS_COLORS.format(**self.load_theme()) + CSS
        self.css_provider.load_from_data(css.encode())

    def watch_scheme(self):
        file = Gio.File.new_for_path(SCHEME_CONFIG)
        directory = Gio.File.new_for_path(SCHEME_DIR)

        try:
            self.scheme_file_monitor = file.monitor_file(
                Gio.FileMonitorFlags.NONE,
                None,
            )
            self.scheme_file_monitor.connect("changed", self.on_scheme_changed)
        except GLib.Error:
            self.scheme_file_monitor = None

        try:
            self.scheme_dir_monitor = directory.monitor_directory(
                Gio.FileMonitorFlags.NONE,
                None,
            )
            self.scheme_dir_monitor.connect("changed", self.on_scheme_changed)
        except GLib.Error:
            self.scheme_dir_monitor = None

    def on_scheme_changed(self, _monitor, file, _other_file, _event_type):
        if file is not None and file.get_path() not in {SCHEME_CONFIG, SCHEME_DIR}:
            return

        if self.theme_reload_source is not None:
            GLib.source_remove(self.theme_reload_source)

        self.theme_reload_source = GLib.timeout_add(
            150,
            self.reload_theme_from_monitor,
        )

    def reload_theme_from_monitor(self):
        self.theme_reload_source = None
        self.reload_css()
        return GLib.SOURCE_REMOVE

    def create_header(self):
        topbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        topbar.add_css_class("topbar")

        mark = Gtk.Label(label="HY")
        mark.add_css_class("app-mark")
        mark.set_valign(Gtk.Align.CENTER)

        heading = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        heading.set_hexpand(True)

        title = Gtk.Label(label="Atajos de Caelestia")
        title.add_css_class("title")
        title.set_xalign(0)

        subtitle = Gtk.Label(label="Binds de Hyprland cargados desde keybinds.conf")
        subtitle.add_css_class("subtitle")
        subtitle.set_xalign(0)

        self.count_label = Gtk.Label()
        self.count_label.add_css_class("counter")
        self.count_label.set_valign(Gtk.Align.CENTER)

        heading.append(title)
        heading.append(subtitle)
        topbar.append(mark)
        topbar.append(heading)
        topbar.append(self.count_label)

        self.update_count()
        return topbar

    def create_tab_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        bar.add_css_class("tab-bar")
        bar.set_halign(Gtk.Align.CENTER)

        tabs = [
            ("binds", "Atajos", "input-keyboard-symbolic"),
            ("gifs", "GIFs", "image-x-generic-symbolic"),
        ]

        first_button = None
        for tab_id, label, icon_name in tabs:
            button = Gtk.ToggleButton()
            button.add_css_class("tab-button")
            button.set_hexpand(False)

            content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            text = Gtk.Label(label=label)
            content.append(icon)
            content.append(text)
            button.set_child(content)

            button.connect("toggled", self.on_tab_toggled, tab_id)
            self.tab_buttons[tab_id] = button
            bar.append(button)

            if first_button is None:
                first_button = button

        if first_button is not None:
            first_button.set_active(True)

        return bar

    def create_tab_stack(self):
        self.tab_stack = Gtk.Stack()
        self.tab_stack.add_css_class("tab-stack")
        self.tab_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.tab_stack.set_transition_duration(180)
        self.tab_stack.set_vexpand(True)

        self.tab_stack.add_named(self.create_binds_page(), "binds")
        self.tab_stack.add_named(self.create_gifs_page(), "gifs")
        self.tab_stack.set_visible_child_name("binds")

        return self.tab_stack

    def create_binds_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page.add_css_class("tab-page")
        page.append(self.create_search())
        page.append(self.create_bind_list())
        return page

    def create_gifs_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page.add_css_class("tab-page")

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content.append(self.create_session_gif_gallery())
        content.append(self.create_media_gif_gallery())

        scrolled.set_child(content)
        page.append(scrolled)
        return page

    def on_tab_toggled(self, button, tab_id):
        if not button.get_active():
            other_active = any(
                other_id != tab_id and other_button.get_active()
                for other_id, other_button in self.tab_buttons.items()
            )
            if not other_active:
                button.set_active(True)
            return

        for other_id, other_button in self.tab_buttons.items():
            if other_id != tab_id and other_button.get_active():
                other_button.set_active(False)

        if self.tab_stack is not None:
            self.tab_stack.set_visible_child_name(tab_id)

    def create_session_gif_gallery(self):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        section.add_css_class("session-gallery")

        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        header.set_hexpand(True)

        title = Gtk.Label(label="GIFs para caelestia:session")
        title.add_css_class("session-gallery-title")
        title.set_xalign(0)

        copy = Gtk.Label(label=f"Carga automaticamente los .gif desde {SESSION_GIF_DIR}")
        copy.add_css_class("session-gallery-copy")
        copy.set_xalign(0)
        copy.set_ellipsize(Pango.EllipsizeMode.END)

        header.append(title)
        header.append(copy)

        self.session_image_button = Gtk.Button(label="Cambiar imagen")
        self.session_image_button.add_css_class("session-image-button")
        self.session_image_button.set_tooltip_text("Cambiar imagen del panel caelestia:session")
        self.session_image_button.set_valign(Gtk.Align.CENTER)
        self.session_image_button.connect("clicked", self.on_change_session_image)

        header_row.append(header)
        header_row.append(self.session_image_button)
        section.append(header_row)

        gifs = self.get_session_gifs()
        if not gifs:
            empty = Gtk.Label(label="Agrega GIFs en la carpeta sessiongif para verlos aqui.")
            empty.add_css_class("session-gallery-copy")
            empty.set_xalign(0)
            section.append(empty)
            return section

        grid = Gtk.FlowBox()
        grid.add_css_class("session-gif-grid")
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_min_children_per_line(1)
        grid.set_max_children_per_line(5)

        current_path = os.path.realpath(self.get_current_session_gif())
        self.session_gif_buttons = {}
        for path in gifs:
            grid.append(self.create_session_gif_card(path, current_path))

        section.append(grid)
        return section

    def create_session_gif_card(self, path, current_path):
        button = Gtk.Button()
        button.add_css_class("session-gif-card")
        button.set_tooltip_text(path)
        button.connect("clicked", self.on_session_gif_clicked, path)

        if os.path.realpath(path) == current_path:
            button.add_css_class("selected")

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        preview = self.create_gif_preview(path)

        name = Gtk.Label(label=self.get_session_gif_label(path))
        name.add_css_class("session-gif-name")
        name.set_ellipsize(Pango.EllipsizeMode.END)
        name.set_max_width_chars(14)

        content.append(preview)
        content.append(name)
        button.set_child(content)

        self.session_gif_buttons[path] = button
        return button

    def create_gif_preview(self, path):
        preview = Gtk.Picture()
        preview.add_css_class("session-gif-preview")
        preview.set_size_request(PREVIEW_LOGICAL_W, PREVIEW_LOGICAL_H)
        preview.set_can_shrink(True)
        preview.set_content_fit(Gtk.ContentFit.CONTAIN)

        decode_w = max(1, PREVIEW_LOGICAL_W * PREVIEW_DECODE_SCALE)
        decode_h = max(1, PREVIEW_LOGICAL_H * PREVIEW_DECODE_SCALE)

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                path, decode_w, decode_h, True
            )
            preview.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
        except GLib.Error:
            fallback = Gtk.Image.new_from_icon_name("image-missing-symbolic")
            fallback.add_css_class("session-gif-preview")
            fallback.set_size_request(PREVIEW_LOGICAL_W, PREVIEW_LOGICAL_H)
            fallback.set_pixel_size(24)
            return fallback

        return preview

    def create_media_gif_gallery(self):
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        section.add_css_class("session-gallery")

        header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        header.set_hexpand(True)

        title = Gtk.Label(label="GIFs para dashboard media (bongo cat)")
        title.add_css_class("session-gallery-title")
        title.set_xalign(0)

        copy = Gtk.Label(
            label=(
                "GIFs pensados para el dashboard media (velocidad distinta a session). "
                f"Carpeta: {MEDIA_GIF_DIR}"
            )
        )
        copy.add_css_class("session-gallery-copy")
        copy.set_xalign(0)
        copy.set_wrap(True)

        header.append(title)
        header.append(copy)

        self.media_image_button = Gtk.Button(label="Cambiar media")
        self.media_image_button.add_css_class("session-image-button")
        self.media_image_button.set_tooltip_text("Cambiar GIF del dashboard media (bongo cat)")
        self.media_image_button.set_valign(Gtk.Align.CENTER)
        self.media_image_button.connect("clicked", self.on_change_media_image)

        header_row.append(header)
        header_row.append(self.media_image_button)
        section.append(header_row)

        gifs = self.get_media_gifs()
        if not gifs:
            empty = Gtk.Label(
                label="Agrega archivos .gif en la carpeta mediagif para verlos aqui."
            )
            empty.add_css_class("session-gallery-copy")
            empty.set_xalign(0)
            section.append(empty)
            return section

        grid = Gtk.FlowBox()
        grid.add_css_class("session-gif-grid")
        grid.set_selection_mode(Gtk.SelectionMode.NONE)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_min_children_per_line(1)
        grid.set_max_children_per_line(5)

        current_path = os.path.realpath(self.get_current_media_gif())
        self.media_gif_buttons = {}
        for path in gifs:
            grid.append(self.create_media_gif_card(path, current_path))

        section.append(grid)
        return section

    def create_media_gif_card(self, path, current_path):
        button = Gtk.Button()
        button.add_css_class("session-gif-card")
        button.set_tooltip_text(path)
        button.connect("clicked", self.on_media_gif_clicked, path)

        if os.path.realpath(path) == current_path:
            button.add_css_class("selected-media")

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        preview = self.create_gif_preview(path)

        name = Gtk.Label(label=self.get_session_gif_label(path))
        name.add_css_class("session-gif-name")
        name.set_ellipsize(Pango.EllipsizeMode.END)
        name.set_max_width_chars(14)

        content.append(preview)
        content.append(name)
        button.set_child(content)

        self.media_gif_buttons[path] = button
        return button

    def get_media_gifs(self):
        return self.list_gif_paths(MEDIA_GIF_DIR)

    def get_current_media_gif(self):
        if not os.path.exists(CAELESTIA_CONFIG):
            return ""

        try:
            with open(CAELESTIA_CONFIG, "r", encoding="utf-8") as file:
                config = json.load(file)
        except (OSError, json.JSONDecodeError):
            return ""

        return config.get("paths", {}).get("mediaGif", "")

    def list_gif_paths(self, directory):
        if not os.path.isdir(directory):
            return []

        paths = []
        for name in os.listdir(directory):
            if name.lower().endswith(SESSION_GIF_EXTENSIONS):
                path = os.path.join(directory, name)
                if os.path.isfile(path):
                    paths.append(path)

        return sorted(paths, key=lambda path: os.path.basename(path).lower())

    def get_session_gifs(self):
        return self.list_gif_paths(SESSION_GIF_DIR)

    def get_session_gif_label(self, path):
        name = os.path.basename(path)
        label, _extension = os.path.splitext(name)
        return label

    def get_current_session_gif(self):
        if not os.path.exists(CAELESTIA_CONFIG):
            return ""

        try:
            with open(CAELESTIA_CONFIG, "r", encoding="utf-8") as file:
                config = json.load(file)
        except (OSError, json.JSONDecodeError):
            return ""

        return config.get("paths", {}).get("sessionGif", "")

    def on_session_gif_clicked(self, _button, path):
        try:
            self.set_session_gif(path)
        except (OSError, json.JSONDecodeError):
            if self.session_image_button is not None:
                self.flash_session_image_button(self.session_image_button, "No se pudo guardar")
            return

        self.update_session_gif_selection(path)
        if self.session_image_button is not None:
            self.flash_session_image_button(self.session_image_button, "GIF actualizado")

    def update_session_gif_selection(self, selected_path):
        selected_path = os.path.realpath(selected_path)

        for path, button in self.session_gif_buttons.items():
            if os.path.realpath(path) == selected_path:
                button.add_css_class("selected")
            else:
                button.remove_css_class("selected")

    def on_media_gif_clicked(self, _button, path):
        try:
            self.set_media_gif(path)
        except (OSError, json.JSONDecodeError):
            if self.media_image_button is not None:
                self.flash_media_image_button(self.media_image_button, "No se pudo guardar")
            return

        self.update_media_gif_selection(path)
        if self.media_image_button is not None:
            self.flash_media_image_button(self.media_image_button, "Media actualizado")

    def update_media_gif_selection(self, selected_path):
        selected_path = os.path.realpath(selected_path)

        for path, button in self.media_gif_buttons.items():
            if os.path.realpath(path) == selected_path:
                button.add_css_class("selected-media")
            else:
                button.remove_css_class("selected-media")

    def create_search(self):
        search = Gtk.SearchEntry()
        search.add_css_class("search-box")
        search.set_placeholder_text("Buscar por tecla, dispatcher o accion")
        search.set_margin_bottom(18)
        search.connect("search-changed", self.on_search_changed)
        return search

    def create_bind_list(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        self.listbox = Gtk.ListBox()
        self.listbox.add_css_class("bind-list")
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox.set_filter_func(self.filter_row)

        if not self.binds:
            self.listbox.append(self.create_empty_row())
        else:
            for bind in self.binds:
                self.listbox.append(self.create_bind_row(bind))

        scrolled.set_child(self.listbox)
        return scrolled

    def create_bind_row(self, bind):
        row = Gtk.ListBoxRow()
        row.search_text = self.get_search_text(bind)

        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        card.add_css_class("bind-card")

        keys = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=7)
        keys.set_valign(Gtk.Align.CENTER)
        keys.set_size_request(280, -1)

        for index, key in enumerate(bind["keys"]):
            if index:
                plus = Gtk.Label(label="+")
                plus.add_css_class("plus")
                keys.append(plus)

            chip = Gtk.Label(label=key)
            chip.add_css_class("key-chip")
            keys.append(chip)

        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        action_box.set_hexpand(True)

        action = Gtk.Label(label=bind["args"] or bind["dispatcher"])
        action.add_css_class("action")
        action.set_ellipsize(Pango.EllipsizeMode.END)
        action.set_xalign(0)

        dispatcher = Gtk.Label(label=bind["dispatcher"])
        dispatcher.add_css_class("dispatcher")
        dispatcher.set_ellipsize(Pango.EllipsizeMode.END)
        dispatcher.set_xalign(0)

        action_box.append(action)
        action_box.append(dispatcher)

        accent = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        accent.add_css_class("card-accent")

        run_button = Gtk.Button()
        run_button.add_css_class("run-button")
        run_button.set_tooltip_text("Ejecutar esta accion con hyprctl dispatch")
        run_button.set_valign(Gtk.Align.CENTER)
        self.set_run_button_icon(run_button, "media-playback-start-symbolic")
        run_button.connect("clicked", self.on_run_clicked, bind)

        card.append(accent)
        card.append(keys)
        card.append(action_box)
        card.append(run_button)
        row.set_child(card)

        return row

    def create_empty_row(self):
        row = Gtk.ListBoxRow()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.add_css_class("bind-card")
        box.set_margin_top(30)
        box.set_margin_bottom(30)

        title = Gtk.Label(label="No encontre binds")
        title.add_css_class("empty-title")

        copy = Gtk.Label(label=f"Revisa que exista {CONFIG}")
        copy.add_css_class("empty-copy")

        box.append(title)
        box.append(copy)
        row.set_child(box)

        return row

    def on_search_changed(self, entry):
        self.query = entry.get_text().strip().lower()
        self.listbox.invalidate_filter()
        self.update_count()

    def filter_row(self, row, _user_data=None):
        if not self.query or not hasattr(row, "search_text"):
            return True

        return self.query in row.search_text

    def on_run_clicked(self, button, bind):
        command = ["hyprctl", "dispatch", bind["dispatcher"]]
        args = self.strip_inline_comment(bind["args"])

        if args:
            command.append(args)

        try:
            subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self.set_run_button_icon(button, "dialog-warning-symbolic")
            button.set_tooltip_text("No se encontro hyprctl")
            button.set_sensitive(False)
            return

        self.set_run_button_icon(button, "emblem-ok-symbolic")
        GLib.timeout_add(1200, self.reset_run_button, button)

    def reset_run_button(self, button):
        self.set_run_button_icon(button, "media-playback-start-symbolic")
        return GLib.SOURCE_REMOVE

    def set_run_button_icon(self, button, icon_name):
        button.set_child(Gtk.Image.new_from_icon_name(icon_name))

    def on_change_session_image(self, button):
        dialog = Gtk.FileChooserNative(
            title="Elegir imagen para caelestia:session",
            transient_for=self.get_active_window(),
            action=Gtk.FileChooserAction.OPEN,
            accept_label="Usar imagen",
            cancel_label="Cancelar",
        )

        image_filter = Gtk.FileFilter()
        image_filter.set_name("Imagenes y GIFs")
        image_filter.add_mime_type("image/gif")
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_mime_type("image/webp")
        dialog.add_filter(image_filter)

        dialog.connect("response", self.on_session_image_selected, button)
        dialog.show()

    def on_change_media_image(self, button):
        dialog = Gtk.FileChooserNative(
            title="Elegir GIF para dashboard media",
            transient_for=self.get_active_window(),
            action=Gtk.FileChooserAction.OPEN,
            accept_label="Usar GIF",
            cancel_label="Cancelar",
        )

        image_filter = Gtk.FileFilter()
        image_filter.set_name("Imagenes y GIFs")
        image_filter.add_mime_type("image/gif")
        image_filter.add_mime_type("image/png")
        image_filter.add_mime_type("image/jpeg")
        image_filter.add_mime_type("image/webp")
        dialog.add_filter(image_filter)

        folder = Gio.File.new_for_path(MEDIA_GIF_DIR)
        try:
            dialog.set_current_folder(folder)
        except GLib.Error:
            pass

        dialog.connect("response", self.on_media_image_selected, button)
        dialog.show()

    def on_session_image_selected(self, dialog, response, button):
        try:
            if response != Gtk.ResponseType.ACCEPT:
                return

            file = dialog.get_file()
            if file is None:
                return

            path = file.get_path()
            if not path:
                return

            self.set_session_gif(path)
            self.update_session_gif_selection(path)
            self.flash_session_image_button(button, "Imagen actualizada")
        except (OSError, json.JSONDecodeError):
            self.flash_session_image_button(button, "No se pudo guardar")
        finally:
            dialog.destroy()

    def on_media_image_selected(self, dialog, response, button):
        try:
            if response != Gtk.ResponseType.ACCEPT:
                return

            file = dialog.get_file()
            if file is None:
                return

            path = file.get_path()
            if not path:
                return

            self.set_media_gif(path)
            self.update_media_gif_selection(path)
            self.flash_media_image_button(button, "Media actualizado")
        except (OSError, json.JSONDecodeError):
            self.flash_media_image_button(button, "No se pudo guardar")
        finally:
            dialog.destroy()

    def set_session_gif(self, path):
        config = {}

        if os.path.exists(CAELESTIA_CONFIG):
            with open(CAELESTIA_CONFIG, "r", encoding="utf-8") as file:
                config = json.load(file)

        config.setdefault("paths", {})["sessionGif"] = path

        os.makedirs(os.path.dirname(CAELESTIA_CONFIG), exist_ok=True)
        with open(CAELESTIA_CONFIG, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
            file.write("\n")

    def set_media_gif(self, path):
        config = {}

        if os.path.exists(CAELESTIA_CONFIG):
            with open(CAELESTIA_CONFIG, "r", encoding="utf-8") as file:
                config = json.load(file)

        config.setdefault("paths", {})["mediaGif"] = path

        os.makedirs(os.path.dirname(CAELESTIA_CONFIG), exist_ok=True)
        with open(CAELESTIA_CONFIG, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)
            file.write("\n")

    def flash_session_image_button(self, button, label):
        button.set_label(label)
        GLib.timeout_add(1600, self.reset_session_image_button, button)

    def reset_session_image_button(self, button):
        button.set_label("Cambiar imagen")
        return GLib.SOURCE_REMOVE

    def flash_media_image_button(self, button, label):
        button.set_label(label)
        GLib.timeout_add(1600, self.reset_media_image_button, button)

    def reset_media_image_button(self, button):
        button.set_label("Cambiar media")
        return GLib.SOURCE_REMOVE

    def update_count(self):
        if self.count_label is None:
            return

        visible = len(self.binds)
        if self.query:
            visible = sum(
                1
                for bind in self.binds
                if self.query in self.get_search_text(bind)
            )

        label = "1 bind" if visible == 1 else f"{visible} binds"
        self.count_label.set_text(label)

    def get_search_text(self, bind):
        return " ".join(
            [" ".join(bind["keys"]), bind["dispatcher"], bind["args"]]
        ).lower()

    def load_binds(self):
        binds = []
        variables = self.load_variables()

        if not os.path.exists(CONFIG):
            return binds

        with open(CONFIG, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line.startswith("bind"):
                    continue

                bind_type, _, value = line.partition("=")
                if bind_type.strip() not in BIND_TYPES:
                    continue

                value = self.resolve_variables(value.strip(), variables)
                parts = [part.strip() for part in value.split(",")]
                if len(parts) < 3:
                    continue

                keys = self.get_key_tokens([parts[0], parts[1]])
                dispatcher = parts[2]
                args = ", ".join(parts[3:]).strip()

                binds.append({
                    "keys": keys,
                    "dispatcher": dispatcher,
                    "args": args,
                })

        return binds

    def get_key_tokens(self, key_parts):
        keys = []

        for part in key_parts:
            for key in part.split("+"):
                key = key.strip()
                if key:
                    keys.append(self.describe_key(key))

        return keys

    def describe_key(self, key):
        label = KEY_LABELS.get(key.lower())
        if label:
            return label

        mouse_button = re.fullmatch(r"mouse:(\d+)", key.lower())
        if mouse_button:
            return f"Boton del mouse {mouse_button.group(1)}"

        return key

    def load_theme(self):
        theme = THEME_FALLBACKS.copy()

        if not os.path.exists(SCHEME_CONFIG):
            return theme

        with open(SCHEME_CONFIG, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line.startswith("$") or "=" not in line:
                    continue

                name, _, value = line.partition("=")
                name = name.strip()[1:]
                value = self.strip_inline_comment(value.strip())

                if name in theme and re.fullmatch(r"[0-9A-Fa-f]{6}", value):
                    theme[name] = f"#{value.lower()}"

        return theme

    def load_variables(self):
        variables = {}

        for path in self.get_config_files():
            if not os.path.exists(path):
                continue

            with open(path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()

                    if not line.startswith("$") or "=" not in line:
                        continue

                    name, _, value = line.partition("=")
                    value = self.strip_inline_comment(value.strip())
                    variables[name.strip()] = self.resolve_variables(value, variables)

        return variables

    def get_config_files(self):
        root_config = HYPR_CONFIG if os.path.exists(HYPR_CONFIG) else CONFIG
        files = []
        pending = [root_config]
        variables = {}

        while pending:
            path = os.path.expanduser(pending.pop(0))
            if path in files or not os.path.exists(path):
                continue

            files.append(path)

            with open(path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()

                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("$") and "=" in line:
                        name, _, value = line.partition("=")
                        value = self.strip_inline_comment(value.strip())
                        variables[name.strip()] = self.resolve_variables(value, variables)
                        continue

                    key, _, value = line.partition("=")
                    if key.strip() != "source":
                        continue

                    source = self.resolve_variables(value.strip(), variables)
                    source = os.path.expanduser(source)
                    matches = sorted(glob.glob(source))
                    pending.extend(matches or [source])

        return files

    def resolve_variables(self, value, variables):
        for _ in range(8):
            resolved = re.sub(
                r"\$[A-Za-z_][A-Za-z0-9_]*",
                lambda match: variables.get(match.group(0), match.group(0)),
                value,
            )

            if resolved == value:
                break

            value = resolved

        return value

    def strip_inline_comment(self, value):
        return re.sub(r"\s+#.*$", "", value).strip()


app = BindViewer()
app.run()
