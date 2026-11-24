import os
import warnings

import unreal
from png_reader import read_png

GRID_CLASS_PATH = "/Game/ArenaTools/PDA_ArenaGrid"


def grid_class():
    return unreal.EditorAssetLibrary.load_blueprint_class(GRID_CLASS_PATH)


def cell_enum():
    """Renvoie le type Python de l'enum Blueprint E_ArenaCell."""
    probe = unreal.new_object(grid_class())
    with warnings.catch_warnings():
        # La grille sonde est vide : GetCell avertit d'un accès hors tableau, c'est voulu.
        warnings.simplefilter("ignore", RuntimeWarning)
        return type(probe.call_method("GetCell", (0, 0)))


def build_palette():
    cell = cell_enum()
    return {
        (0, 0, 0): cell.WALL,
        (255, 255, 255): cell.EMPTY,
        (255, 0, 0): cell.SPAWN,
        (255, 255, 0): cell.POWER_UP,
        (0, 0, 255): cell.PORTAL,
        (0, 255, 0): cell.BOOST,
    }


def nearest_cell(rgb, palette):
    """Renvoie la case dont la couleur est la plus proche, et la distance (au carré) à cette couleur."""
    best_cell, best_distance = None, None
    for color, cell in palette.items():
        distance = sum((a - b) ** 2 for a, b in zip(color, rgb))
        if best_distance is None or distance < best_distance:
            best_cell, best_distance = cell, distance
    return best_cell, best_distance

ASSET_FOLDER = "/Game/ArenaTools/Arenas"
MAX_COLOR_DISTANCE = 60 ** 2


def image_to_grid(column, row, image_width, image_height):
    """Pixel (colonne, ligne) -> case (X, Y). Voir l'encadré « Le sens des Y »."""
    return image_height - 1 - row, column


def get_or_create_grid(name):
    path = f"{ASSET_FOLDER}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", grid_class())
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    return tools.create_asset(name, ASSET_FOLDER, None, factory)


def import_image(png_path):
    image_width, image_height, rows = read_png(png_path)
    palette = build_palette()

    # La grille fait image_height cases en X et image_width cases en Y (voir image_to_grid).
    grid_width, grid_height = image_height, image_width
    cells = [None] * (grid_width * grid_height)
    suspicious = []
    for row in range(image_height):
        for column in range(image_width):
            rgb = rows[row][column]
            cell, distance = nearest_cell(rgb, palette)
            if distance > MAX_COLOR_DISTANCE:
                suspicious.append((column, row, rgb))
            x, y = image_to_grid(column, row, image_width, image_height)
            cells[y * grid_width + x] = cell   # même index que SetCell : Y * Width + X

    name = "DA_Arena_" + os.path.splitext(os.path.basename(png_path))[0]
    grid = get_or_create_grid(name)
    with unreal.ScopedEditorTransaction(f"Importer {name}"):
        grid.modify()
        grid.set_editor_property("Width", grid_width)
        grid.set_editor_property("Height", grid_height)
        grid.set_editor_property("Cells", cells)
    unreal.EditorAssetLibrary.save_loaded_asset(grid)

    for column, row, rgb in suspicious[:10]:
        unreal.log_warning(f"{name} : pixel ({column}, {row}) de couleur {rgb} sans correspondance claire")
    unreal.log(f"{name} : {image_width} × {image_height} cases importées")
    return grid

def import_folder():
    folder = os.path.join(unreal.Paths.project_dir(), "ArenaImages")
    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".png"))
    with unreal.ScopedSlowTask(len(files), "Import des arènes") as task:
        task.make_dialog(True)
        for filename in files:
            if task.should_cancel():
                break
            task.enter_progress_frame(1, filename)
            try:
                import_image(os.path.join(folder, filename))
            except Exception as error:  # une image illisible ne doit pas arrêter les autres
                unreal.log_error(f"{filename} : {error}")