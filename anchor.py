import queue
import threading
import uuid

import flet as ft
from flet_core.canvas import CanvasResizeEvent


def _anchor_prop(attribute):
    return property(
        lambda self: Anchor(self, attribute),
        lambda self, value: self._anchors.set_anchor(attribute, value),
    )


class Anchored(ft.canvas.Canvas):
    DEFAULT_GAP = 10
    DEFAULT_PADDING = 10

    def __init__(self, content=None, **kwargs):
        self._anchors = self.get_manager(kwargs)
        super().__init__(content=content, **kwargs)
        self.on_resize = self._anchors.on_resize

    def get_manager(self, kwargs):
        top = kwargs.pop("top", None)
        bottom = kwargs.pop("bottom", None)
        left = kwargs.pop("left", None)
        right = kwargs.pop("right", None)
        width = kwargs.pop("width", None)
        height = kwargs.pop("height", None)
        center_x = kwargs.pop("center_x", None)
        center_y = kwargs.pop("center_y", None)
        gap = kwargs.pop("gap", None)
        padding = kwargs.pop("padding", None)

        return AnchorManager(
            self,
            top=top,
            bottom=bottom,
            left=left,
            right=right,
            width=width,
            height=height,
            center_x=center_x,
            center_y=center_y,
            gap=gap,
            padding=padding,
        )

    def is_contained_in(self, source):
        return isinstance(source.content, ft.Stack) and self in source.content.controls

    @property
    def gap(self):
        custom_gap = self._anchors.gap
        return custom_gap if custom_gap is not None else self.DEFAULT_GAP

    @gap.setter
    def gap(self, value):
        self._anchors.gap = value

    top = _anchor_prop("top")
    bottom = _anchor_prop("bottom")
    left = _anchor_prop("left")
    right = _anchor_prop("right")
    width = _anchor_prop("width")
    height = _anchor_prop("height")
    center_x = _anchor_prop("center_x")
    center_y = _anchor_prop("center_y")


class AnchoredStack(Anchored):
    def __init__(self, controls=None, **kwargs):
        controls = controls or []
        for control in controls or []:
            control.left = 0
        content = ft.Stack(controls=controls, expand=True)

        super().__init__(content=content, **kwargs)

    @property
    def controls(self):
        return self.content.controls

    @controls.setter
    def controls(self, value):
        self.content.controls = value

        for control in value:
            if type(control) is Anchored:
                control._anchors.parent = self

    @property
    def padding(self):
        custom_padding = self._anchors.padding
        return custom_padding if custom_padding is not None else self.DEFAULT_PADDING

    @padding.setter
    def padding(self, value):
        self._anchors.padding = value


