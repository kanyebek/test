from db import main_db
import flet as ft

def main(page: ft.Page):
    page.title = "Список покупок"
    page.theme_mode = ft.ThemeMode.SYSTEM

    item_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)

    filter_type = "all"

    def load_items():
        item_list.controls.clear()
        items = main_db.get_items(filter_type)
        for item_id, item_label, purchased, in items:
            item_list.controls.append(create_item_row(item_id, item_label, purchased))
        page.update()

    def create_item_row(item_id, item_label, purchased):
        item_field = ft.TextField(value = item_label, expand=True, dense=True, read_only=True)
        item_checkbox = ft.Checkbox(value=bool(purchased), on_change=lambda e: toggle_item(item_id, e.control.value))

        return ft.Row([
            item_field,
            item_checkbox,
            ft.IconButton(ft.icons.DELETE, icon_color="red", on_click=lambda e:delete_item(item_id))
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def toggle_item(item_id, is_purchased):
        main_db.update_item(item_id, purchased = int(is_purchased) )
        load_items()

    def add_item(e):
        if item_input.value.strip():
            item_id = main_db.add_item(item_input.value)
            item_list.controls.append(create_item_row(item_id, item_input.value, 0))
            item_input.value = ""
            page.update()

    def delete_item(item_id):
        main_db.delete_item(item_id)
        load_items()

    def filter_items(filter_value):
        nonlocal filter_type

        filter_type = filter_value
        load_items()

    item_input = ft.TextField(label="Добавить товар", expand=True, on_submit=add_item)
    add_button = ft.IconButton(ft.icons.ADD, icon_color="green", on_click=add_item)

    filter_buttons = ft.Row([
        ft.ElevatedButton("Все", on_click=lambda e: filter_items("all")),
        ft.ElevatedButton("Куплено", on_click=lambda e: filter_items("purchased")),
        ft.ElevatedButton("Не куплено", on_click=lambda e: filter_items("unpurchased")),
    ], alignment=ft.MainAxisAlignment.CENTER)

    content = ft.Container(
        content=ft.Column([
            ft.Row([item_input, add_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            filter_buttons,
            item_list
        ], spacing=10),
        padding=20,
        alignment=ft.alignment.center,
    ) 

    background_image = ft.Image(
        src="/home/kanybek/Desktop/test/image.png",
        fit=ft.ImageFit.FILL,
        width=page.width,
        height=page.height,
    )  

    background = ft.Stack([background_image, content])

    def on_resize(e):
        background_image.width = page.window_width
        background_image.height = page.window_height
        page.update()

    page.add(background)   
    page.on_resize = on_resize

    load_items()

if __name__ == "__main__":
    main_db.init_db()
    ft.app(target=main)