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


def _dock_prop(attribute):
    return property(
        lambda self: self._anchors.check_dock(attribute),
        lambda self, value: self._anchors.set_dock(attribute, value),
    )


def _align_prop(attribute):
    return property(
        lambda self: False,  # Not meaningful
        lambda self, *others: self._anchors.set_align(attribute, others)
    )


class Anchored(ft.canvas.Canvas):
    DEFAULT_GAP = 10
    DEFAULT_PADDING = 10

    def __init__(
        self,
        content=None,
        parent=None,
        gap=None,
        top=None,
        bottom=None,
        left=None,
        right=None,
        width=None,
        height=None,
        center_x=None,
        center_y=None,
        align_top=None,
        align_bottom=None,
        align_left=None,
        align_right=None,
        align_width=None,
        align_height=None,
        align_center_x=None,
        align_center_y=None,
        dock_top_left=None,
        dock_top_right=None,
        dock_bottom_left=None,
        dock_bottom_right=None,
        dock_top_center=None,
        dock_bottom_center=None,
        dock_left_center=None,
        dock_right_center=None,
        dock_sides=None,
        dock_top_bottom=None,
        dock_top=None,
        dock_left=None,
        dock_bottom=None,
        dock_right=None,
        dock_center=None,
        dock_all=None,
        dock_above=None,
        dock_below=None,
        dock_right_of=None,
        dock_left_of=None,
        **kwargs
    ):
        self._anchors = AnchorManager(self)
        super().__init__(content=content, **kwargs)

        if parent:
            if type(parent) is AnchoredStack:
                parent.content.controls.append(self)
                self._anchors.parent = parent
            else:
                raise ValueError(f"parent should be of type AnchoredStack, not {type(parent)}")

        self.gap = gap

        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.width = width
        self.height = height
        self.center_x = center_x
        self.center_y = center_y
        self.align_top = align_top
        self.align_bottom = align_bottom
        self.align_left = align_left
        self.align_right = align_right
        self.align_width = align_width
        self.align_height = align_height
        self.align_center_x = align_center_x
        self.align_center_y = align_center_y
        self.dock_top_left = dock_top_left
        self.dock_top_right = dock_top_right
        self.dock_bottom_left = dock_bottom_left
        self.dock_bottom_right = dock_bottom_right
        self.dock_top_center = dock_top_center
        self.dock_bottom_center = dock_bottom_center
        self.dock_left_center = dock_left_center
        self.dock_right_center = dock_right_center
        self.dock_sides = dock_sides
        self.dock_top_bottom = dock_top_bottom
        self.dock_top = dock_top
        self.dock_left = dock_left
        self.dock_bottom = dock_bottom
        self.dock_right = dock_right
        self.dock_center = dock_center
        self.dock_all = dock_all
        self.dock_above = dock_above
        self.dock_below = dock_below
        self.dock_right_of = dock_right_of
        self.dock_left_of = dock_left_of

        self.on_resize = self._anchors.on_resize

    def is_contained_in(self, source):
        return isinstance(source.content, ft.Stack) and self in source.content.controls

    @property
    def gap(self):
        custom_gap = self._anchors.gap
        return custom_gap if custom_gap is not None else self.DEFAULT_GAP

    @gap.setter
    def gap(self, value):
        self._anchors.set_attribute("gap", value)

    top = _anchor_prop("top")
    bottom = _anchor_prop("bottom")
    left = _anchor_prop("left")
    right = _anchor_prop("right")
    width = _anchor_prop("width")
    height = _anchor_prop("height")
    center_x = _anchor_prop("center_x")
    center_y = _anchor_prop("center_y")

    align_top = _align_prop("top")
    align_bottom = _align_prop("bottom")
    align_left = _align_prop("left")
    align_right = _align_prop("right")
    align_width = _align_prop("width")
    align_height = _align_prop("height")
    align_center_x = _align_prop("center_x")
    align_center_y = _align_prop("center_y")

    dock_top_left = _dock_prop("dock_top_left")
    dock_top_right = _dock_prop("dock_top_right")
    dock_bottom_left = _dock_prop("dock_bottom_left")
    dock_bottom_right = _dock_prop("dock_bottom_right")
    dock_top_center = _dock_prop("dock_top_center")
    dock_bottom_center = _dock_prop("dock_bottom_center")
    dock_left_center = _dock_prop("dock_left_center")
    dock_right_center = _dock_prop("dock_right_center")
    dock_sides = _dock_prop("dock_sides")
    dock_top_bottom = _dock_prop("dock_top_bottom")
    dock_top = _dock_prop("dock_top")
    dock_left = _dock_prop("dock_left")
    dock_bottom = _dock_prop("dock_bottom")
    dock_right = _dock_prop("dock_right")
    dock_center = _dock_prop("dock_center")
    dock_all = _dock_prop("dock_all")

    dock_above = _dock_prop("dock_above")
    dock_below = _dock_prop("dock_below")
    dock_right_of = _dock_prop("dock_right_of")
    dock_left_of = _dock_prop("dock_left_of")


