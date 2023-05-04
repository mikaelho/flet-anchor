import anchor as a
import flet as ft


def main(page: ft.Page):
    page.add(root := a.AnchorStack(expand=True))

    docks = """
    dock_top
    dock_left
    dock_bottom
    dock_right
    """.split()

    for dock in reversed(docks):
        docked = a.Anchored(ft.ElevatedButton(dock))
        setattr(docked, dock, root)
        root.controls.append(docked)


ft.app(main)
