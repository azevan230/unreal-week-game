import unreal


def register_menus():
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    arena_menu = main_menu.add_sub_menu("ArenaTools", "", "ArenaTools", "Arena Tools")

    entry = unreal.ToolMenuEntry(name="ImportImages", type=unreal.MultiBlockType.MENU_ENTRY)
    entry.set_label("Importer les arènes depuis les images")
    entry.set_string_command(
        unreal.ToolMenuStringCommandType.PYTHON,
        "",
        "import importlib, arena_from_image; importlib.reload(arena_from_image); arena_from_image.import_folder()",
    )
    arena_menu.add_menu_entry("Import", entry)
    menus.refresh_all_widgets()


register_menus()