class AnchoredStack(Anchored):
    def __init__(self, controls=None, padding=None, **kwargs):
        controls = controls or []
        for control in controls or []:
            control.left = 0
        content = ft.Stack(controls=controls, expand=True)

        super().__init__(content=content, **kwargs)

        self.padding = padding

    def _get_children(self):
        children = super()._get_children()
        for child in self.content.controls:
            if isinstance(child, Anchored):
                child._anchors.parent = self
        return children

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
        self._anchors.set_attribute("padding", value)


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

    PARENT = "parent"
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

    DOCK_PARENT = {
        "dock_top_left": [TOP, LEFT],
        "dock_top_right": [TOP, RIGHT],
        "dock_bottom_left": [BOTTOM, LEFT],
        "dock_bottom_right": [BOTTOM, RIGHT],
        "dock_top_center": [TOP, CENTER_X],
        "dock_bottom_center": [BOTTOM, CENTER_X],
        "dock_left_center": [LEFT, CENTER_Y],
        "dock_right_center": [RIGHT, CENTER_Y],
        "dock_sides": [LEFT, RIGHT],
        "dock_top_bottom": [TOP, BOTTOM],
        "dock_top": [LEFT, TOP, RIGHT],
        "dock_left": [TOP, LEFT, BOTTOM],
        "dock_bottom": [LEFT, BOTTOM, RIGHT],
        "dock_right": [TOP, RIGHT, BOTTOM],
        "dock_center": [CENTER_X, CENTER_Y],
        "dock_all": [LEFT, RIGHT, TOP, BOTTOM],
    }

    DOCK_PEER = {
        "dock_above": (CENTER_X, BOTTOM, TOP),
        "dock_below": (CENTER_X, TOP, BOTTOM),
        "dock_right_of": (CENTER_Y, LEFT, RIGHT),
        "dock_left_of": (CENTER_Y, RIGHT, LEFT),
    }

    def __init__(self, managed, **kwargs):
        self.uuid = uuid.uuid4()
        self.managed = managed
        self.parent = None
        self.gap = None
        self.padding = None
        self.anchors = {}
        self.source_for = {}
        self.actuals = {}

    def check_dock(self, attribute):
        return all(self.anchors[dock_attribute] for dock_attribute in self.DOCK_PARENT[attribute])

    def set_dock(self, attribute, other):
        if other is None:
            return

        if attributes := self.DOCK_PARENT.get(attribute):
            for dock_attribute in attributes:
                self.UPDATE_QUEUE.put({"set": (self, dock_attribute, Anchor(other, dock_attribute))})
        else:
            center, my_edge, your_edge = self.DOCK_PEER[attribute]
            self.UPDATE_QUEUE.put({"set": (self, center, Anchor(other, center))})
            self.UPDATE_QUEUE.put({"set": (self, my_edge, Anchor(other, your_edge))})

        self.process_queue()

    def set_align(self, attribute, others):
        if not all(others):
            return

        for other in others:
            self.UPDATE_QUEUE.put({"set": (self, attribute, Anchor(other, attribute))})
        self.process_queue()

    def set_anchor(self, attribute, value):
        self.UPDATE_QUEUE.put({"set": (self, attribute, value)})
        self.process_queue()

    def set_attribute(self, attribute, value):
        self.UPDATE_QUEUE.put({"attribute": (self, attribute, value)})
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

                    elif "attribute" in task:
                        manager, attribute, value = task["attribute"]
                        setattr(manager, attribute, value)
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
                source_control = anchor.control
                source_attribute = anchor.attribute
                source = source_control._anchors
                source_type = self.ATTRIBUTE_TYPES[source_attribute]
                target_type = self.ATTRIBUTE_TYPES[attribute]

                if self.managed.is_contained_in(source_control):
                    getter = self.GETTERS_PARENT[source_attribute]
                    source_value = getter(source.actuals)
                    if source_type == self.LEADING and target_type == self.LEADING:
                        source_value += self.parent.padding
                    elif source_type == self.TRAILING and target_type == self.TRAILING:
                        source_value -= self.parent.padding
                else:
                    getter = self.GETTERS_PEER[source_attribute]
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

        # if type(self) is AnchoredStack:
        #     for control in self.content.controls:
        #         if isinstance(control, Anchored):
        #             control._anchors.update_anchor_actuals()

        for control in self.source_for.values():
            control._anchors.update_anchor_actuals()


class Anchor:
    def __init__(self, control, attribute):
        self.control = control
        self.attribute = attribute


if __name__ == "__main__":

    def main(page: ft.Page):
        page.add(root := AnchoredStack(expand=True))
        search_button = Anchored(ft.ElevatedButton("Search"), dock_center=root)
        rescue_button = Anchored(ft.ElevatedButton("Rescue"), dock_below=search_button)
        root.controls = [search_button, rescue_button]

    ft.app(main)
