import anchor as a
import flet as ft


def main(page: ft.Page):
    page.padding = 0
    page.add(root := a.AnchorStack(expand=True))

    app_bar = a.Anchored(ft.Container(bgcolor=ft.colors.RED_100), height=50)
    menu_panel = a.Anchored(ft.Container(bgcolor=ft.colors.BLUE_100), width=200)
    content_area = a.Anchored(ft.Container(bgcolor=ft.colors.GREEN_100))

    app_bar.dock_top = root
    content_area.top = app_bar.bottom
    content_area.dock_bottom_right = root

    with root.width >= 600:
        menu_panel.dock_bottom_left = root
        menu_panel.top = app_bar.bottom
        content_area.left = menu_panel.right

    with root.width < 600:
        menu_panel.dock_top_bottom = root
        menu_panel.right = root.left
        content_area.left = root.left

    root.controls = [app_bar, menu_panel, content_area]


ft.app(main)
