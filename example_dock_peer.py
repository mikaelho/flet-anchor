import anchor as a
import flet as ft


def main(page: ft.Page):
    page.add(root := a.AnchorStack(expand=True))

    docks = """
    dock_above
    dock_below
    dock_right_of
    dock_left_of
    """.split()

    peer = a.Anchored(ft.FilledButton("Peer"), dock_center=root)
    root.controls.append(peer)

    for dock in reversed(docks):
        docked = a.Anchored(ft.ElevatedButton(dock))
        setattr(docked, dock, peer)
        root.controls.append(docked)


ft.app(main)
