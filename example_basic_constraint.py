import anchor as a
import flet as ft


def main(page: ft.Page):
    page.add(root := a.AnchorStack(expand=True))
    center = a.Anchored(ft.FilledButton("Center"), width=root.width/3, dock_center=root)
    on_the_side = a.Anchored(ft.FilledButton("On the side"), top=center.top, left=center.right)
    one_quarter_from_the_top = a.Anchored(ft.FilledButton("1/4 height"), center_x=root.center_x, center_y=root.height / 4)
    adjusted = a.Anchored(ft.FilledButton("Adjusted"), center_x=root.width * 3/4, center_y=20 + root.height / 4)
    max_position = a.Anchored(ft.FilledButton("Max position"), center_y=root.height * 3/4, center_x=max(300, root.center_x))
    reactive = a.Anchored(ft.FilledButton("Reactive"), center_y=(root.width >= 600) & root.width / 2 | 50)
    root.controls = [center, on_the_side, one_quarter_from_the_top, adjusted, max_position, reactive]


ft.app(main)
