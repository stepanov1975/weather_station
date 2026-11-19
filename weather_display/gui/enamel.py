"""Composite the kiosk's live Tk labels onto one continuous enamel surface."""

from pathlib import Path
import tkinter as tk

from PIL import Image, ImageFilter, ImageTk


class EnamelSurface(tk.Canvas):
    """Let Tk measure and wrap the widgets, then paint their faces and relief together."""

    def __init__(self, window, labels, rules):
        super().__init__(window, borderwidth=0, highlightthickness=0, takefocus=False)
        self.labels = labels
        self.rules = rules
        self.pending = False
        self.states: dict = {}
        self.photos: dict = {}
        with Image.open(Path(__file__).resolve().parents[1] / "assets/enamel_backing.png") as image:
            self.backing = image.copy()
        self.place(x=0, y=0, relwidth=1, relheight=1)
        self.invalidate()

    def invalidate(self):
        if not self.pending:
            self.pending = True
            self.after_idle(self._paint)

    @staticmethod
    def widget_tag(widget):
        return f"widget_{id(widget)}"

    def _changed(self, tag, state):
        if self.states.get(tag) == state:
            return False
        self.states[tag] = state
        self.delete(tag)
        return True

    def _paint(self):
        self.pending = False
        width, height = self.winfo_width(), self.winfo_height()
        if min(width, height) <= 1:
            return
        scale = min(width / 1440, height / 810)
        if self._changed("backing", (width, height)):
            self.photos["backing"] = ImageTk.PhotoImage(
                self.backing.resize((width, height), Image.Resampling.BILINEAR), master=self)
            self.create_image(0, 0, anchor="nw", image=self.photos["backing"], tags="backing")
            self.tag_lower("backing")

        left, top = self.winfo_rootx(), self.winfo_rooty()
        for rule in self.rules:
            tag = self.widget_tag(rule)
            x, y = rule.winfo_rootx() - left, rule.winfo_rooty() - top
            w, h = rule.winfo_width(), rule.winfo_height()
            if self._changed(tag, (x, y, w, h, rule.winfo_ismapped())) and rule.winfo_ismapped():
                dx, dy = (0, 1) if w > h else (1, 0)
                for offset, color in ((0, "#10251e"), (1, "#698175")):
                    self.create_line(x+dx*offset, y+dy*offset, x+w-1+dx*offset, y+h-1+dy*offset,
                                     fill=color, tags=tag)

        for widget, role in self.labels:
            tag = self.widget_tag(widget)
            if not widget.winfo_ismapped():
                self._changed(tag, "hidden")
                self.photos.pop(tag, None)
                continue
            # Use the actual Tk label's device-pixel font and wrap length at the current DPI.
            label = widget._label
            x = label.winfo_rootx() - left
            y = label.winfo_rooty() - top + label.winfo_height() / 2
            image = widget.cget("image")
            if image is not None:
                x += label.winfo_width() / 2
                photo = label.cget("image")
                size = tuple(int(self.tk.call("image", dimension, photo)) for dimension in ("width", "height"))
                if self._changed(tag, (x, y, image, size, scale)):
                    self._paint_image(tag, x, y, image.cget("light_image"), size, scale)
                continue
            text, font = widget.cget("text"), str(label.cget("font"))
            color, wrap = widget.cget("text_color"), int(label.cget("wraplength"))
            if self._changed(tag, (x, y, text, font, color, wrap, scale)) and text:
                if role == "network":
                    radius = max(2, round(4 * scale))
                    self.create_oval(x, y-radius, x+2*radius, y+radius, fill=color,
                                     outline="#688073", tags=tag)
                    x += 3.5 * radius
                large = role in ("time", "day_number", "current_temp_value", "current_humidity_value")
                layers = ((5, 7, "#0b1b14"), (4, 5, "#273e33"), (3, 4, "#3d554b"),
                          (2, 3, "#4d695b"), (1, 2, "#678476"), (0, 1, "#7b9c8e")) if large else (
                          (2, 3, "#11231c"), (1, 2, "#344f45"), (0, 1, "#69847b"))
                for dx, dy, ink in (*layers, (0, 0, color)):
                    self.create_text(x+round(1.58*scale*dx), y+round(1.58*scale*dy),
                                     anchor="w", text=text, font=font, fill=ink, width=wrap, tags=tag)

    def _paint_image(self, tag, x, y, source, size, scale):
        face = source.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        offset = max(1, round(4 * scale))
        mask = Image.new("L", (size[0]+3*offset, size[1]+3*offset))
        mask.paste(face.getchannel("A"), (2*offset, 2*offset))
        relief = Image.new("RGBA", mask.size, "#0e1c16")
        relief.putalpha(mask.filter(ImageFilter.GaussianBlur(offset / 2)))
        relief.alpha_composite(face, (offset, offset))
        self.photos[tag] = ImageTk.PhotoImage(relief, master=self)
        self.create_image(x-size[0]/2-offset, y-size[1]/2-offset, anchor="nw",
                          image=self.photos[tag], tags=tag)
