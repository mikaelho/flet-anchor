import anchor as a
import flet as ft


def main(page: ft.Page):
    page.add(root := a.AnchorStack(expand=True))
    center = a.Anchored(ft.FilledButton("Center"), dock_center=root)
    on_the_side = a.Anchored(ft.FilledButton("On the side"), top=center.top, left=center.right)
    one_quarter_from_the_bottom = a.Anchored(ft.FilledButton("1/4 from the bottom"), center_x=root.center_x, center_y=root.height*3/4)
    root.controls = [center, on_the_side, one_quarter_from_the_bottom]


ft.app(main)
