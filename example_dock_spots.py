import anchor as a
import flet as ft


def main(page: ft.Page):
    page.add(root := a.AnchorStack(expand=True))

    docks = """
    dock_top_left
    dock_top_right
    dock_bottom_left
    dock_bottom_right
    dock_top_center
    dock_bottom_center
    dock_left_center
    dock_right_center
    dock_center
    """.split()

    for dock in reversed(docks):
        docked = a.Anchored(ft.ElevatedButton(dock))
        setattr(docked, dock, root)
        root.controls.append(docked)


ft.app(main)