class AnchorManager:
    UPDATE_LOCK = threading.RLock()
    UPDATE_QUEUE = queue.Queue()

    LEFT, RIGHT, TOP, BOTTOM, WIDTH, HEIGHT, CENTER_X, CENTER_Y = (
        "left", "right", "top", "bottom", "width", "height", "center_x", "center_y"
    )

    GETTERS_PARENT = {
        LEFT: lambda parent_actuals: 0,
        RIGHT: lambda parent_actuals: parent_actuals.get("width", 0),
        TOP: lambda parent_actuals: 0,
        BOTTOM: lambda parent_actuals: parent_actuals.get("height", 0),
        WIDTH: lambda parent_actuals: parent_actuals.get("width", 0),
        HEIGHT: lambda parent_actuals: parent_actuals.get("height", 0),
        CENTER_X: lambda parent_actuals: parent_actuals.get("width", 0) / 2,
        CENTER_Y: lambda parent_actuals: parent_actuals.get("height", 0) / 2,
    }

    GETTERS_PEER = {
        LEFT: lambda source_actuals, parent_actuals: source_actuals.get("left", 0),
        RIGHT: lambda source_actuals, parent_actuals: (
            (parent_actuals.get("width", 0) - source_actuals.get("right"))
            if source_actuals.get("right") is not None
            else (source_actuals.get("left", 0) + source_actuals.get("width", 0))
        ),
        TOP: lambda source_actuals, parent_actuals: source_actuals.get("top", 0),
        BOTTOM: lambda source_actuals, parent_actuals: (
            (parent_actuals.get("height", 0) - source_actuals.get("bottom"))
            if source_actuals.get("bottom") is not None
            else (source_actuals.get("top", 0) + source_actuals.get("height", 0))
        ),
        WIDTH: lambda source_actuals, parent_actuals: source_actuals.get("width", 0),
        HEIGHT: lambda source_actuals, parent_actuals: source_actuals.get("height", 0),
        CENTER_X: lambda source_actuals, parent_actuals: (
            source_actuals.get("left", 0) + source_actuals.get("width", 0) / 2
        ),
        CENTER_Y: lambda source_actuals, parent_actuals: (
            source_actuals.get("top", 0) + source_actuals.get("height", 0) / 2
        ),
    }

    SETTERS = {
        LEFT: lambda value, anchors, actuals, parent_actuals: {"left": value},
        RIGHT: lambda value, anchors, actuals, parent_actuals: {"right": parent_actuals.get("width", 0) - value},
        TOP: lambda value, anchors, actuals, parent_actuals: {"top": value},
        BOTTOM: lambda value, anchors, actuals, parent_actuals: {"bottom": parent_actuals.get("height", 0) - value},
        CENTER_X: lambda value, anchors, actuals, parent_actuals: (
            {"width": 2 * (value - actuals.get("left", 0))}  # left locked, width must give
            if anchors.get("left") is not None
            else {
                "width": 2 * (parent_actuals.get("width", 0) - actuals.get("right", 0) - value)
            }  # right locked, width must give
            if anchors.get("right") is not None
            else {"left": value - actuals.get("width", 0) / 2}  # Neither locked, move so that center in right place
        ),
        CENTER_Y: lambda value, anchors, actuals, parent_actuals: (
            {"height": 2 * (value - actuals.get("top", 0))}  # top locked, height must give
            if anchors.get("top") is not None
            else {
                "height": 2 * (parent_actuals.get("height", 0) - actuals.get("bottom", 0) - value)
            }  # bottom locked, change height
            if anchors.get("bottom") is not None
            else {"top": value - actuals.get("height", 0) / 2}  # Neither locked, move so that center in right place
        ),
    }

    LEADING, TRAILING, NEUTRAL = "leading", "trailing", "neutral"

    ATTRIBUTE_TYPES = {
        WIDTH: NEUTRAL,
        HEIGHT: NEUTRAL,
        LEFT: LEADING,
        RIGHT: TRAILING,
        TOP: LEADING,
        BOTTOM: TRAILING,
        CENTER_X: NEUTRAL,
        CENTER_Y: NEUTRAL,
    }

    def __init__(self, managed, **kwargs):
        self.uuid = uuid.uuid4()
        self.managed = managed
        self.parent = None
        self.gap = kwargs.pop("gap")
        self.padding = kwargs.pop("padding")
        self.anchors = {**kwargs}
        self.source_for = {}
        self.actuals = {}

    def set_anchor(self, attribute, value):
        self.UPDATE_QUEUE.put({"set": (self, attribute, value)})
        self.process_queue()

    def register(self, dependent):
        self.source_for[dependent._anchors.uuid] = dependent

    def on_resize(self, event: CanvasResizeEvent):
        self.UPDATE_QUEUE.put({"resize": (self, event.width, event.height)})
        self.process_queue()

    def process_queue(self):
        with self.UPDATE_LOCK:
            while True:
                try:
                    task = self.UPDATE_QUEUE.get_nowait()
                    if "set" in task:
                        manager, attribute, value = task["set"]
                        manager.anchors[attribute] = value

                        if type(value) is Anchor:
                            value.control._anchors.register(manager.managed)

                        if manager.managed.page:  # If we are being displayed
                            manager.update_anchor_actuals()

                    elif "resize" in task:
                        manager, width, height = task["resize"]

                        manager.actuals["width"] = width
                        manager.actuals["height"] = height
                        manager.update_anchor_actuals()

                except queue.Empty:
                    break

            if self.managed.page:
                self.managed.page.update()

    def update_anchor_actuals(self):
        for attribute, anchor in self.anchors.items():
            if anchor is None:
                continue
            if type(anchor) is not Anchor:
                source_value = anchor
            else:
                source = anchor.control._anchors
                source_type = self.ATTRIBUTE_TYPES[anchor.attribute]
                target_type = self.ATTRIBUTE_TYPES[attribute]
                if self.managed.is_contained_in(anchor.control):
                    getter = self.GETTERS_PARENT[anchor.attribute]
                    source_value = getter(source.actuals)
                    if source_type == self.LEADING and target_type == self.LEADING:
                        source_value += self.parent.padding
                    elif source_type == self.TRAILING and target_type == self.TRAILING:
                        source_value -= self.parent.padding
                else:
                    getter = self.GETTERS_PEER[anchor.attribute]
                    source_value = getter(source.actuals, source.parent._anchors.actuals)
                    if source_type == self.LEADING and target_type == self.TRAILING:
                        source_value -= self.managed.gap
                    elif source_type == self.TRAILING and target_type == self.LEADING:
                        source_value += self.managed.gap
            setter = self.SETTERS[attribute]
            for set_attribute, final_value in setter(
                source_value, self.anchors, self.actuals, self.parent._anchors.actuals
            ).items():
                if self.actuals.get(set_attribute) != final_value:
                    self.actuals[set_attribute] = final_value
                    self.managed._set_attr(set_attribute, final_value)

        for control in self.source_for.values():
            control._anchors.update_anchor_actuals()


class Anchor:
    def __init__(self, control, attribute):
        self.control = control
        self.attribute = attribute


if __name__ == "__main__":

    def main(page: ft.Page):
        page.padding = 0
        page.add(root := AnchoredStack(expand=True))
        # search_button = Anchored(ft.ElevatedButton("Search"), parent=root, center=True)
        # rescue_button = Anchored(ft.ElevatedButton("Rescue"), below=search_button)

        search_button = Anchored(ft.ElevatedButton("Search"))
        rescue_button = Anchored(ft.ElevatedButton("Rescue"))
        search_button.center_x = root.center_x
        search_button.top = root.top
        rescue_button.center_x = search_button.center_x
        rescue_button.top = search_button.bottom

        root.controls = [search_button, rescue_button]

    ft.app(main)
