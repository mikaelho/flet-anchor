import inspect
import operator
import queue
import threading
import uuid
from dataclasses import dataclass

import flet as ft
from flet_core.canvas import CanvasResizeEvent


LEFT, RIGHT, TOP, BOTTOM, WIDTH, HEIGHT, CENTER_X, CENTER_Y = (
        "left", "right", "top", "bottom", "width", "height", "center_x", "center_y"
    )


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
            if type(parent) is AnchorStack:
                parent.content.controls.append(self)
                self._anchors.parent = parent
            else:
                raise ValueError(f"parent should be of type AnchorStack, not {type(parent)}")

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


class AnchorStack(Anchored):

    DEFAULT_PADDING = 0

    def __init__(self, controls=None, padding=None, **kwargs):
        controls = controls or []
        for control in controls or []:
            control.left = 0
        content = ft.Stack(controls=controls, expand=True)

        super().__init__(content=content, **kwargs)

        self._wrap_controls()

        self.padding = padding

    @property
    def controls(self):
        return self.content.controls

    @controls.setter
    def controls(self, value):
        self.content.controls = value

        for control in self.content.controls:
            if type(control) is Anchored:
                control._anchors.parent = self

    def _wrap_controls(self):
        tracked_list = AnchorList(self.controls)
        tracked_list.stack = self
        self.controls = tracked_list

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

    SETTERS = {
        LEFT: lambda value, anchors, actuals, parent_actuals: {"left": value},
        RIGHT: lambda value, anchors, actuals, parent_actuals: {"right": parent_actuals.get("width", 0) - value},
        TOP: lambda value, anchors, actuals, parent_actuals: {"top": value},
        BOTTOM: lambda value, anchors, actuals, parent_actuals: {"bottom": parent_actuals.get("height", 0) - value},
        WIDTH: lambda value, anchors, actuals, parent_actuals: {"width": value},
        HEIGHT: lambda value, anchors, actuals, parent_actuals: {"height": value},
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
        self.conditions = {}
        self.conditional_anchors = {}
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
                        if conditions_from_context := Anchor.get_current_conditions():
                            context_id, current_conditions = conditions_from_context
                            manager.conditions[context_id] = current_conditions
                            manager.conditional_anchors.setdefault(context_id, {})[attribute] = value
                        else:
                            manager.anchors[attribute] = value

                        if type(value) is Anchor:
                            value._control._anchors.register(manager.managed)

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
        self.check_conditions()

        self.update_anchors(self.anchors)

        for control in self.source_for.values():
            control._anchors.update_anchor_actuals()

    def update_anchors(self, anchors):
        for attribute, anchor in anchors.items():
            if anchor is None:
                continue
            # print (self.managed.content, attribute, anchor)
            if type(anchor) is not Anchor:
                source_value = anchor
            else:
                target_data = Anchor.TargetData(self.managed, attribute, self.parent)
                source_value = anchor._resolve(target_data)
                if source_value is None:
                    continue

            setter = self.SETTERS[attribute]
            set_value = setter(source_value, self.anchors, self.actuals, self.parent._anchors.actuals)

            for set_attribute, final_value in set_value.items():
                if self.actuals.get(set_attribute) != final_value:
                    self.actuals[set_attribute] = final_value
                    self.managed._set_attr(set_attribute, final_value)

    def check_conditions(self):
        target = Anchor.TargetData(self.managed, TOP, self.parent)  # Dummy attribute
        for context_id, conditions in self.conditions.items():
            if all(
                Anchor._resolve_recursively(condition, target)
                for condition_list in conditions for condition in condition_list
            ):
                self.update_anchors(self.conditional_anchors[context_id])


class Anchor:
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
        LEFT: lambda source_actuals, parent_actuals: (
            source_actuals.get("left")
            if source_actuals.get("left") is not None
            else (parent_actuals.get("width", 0) - source_actuals.get("right", 0) - source_actuals.get("width", 0))
        ),
        RIGHT: lambda source_actuals, parent_actuals: (
            (parent_actuals.get("width", 0) - source_actuals.get("right"))
            if source_actuals.get("right") is not None
            else (source_actuals.get("left", 0) + source_actuals.get("width", 0))
        ),
        TOP: lambda source_actuals, parent_actuals: (
            source_actuals.get("top")
            if source_actuals.get("top") is not None
            else (parent_actuals.get("height", 0) - source_actuals.get("bottom", 0) - source_actuals.get("height", 0))
        ),
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

    @dataclass
    class TargetData:
        control: Anchored
        attribute: str
        parent: Anchored

    def __init__(self, control, attribute):
        self._control = control
        self._attribute = attribute
        self._modifiers = None
        self._conditions = []
        self._alternative = None
        self._real_conditions = False
        self._max_of = set()
        self._min_of = set()
        self._value = None
        self._share = None

    def share(self, share_of, total):
        self._share = share_of, total
        return self

    def __str__(self):
        return f"{isinstance(self._control, Anchored) and type(self._control.content).__name__ or self._control}.{self._attribute}"

    def _add_modifier(self, op, other):
        if self._modifiers is None:
            self._modifiers = lambda: self._value

        self._modifiers = {"op": op, "left": self._modifiers, "right": other}

        return self

    def _resolve(self, target: TargetData, was=None):
        result = None
        if self._resolve_conditions(target):
            if self._control == "constant":
                result = self._attribute
            elif self._max_of and was != "max":
                result = max(self._resolve_many(self._max_of, target, "max"))
            elif self._min_of and was != "min":
                result = min(self._resolve_many(self._min_of, target, "min"))
            else:
                result = self._resolve_one(target)
        elif self._alternative:
            result = self._resolve_alternative(target)

        if result is None:
            return None

        if self._share is not None:
            result = self._apply_share(result, target)

        return result

    def _resolve_alternative(self, target):
        if type(self._alternative) is Anchor:
            return self._alternative._resolve(target)
        else:
            return self._alternative

    def _resolve_many(self, anchors, target: TargetData, was=None):
        return (
            anchor._resolve(target, was)
            if type(anchor) is Anchor
            else anchor
            for anchor in anchors
        )

    def _resolve_one(self, target: TargetData):
        source_control = self._control
        source_attribute = self._attribute
        source = source_control._anchors
        source_type = self.ATTRIBUTE_TYPES[source_attribute]
        target_type = self.ATTRIBUTE_TYPES[target.attribute]

        if target.control.is_contained_in(source_control):
            getter = self.GETTERS_PARENT[source_attribute]
            source_value = getter(source.actuals)
            if source_type == self.LEADING and target_type == self.LEADING:
                source_value += target.parent.padding
            elif source_type == self.TRAILING and target_type == self.TRAILING:
                source_value -= target.parent.padding
        else:
            getter = self.GETTERS_PEER[source_attribute]
            source_value = getter(source.actuals, source.parent._anchors.actuals)

            if source_type == self.LEADING and target_type == self.TRAILING:
                source_value -= target.control.gap
            elif source_type == self.TRAILING and target_type == self.LEADING:
                source_value += target.control.gap

        return self._resolve_modifiers(source_value, target)

    def _resolve_modifiers(self, source_value, target: TargetData):
        if self._modifiers is None:
            return source_value

        self._value = source_value

        return self._resolve_recursively(self._modifiers, target)

    def _resolve_conditions(self, target: TargetData):
        # print(f"{self.conditions=} {self._real_conditions=} {list(self._max_of)=}")
        if not self._real_conditions:
            return True

        return all(Anchor._resolve_recursively(condition, target) for condition in self._conditions[0]._conditions)

    @classmethod
    def _resolve_recursively(cls, value, target: TargetData):
        if type(value) is dict:
            return value["op"](
                cls._resolve_recursively(value["left"], target), cls._resolve_recursively(value["right"], target)
            )
        elif type(value) is Anchor:
            return value._resolve(target)
        elif callable(value):
            return value()
        else:
            return value

    def _apply_share(self, value, target):
        share_of, total = self._share
        parent_anchors: AnchorManager = target.parent._anchors
        target_anchors: AnchorManager = target.control._anchors
        padding = parent_anchors.padding if parent_anchors.padding is not None else target.parent.DEFAULT_PADDING
        gap = target_anchors.gap if target_anchors.gap is not None else target.control.DEFAULT_GAP

        final_share = ((value - (total - 1) * gap - 2 * padding) / total) * share_of + (share_of - 1) * gap

        return final_share

    def __add__(self, other):
        return self._add_modifier(operator.add, other)

    def __sub__(self, other):
        return self._add_modifier(operator.sub, other)

    def __mul__(self, other):
        return self._add_modifier(operator.mul, other)

    def __truediv__(self, other):
        return self._add_modifier(operator.truediv, other)

    def __floordiv__(self, other):
        return self._add_modifier(operator.floordiv, other)

    def __mod__(self, other):
        return self._add_modifier(operator.mod, other)

    def __radd__(self, other):
        return self._add_modifier(operator.add, other)

    def __rsub__(self, other):
        return self._add_modifier(operator.sub, other)

    def __rmul__(self, other):
        return self._add_modifier(operator.mul, other)

    def __rtruediv__(self, other):
        return self._add_modifier(operator.truediv, other)

    def __rfloordiv__(self, other):
        return self._add_modifier(operator.floordiv, other)

    def __rmod__(self, other):
        return self._add_modifier(operator.mod, other)

    def __pow__(self, other, modulo=None):
        return self._add_modifier(operator.pow, other)

    def __and__(self, other):
        other._conditions.append(self)
        other._real_conditions = True
        return other

    def __or__(self, other):
        self._alternative = other
        return self

    # Double duty for conditions and min/max - conditions are only actually used if _real_conditions set (in __add__)

    def __lt__(self, other):
        self.add_condition(operator.lt, other)

        self._min_of.add(self)
        if type(other) is Anchor and other._min_of:
            self._min_of |= other._min_of
        else:
            self._min_of.add(other)

        return self

    def __gt__(self, other):
        self.add_condition(operator.gt, other)

        self._max_of.add(self)
        if type(other) is Anchor and other._max_of:
            self._max_of |= other._max_of
        else:
            self._max_of.add(other)

        return self

    # Anchors in min/max must play False in order to come out as the winner
    def __bool__(self):
        if self._conditions and not self._real_conditions:
            return False

        return True

    # For conditions

    def __le__(self, other):
        self.add_condition(operator.le, other)

        return self

    def __ge__(self, other):
        self.add_condition(operator.ge, other)

        return self

    # def __eq__(self, other):
    #     self.add_condition(operator.eq, other)
    #
    # def __ne__(self, other):
    #     self.add_condition(operator.ne, other)

    def add_condition(self, operation, other):
        self._conditions.append({"op": operation, "left": self, "right": other})

    # As a context manager

    def __enter__(self):
        frame = inspect.currentframe().f_back.f_back
        conditions = frame.f_locals.get("_flet_anchor_conditions", {})
        conditions.setdefault("context_ids", []).append(uuid.uuid4())
        conditions.setdefault("conditions", []).append(self._conditions)
        frame.f_locals["_flet_anchor_conditions"] = conditions

    def __exit__(self, exc_type, exc_val, exc_tb):
        frame = inspect.currentframe().f_back.f_back
        conditions = frame.f_locals.get("_flet_anchor_conditions")
        conditions["context_ids"].pop()
        conditions["conditions"].pop()
        if not conditions["conditions"]:
            del frame.f_locals["_flet_anchor_conditions"]

    @staticmethod
    def get_current_conditions():
        frame = inspect.currentframe()
        while frame:
            if conditions := frame.f_locals.get("_flet_anchor_conditions"):
                context_id = conditions["context_ids"][-1]
                current_conditions = conditions["conditions"]
                return context_id, list(current_conditions)
            frame = frame.f_back
        return None


class AnchorList(list):
    """
    Capture append and extend on the controls list in order to make sure the controls know about the parent.
    """

    def append(self, item):
        super().append(item)

        self.stack._wrap_controls()

    def extend(self, items):
        super().extend(items)

        self.stack._wrap_controls()


if __name__ == "__main__":

    def main(page: ft.Page):
        page.add(root := AnchorStack(expand=True))

        search_button = Anchored(ft.FilledButton("Search"), dock_top_right=root)
        search_field = Anchored(
            ft.Container(ft.TextField(dense=True), bgcolor=ft.colors.BLUE_GREY_900),
            dock_top_left=root,
            right=search_button.left,
            align_height=search_button
        )
        done_button = Anchored(ft.FilledButton("Done"), dock_bottom_right=root)
        result_area = Anchored(
            ft.Container(results := ft.ListView(), bgcolor=ft.colors.BLUE_GREY_900),
            dock_sides=root,
            top=search_field.bottom,
            bottom=done_button.top
        )

        results.controls = [
            ft.ListTile(title=ft.Text("Value " * (i + 1), size=12), height=40) for i in range(50)
        ]

        root.controls = [search_field, search_button, result_area, done_button]


    ft.app(main)
