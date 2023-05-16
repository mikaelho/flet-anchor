import anchor as a
import flet as ft


def main(page: ft.Page):
    page.add(root := a.AnchorStack(expand=True))

    # center = a.Anchored(ft.FilledButton("Center"), width=root.width/3, dock_center=root)
    # on_the_side = a.Anchored(ft.FilledButton("On the side"), top=center.top, left=center.right)
    # one_quarter_from_the_top = a.Anchored(ft.FilledButton("1/4 height"), center_x=root.center_x, center_y=root.height / 4)
    # adjusted = a.Anchored(ft.FilledButton("Adjusted"), center_x=root.width * 3/4, center_y=20 + root.height / 4)
    # max_position = a.Anchored(ft.FilledButton("Max position"), center_y=root.height * 3/4, center_x=max(root.center_x, 300))
    reactive = a.Anchored(
        ft.FilledButton("Condition"),
        center_x=(root.width >= 600) & root.width/2 | root.width/4,
    )



    # one_third = a.Anchored(
    #     ft.FilledButton("1/3"),
    #     dock_left=root,
    #     width=root.width.share(1, 3)
    # )
    # two_thirds = a.Anchored(
    #     ft.FilledButton("2/3"),
    #     dock_right=root,
    #     width=root.width.share(2, 3)
    # )

    # root.controls = [center, on_the_side, one_quarter_from_the_top, adjusted, max_position, reactive, one_third, two_thirds]
    root.controls = [reactive]


ft.app(main)
