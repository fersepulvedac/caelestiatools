#!/usr/bin/env python

import gi
import glob
import json
import os
import re
import subprocess

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, Gio, GLib, Gtk, Pango

HYPR_CONFIG = os.path.expanduser("~/.config/hypr/hyprland.conf")
CONFIG = os.path.expanduser("~/.config/hypr/hyprland/keybinds.conf")
CAELESTIA_CONFIG = os.path.expanduser("~/.config/caelestia/shell.json")
SCHEME_CONFIG = os.path.expanduser("~/.config/hypr/scheme/current.conf")
SCHEME_DIR = os.path.dirname(SCHEME_CONFIG)
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

    def do_activate(self):
        self.install_css()
        self.watch_scheme()
        self.binds = self.load_binds()

        window = Gtk.ApplicationWindow(application=self)
        window.set_title("Atajos de Caelestia")
        window.set_default_size(860, 620)

        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        shell.add_css_class("app-shell")

        shell.append(self.create_header())
        shell.append(self.create_search())
        shell.append(self.create_bind_list())

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

        self.session_image_button = Gtk.Button(label="Cambiar imagen")
        self.session_image_button.add_css_class("session-image-button")
        self.session_image_button.set_tooltip_text("Cambiar imagen del panel caelestia:session")
        self.session_image_button.set_valign(Gtk.Align.CENTER)
        self.session_image_button.connect("clicked", self.on_change_session_image)

        heading.append(title)
        heading.append(subtitle)
        topbar.append(mark)
        topbar.append(heading)
        topbar.append(self.session_image_button)
        topbar.append(self.count_label)

        self.update_count()
        return topbar

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
            self.flash_session_image_button(button, "Imagen actualizada")
        except (OSError, json.JSONDecodeError):
            self.flash_session_image_button(button, "No se pudo guardar")
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

    def flash_session_image_button(self, button, label):
        button.set_label(label)
        GLib.timeout_add(1600, self.reset_session_image_button, button)

    def reset_session_image_button(self, button):
        button.set_label("Cambiar imagen")
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
