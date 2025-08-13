import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import base64
import zlib, os
import mmap, starbound
import numpy as np
import json

class StarboundToTiledUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Starbound → Tiled Converter")
        self.root.geometry("600x400")

        # Path variables
        self.config_path = tk.StringVar()
        self.world_path = tk.StringVar()
        self.tileset_paths = []
        self.tileset_save_path = tk.StringVar()
        self.map_save_path = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        row = 0

        # starbound.config
        tk.Label(self.root, text="starbound.config path:").grid(row=row, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.config_path, width=50).grid(row=row, column=1)
        tk.Button(self.root, text="Browse", command=self.select_config).grid(row=row, column=2)
        row += 1

        # .world file
        tk.Label(self.root, text=".world file path:").grid(row=row, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.world_path, width=50).grid(row=row, column=1)
        tk.Button(self.root, text="Browse", command=self.select_world).grid(row=row, column=2)
        row += 1

        # Multiple tilesets to load
        tk.Label(self.root, text="Tileset files to load:").grid(row=row, column=0, sticky="w")
        tk.Button(self.root, text="Add Tilesets", command=self.add_tilesets).grid(row=row, column=1, sticky="w")
        row += 1

        # Tileset list table
        self.tileset_table = ttk.Treeview(self.root, columns=("path",), show="headings", height=5)
        self.tileset_table.heading("path", text="Tileset Path")
        self.tileset_table.grid(row=row, column=0, columnspan=3, sticky="nsew")
        row += 1

        # Output tileset folder (single folder)
        tk.Label(self.root, text="Output tileset folder:").grid(row=row, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.tileset_save_path, width=50).grid(row=row, column=1)
        tk.Button(self.root, text="Browse", command=self.select_tileset_save).grid(row=row, column=2)
        row += 1

        # Output Tiled map folder
        tk.Label(self.root, text="Output Tiled map folder:").grid(row=row, column=0, sticky="w")
        tk.Entry(self.root, textvariable=self.map_save_path, width=50).grid(row=row, column=1)
        tk.Button(self.root, text="Browse", command=self.select_map_save).grid(row=row, column=2)
        row += 1

        # Progress bar
        tk.Label(self.root, text="Progress:").grid(row=row, column=0, sticky="w")
        self.progress_bar = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress_bar.grid(row=row, column=1, sticky="ew", padx=(0, 10))
        row += 1

        # Status label
        self.status_label = tk.Label(self.root, text="Ready", fg="blue")
        self.status_label.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        # Run button
        tk.Button(self.root, text="Run Conversion", command=self.run_conversion, bg="#4CAF50", fg="white").grid(row=row, column=0, columnspan=3, pady=10)

    def load_tileset(self, filepath, name):
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        tileprops = data.get("tileproperties", {})
        material_to_id = {}

        for tile_id_str, props in tileprops.items():
            # Convert key
            tile_id = np.uint32(int(tile_id_str))

            # liquid format
            if "liquid" in props:
                liquid = props.get("liquid")
                source_raw = props.get("source", "false")
                source = source_raw.lower() == "true"

                key = (liquid, source)
                material_to_id[key] = tile_id
                continue

            # material format
            material_name = props.get("material")
            if not material_name:
                continue

            color_variant_str = props.get("colorVariant")
            try:
                color_variant = int(color_variant_str) if color_variant_str is not None else None
            except ValueError:
                continue

            mod = props.get("mod")
            mod = mod if mod and mod.strip() != "" else None

            key = (material_name, color_variant, mod)
            material_to_id[key] = tile_id

        return {
            "name": name,
            "material_map": material_to_id
        }

    def select_config(self):
        path = filedialog.askopenfilename(title="Select starbound.config", filetypes=[("Starbound Config File", "*.config")])
        if path:
            self.config_path.set(path)

    def select_world(self):
        path = filedialog.askopenfilename(title="Select .world file", filetypes=[("Starbound World File", "*.world;*.shipworld")])
        if path:
            self.world_path.set(path)

    def add_tilesets(self):
        paths = filedialog.askopenfilenames(title="Select tilesets", filetypes=[("Starbound Tilesets File", "*.json")])
        for p in paths:
            if p not in self.tileset_paths:
                self.tileset_paths.append(p)
                self.tileset_table.insert("", tk.END, values=(p,))

    def select_tileset_save(self):
        path = filedialog.askdirectory(title="Select output generated tileset folder")
        if path:
            self.tileset_save_path.set(path)

    def select_map_save(self):
        path = filedialog.askdirectory(title="Select output Tiled dungeon map folder")
        if path:
            self.map_save_path.set(path)

    def run_conversion(self):
        if not self.config_path.get() or not self.world_path.get() or not self.tileset_paths \
           or not self.tileset_save_path.get() or not self.map_save_path.get():
            messagebox.showerror("Error", "Please fill in all paths.")
            return

        # Start progress indication
        self.progress_bar.start()
        self.status_label.config(text="Starting conversion...", fg="orange")
        self.root.update()

        # Actual conversion logic goes here
        self.convert_world_to_tiled()

        # Stop progress indication
        self.progress_bar.stop()
        self.status_label.config(text="Ready", fg="blue")

    def material_names_to_tuples_with_color_variant(self, material_array, all_tilesets, missing_tile_map):
        height = len(material_array)
        width = len(material_array[0]) if height > 0 else 0
        result = np.empty((height, width), dtype=object)
        already_reported = set()

        current_missing_local_id = len(missing_tile_map)  # Start from 0 or continue from previous

        for y in range(height):
            for x in range(width):
                entry = material_array[y][x]

                if (
                    not entry or
                    (isinstance(entry, str) and entry.strip() == "") or
                    (isinstance(entry, (list, tuple)) and len(entry) > 0 and str(entry[0]).strip() == "")
                ):
                    result[y, x] = ("empty", np.uint32(0))
                    continue

                if isinstance(entry, (list, tuple)):
                    material = entry[0] if len(entry) > 0 else None
                    color_variant = entry[1] if len(entry) > 1 else 0
                    mod = entry[2] if len(entry) > 2 else None
                else:
                    material = entry
                    color_variant = 0
                    mod = None

                if not isinstance(color_variant, int) or not (0 <= color_variant <= 8):
                    result[y, x] = ("empty", np.uint32(0))
                    continue

                color_variant_key = None if color_variant == 0 else color_variant
                mod = None if not mod or str(mod).strip() == "" else mod

                found = False

                for tileset in all_tilesets:
                    material_map = tileset.get("material_map", {})

                    try_keys = [
                        (material, color_variant_key, mod),
                        (material, None, mod) if color_variant_key is not None else None,
                        (material, color_variant_key, None) if mod is not None else None,
                        (material, None, None) if color_variant_key is None and mod is None else None,
                    ]

                    for key in try_keys:
                        if key and key in material_map:
                            if key[1] != color_variant_key and color_variant_key is not None:
                                continue
                            if key[2] != mod and mod is not None:
                                continue

                            # Found in existing tileset
                            result[y, x] = (tileset["name"], np.uint32(material_map[key]))
                            found = True
                            break
                    if found:
                        break

                if not found:
                    report_key = (material, color_variant, mod)
                    if report_key not in already_reported:
                        already_reported.add(report_key)

                    if report_key not in missing_tile_map:
                        if color_variant == 0:
                            print(f"Material '{material}'"
                                + (f" and mod '{mod}'" if mod else "")
                                + f" not found in any tileset. Assigning local ID '{current_missing_local_id}'")
                        else:
                            print(f"Material '{material}' with colorVariant '{color_variant}'"
                                + (f" and mod '{mod}'" if mod else "")
                                + f" not found in any tileset. Assigning local ID '{current_missing_local_id}'")
                        missing_tile_map[report_key] = current_missing_local_id
                        current_missing_local_id += 1

                    local_id = missing_tile_map[report_key]
                    result[y, x] = ("generated_tiles", np.uint32(local_id))

        return result

    def liquid_names_to_tuples(self, liquid_array, all_tilesets, missing_tile_map):
        def is_truthy(val):
            # Handle various true values
            if isinstance(val, bool):
                return val
            if isinstance(val, int):
                return val == 1
            if isinstance(val, str):
                return val.strip().lower() in ("true", "1", "yes")
            return False

        height = len(liquid_array)
        width = len(liquid_array[0]) if height > 0 else 0
        result = np.empty((height, width), dtype=object)
        already_reported = set()

        current_missing_local_id = len(missing_tile_map)

        for y in range(height):
            for x in range(width):
                entry = liquid_array[y][x]

                # Handle empty cells
                if (
                    not entry or
                    (isinstance(entry, str) and entry.strip() == "") or
                    (isinstance(entry, (list, tuple)) and len(entry) > 0 and str(entry[0]).strip() == "")
                ):
                    result[y, x] = ("empty", np.uint32(0))
                    continue

                # Parse
                if isinstance(entry, (list, tuple)):
                    liquid = entry[0] if len(entry) > 0 else None
                    raw_source = entry[1] if len(entry) > 1 else False
                else:
                    liquid = entry
                    raw_source = False

                # Clean up source value (1, "true", "1", True etc. → True)
                source = is_truthy(raw_source)

                # Find in tileset
                found = False
                for tileset in all_tilesets:
                    material_map = tileset.get("material_map", {})
                    key = (liquid, source)
                    if key in material_map:
                        result[y, x] = (tileset["name"], np.uint32(material_map[key]))
                        found = True
                        break

                if not found:
                    report_key = (liquid, source)
                    if report_key not in already_reported:
                        print(f"Liquid '{liquid}' with source={source} not found. Assigning local ID '{current_missing_local_id}'")
                        already_reported.add(report_key)

                    if report_key not in missing_tile_map:
                        missing_tile_map[report_key] = current_missing_local_id
                        current_missing_local_id += 1

                    local_id = missing_tile_map[report_key]
                    result[y, x] = ("generated_tiles", np.uint32(local_id))

        return result

    def safe_get_entities(self, world, rx, ry):
        try:
            return world.get_entities(rx, ry)
        except KeyError:
            return []

    def extract_entities(self, entities, world_height, object_nodes, object_input_nodes, object_output_nodes):
        monster_list = []
        npc_list = []
        object_list = []

        for entity in entities:
            if getattr(entity, "name", None) == "MonsterEntity":
                data = entity.data
                persistent = data.get("monsterVariant", {}).get("uniqueParameters", {}).get("persistent", False)
                if persistent:
                    monster_variant = data.get("monsterVariant", {})
                    position = data.get("movementState", {}).get("position", [0, 0])
                    obj = {
#                        "level": data.get("monsterLevel"),
                        "position": [int(round(position[0])), int(round(position[1]))],
                        "seed": monster_variant.get("seed"),
                        "type": monster_variant.get("type"),
                        "uniqueParameters": monster_variant.get("uniqueParameters", {})
                    }
#                    print(monster_variant.get("uniqueParameters", {}))
                    monster_list.append(obj)
            elif getattr(entity, "name", None) == "NpcEntity":
                data = entity.data.get("npcVariant", {})
                position = entity.data.get("movementController", {}).get("position", [0, 0])
                obj = {
#                        "level": data.get("level"),
                    "overrides": data.get("overrides", {}),
                    "position": [int(round(position[0])), int(round(position[1]))],
                    "seed": data.get("seed"),
                    "species": data.get("species"),
                    "typeName": data.get("typeName")
                }
#                print(data.get("overrides", {}))
                npc_list.append(obj)
            elif getattr(entity, "name", None) == "ObjectEntity":
                data = entity.data
                tile_position = [data.get("tilePosition")[0], world_height - data.get("tilePosition")[1] - 1]
                object_name = data.get("name")
                obj = {
                    "name": object_name,
                    "tilePosition": tile_position,
                    "orientationIndex": data.get("orientationIndex"),
                    "parameters": data.get("parameters", {}),
                    "inputWireNodes": data.get("inputWireNodes", []),
                    "outputWireNodes": data.get("outputWireNodes", [])
                }

                input_nodes = data.get("inputWireNodes", [])
                if isinstance(input_nodes, list) and input_nodes:
                    for i, pos in enumerate(input_nodes):
                        connections = pos.get("connections", []) if isinstance(pos, dict) else []
                        if connections:  # Only when connections list is not empty
                            offset = object_nodes[object_name][f"i_{i}"]
                            object_input_nodes[f"{tile_position[0]}_{tile_position[1]}_i_{i}"] = [tile_position[0] + offset[0], tile_position[1] - offset[1]]

                output_nodes = data.get("outputWireNodes", [])
                if isinstance(output_nodes, list) and output_nodes:
                    for i, pos in enumerate(output_nodes):
                        connections = pos.get("connections", []) if isinstance(pos, dict) else []
                        if connections:  # Only when connections list is not empty
                            offset = object_nodes[object_name][f"o_{i}"]
                            for conn in connections:
                                coord = [conn[0][0], world_height - conn[0][1] - 1]
                                key = f"{coord[0]}_{coord[1]}_i_{conn[1]}"
                                object_output_nodes.setdefault(f"{tile_position[0] + offset[0]}_{tile_position[1] - offset[1]}_o_{i}", []).append(key)

                object_list.append(obj)

        return monster_list, npc_list, object_list

    def named_to_gid(self, tileset_name, local_id, tilesets):
        if tileset_name == "empty":
            return 0
        for ts in tilesets:
            if ts["name"] == tileset_name:
                return ts["firstgid"] + local_id
        raise ValueError(f"Unknown tileset name: {tileset_name}")

    def encode_map(self, named_tile_map, tilesets):
        # named_tile_map: 2D array of (tileset_name, local_id)
        height, width = named_tile_map.shape
        gids = np.zeros((height * width,), dtype=np.uint32)
        for i in range(height):
            for j in range(width):
                tileset_name, local_id = named_tile_map[i, j]
                gids[i * width + j] = self.named_to_gid(tileset_name, local_id, tilesets)
        # Compression + base64 encoding
        raw_bytes = gids.tobytes()
        compressed = zlib.compress(raw_bytes)
        encoded = base64.b64encode(compressed).decode('utf-8')
        return encoded

    def generate_tilesets(self, tileset_paths, relative_to="tiled/packed/dungeons/converted"):
        tilesets = []
        current_gid = 1
        for path, name in tileset_paths:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            tilecount = data.get("tilecount")
            if tilecount is None:
                raise ValueError(f"tilecount not found in {path}")
            relative_path = os.path.relpath(path, start=relative_to).replace("\\", "/")
            tilesets.append({
                "firstgid": current_gid,
                "name": name,
                "source": relative_path
            })
            current_gid += tilecount
        return tilesets

    def generate_missing_tileset_from_map(self, missing_tile_map, tileset_name="generated_tiles"):
        tileset = {
            "name": tileset_name,
            "tilewidth": 8,
            "tileheight": 8,
            "spacing": 0,
            "margin": 0,
            "tilecount": len(missing_tile_map),
            "tiles": {},
            "tileproperties": {}
        }

        for key, local_id in missing_tile_map.items():
            tileset["tiles"][str(local_id)] = {
                "image": "./../../../../tiled/packed/../packed/invalid.png"
            }

            # Branch processing: material or liquid?
            if len(key) == 3:
                # material tileset
                material, color, mod = key
                prop = {"material": material}
                if color is not None and color != 0:
                    prop["colorVariant"] = str(color)
                if mod:
                    prop["mod"] = str(mod)
            elif len(key) == 2:
                # liquid tileset
                liquid, source = key
                prop = {"liquid": liquid}
                if source:
                    prop["source"] = "true"  # Only save when source is True
            else:
                raise ValueError(f"Unrecognized key format in missing_tile_map: {key}")

            tileset["tileproperties"][str(local_id)] = prop

        return tileset

    def build_polylines(self, object_output_nodes, object_input_nodes, starting_id=1000):
        polylines = []
        current_id = starting_id

        for out_key, in_keys in object_output_nodes.items():
            # Extract starting coordinates from key
            start_part = out_key.split('_o_')[0]
            start_x, start_y = map(int, start_part.split('_'))

            for in_key in in_keys:
                if in_key not in object_input_nodes:
                    continue  # Skip if no match

                # Get destination coordinates directly from value
                end_x, end_y = object_input_nodes[in_key]

                # Calculate change amount
                x_diff = end_x - start_x
                y_diff = end_y - start_y

                # Coordinate representation (x, y coordinates are tile units → multiply by 8 for px conversion)
                polyline_obj = {
                    "height": 0,
                    "id": current_id,
                    "name": "",
                    "polyline": [
                        {"x": 0, "y": 0},
                        {"x": x_diff * 8, "y": y_diff * 8}
                    ],
                    "rotation": 0,
                    "type": "",
                    "visible": True,
                    "width": 0,
                    "x": start_x * 8,
                    "y": start_y * 8
                }

                polylines.append(polyline_obj)
                current_id += 1

        return polylines, current_id

    def create_tiled_map_json(self, world_name, tileset_paths, fbase64_data, bbase64_data, lbase64_data, width, height, tilesets, monster_entities=None, npc_entities=None, object_entities=None, object_output_nodes=None, object_input_nodes=None):
        # Create .json file path
        filename = os.path.splitext(os.path.basename(world_name))[0] + ".json"
        json_path = os.path.join(self.map_save_path.get(), filename)

        # Basic layer structure
        def make_layer(id_, name, opacity, base64_data=None):
            layer = {
                "id": id_,
                "name": name,
                "opacity": opacity,
                "type": "tilelayer" if base64_data else "objectgroup",
                "visible": True,
                "x": 0,
                "y": 0,
                "draworder": "topdown" if not base64_data else None
            }
            if base64_data:
                layer.update({
                    "compression": "zlib",
                    "encoding": "base64",
                    "data": base64_data,
                    "width": width,
                    "height": height
                })
            else:
                layer["objects"] = []
            return layer

        # Complete map data structure
        map_data = {
            "backgroundcolor": "#000000",
            "compressionlevel": 0,
            "editorsettings": {
                "export": {
                    "target": "."
                }
            },
            "height": height,
            "width": width,
            "tilewidth": 8,
            "tileheight": 8,
            "infinite": False,
            "layers": [
                make_layer(1, "back", 0.5, bbase64_data),
                make_layer(2, "front", 1, lbase64_data),
                make_layer(3, "front", 1, fbase64_data),
                make_layer(4, "mods", 1),
                make_layer(5, "objects", 1),
                make_layer(6, "wiring", 1),
                make_layer(7, "monsters", 1),
                make_layer(8, "npcs", 1),
                make_layer(9, "anchors etc", 1),
                make_layer(10, "items", 1),
            ],
            "nextlayerid": 11,
            "nextobjectid": 1,
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "tiledversion": "1.3.1",
            "type": "map",
            "version": 1.2,
            "tilesets": tilesets
        }

        current_id = 1

        # Process object_entities
        if object_entities:
            object_layer = map_data["layers"][4]  # "objects"
            for obj in object_entities:
                tile_x, tile_y = obj["tilePosition"]
                direction = "right" if obj["orientationIndex"] == 1 else "left"
                param_data = obj.get("parameters", {})

                properties = [
                    {"name": "object", "type": "string", "value": obj["name"]},
                    {"name": "tilesetDirection", "type": "string", "value": direction}
                ]
                if param_data:
                    properties.append({
                        "name": "parameters",
                        "type": "string",
                        "value": json.dumps(param_data, ensure_ascii=False)
                    })

                object_layer["objects"].append({
                    "height": 8,
                    "width": 8,
                    "id": current_id,
                    "name": "",
                    "type": "",
                    "rotation": 0,
                    "visible": True,
                    "x": tile_x * 8,
                    "y": tile_y * 8,
                    "properties": properties
                })

                current_id += 1

        # Process wiring
        if object_output_nodes and object_input_nodes:
            result, next_id = self.build_polylines(object_output_nodes, object_input_nodes, current_id)
            if result:
                wire_layer = map_data["layers"][5]  # "wires"
                wire_layer["color"] = "#ffff00"
                wire_layer["objects"] = result
        else:
            wire_layer = map_data["layers"][5]  # "wires"
            wire_layer["color"] = "#ffff00"
            wire_layer["objects"] = []
            next_id = current_id

        current_id = next_id

        # Process monster_entities
        if monster_entities:
            monster_layer = map_data["layers"][6]  # "monsters"
            monster_layer["color"] = "#ff0000"
            for monster in monster_entities:
                x, y = monster.get("position", [0, 0])
                seed = monster.get("seed")
                if isinstance(seed, int) and seed < 0:
                    seed = seed + (1 << 64)  # uint64 correction
                param_data = monster.get("uniqueParameters", {})

                properties = [
                    {"name": "seed", "type": "string", "value": str(seed)},
                    {"name": "monster", "type": "string", "value": monster.get("type", "")}
#                    {"name": "level", "type": "string", "value": str(monster.get("level", ""))}
                ]
                if param_data:
                    properties.append({
                        "name": "parameters",
                        "type": "string",
                        "value": json.dumps(param_data, ensure_ascii=False)
                    })

                monster_layer["objects"].append({
                    "height": 8,
                    "width": 8,
                    "id": current_id,
                    "name": "",
                    "type": "",
                    "rotation": 0,
                    "visible": True,
                    "x": x * 8,
                    "y": (height - y - 1) * 8,
                    "properties": properties
                })

                current_id += 1

        # Process npc_entities
        if npc_entities:
            npc_layer = map_data["layers"][7]  # "npcs"
            npc_layer["color"] = "#00ff00"
            for npc in npc_entities:
                x, y = npc.get("position", [0, 0])
                seed = npc.get("seed")
                if isinstance(seed, int) and seed < 0:
                    seed = seed + (1 << 64)  # uint64 correction
                param_data = npc.get("overrides", {})

                properties = [
                    {"name": "seed", "type": "string", "value": str(seed)},
                    {"name": "typeName", "type": "string", "value": npc.get("typeName", "")},
                    {"name": "npc", "type": "string", "value": npc.get("species", "")}
#                    {"name": "level", "type": "string", "value": str(npc.get("level", ""))}
                ]
                if param_data:
                    properties.append({
                        "name": "parameters",
                        "type": "string",
                        "value": json.dumps(param_data, ensure_ascii=False)
                    })
                    
                npc_layer["objects"].append({
                    "height": 8,
                    "width": 8,
                    "id": current_id,
                    "name": "",
                    "type": "",
                    "rotation": 0,
                    "visible": True,
                    "x": x * 8,
                    "y": (height - y - 1) * 8,
                    "properties": properties
                })

                current_id += 1

        # Update final object ID
        map_data["nextobjectid"] = current_id

        # Save JSON file
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(map_data, f, indent=4)

        print(f"Converted Tiled Map creation completed: {json_path}")

    def convert_tile_array_to_material_input(self, tile_arr, material_id_to_name, mod_id_to_name):
        height, width = tile_arr.shape
        result = []

        # Add set to prevent duplicates
        unknown_material_ids = set()
        unknown_mod_ids = set()

        for y in range(height):
            row = []
            for x in range(width):
                material_id, variant, mod_id = tile_arr[y, x]

                # Handle negative values using bit mask
                material_id &= 0xFFFF  # Same as subtracting from 65536 (uint16)
                mod_id &= 0xFFFF       # Same as subtracting from 65536 (uint16)
                variant &= 0xFF        # Same as subtracting from 256 (uint8)

                material_name = material_id_to_name.get(str(material_id), "")
                mod_name = mod_id_to_name.get(str(mod_id), "")

                if material_name == "empty":
                    material_name = ""
                elif material_name == "":
                    if material_id not in unknown_material_ids:
                        print(f"Failed to convert material ID '{material_id}' to material name.")
                        unknown_material_ids.add(material_id)

                if mod_name == "empty":
                    mod_name = None
                elif mod_name == "":
                    if mod_id not in unknown_mod_ids:
                        print(f"Failed to convert material mod ID '{mod_id}' to material mod name.")
                        unknown_mod_ids.add(mod_id)

                row.append([material_name, variant, mod_name])
            result.append(row)
        return result

    def convert_tile_array_to_liquid_input(self, tile_arr, liquid_id_to_name):
        height, width = tile_arr.shape
        result = []

        # Add set to prevent duplicates
        unknown_liquid_ids = set()

        for y in range(height):
            row = []
            for x in range(width):
                liquid_id, infinite = tile_arr[y, x]

                # Handle negative values using bit mask
                liquid_id &= 0xFF  # Same as subtracting from 256 (uint16)

                liquid_name = liquid_id_to_name.get(str(liquid_id), "")

                if liquid_name == "empty":
                    liquid_name = ""
                elif liquid_name == "":
                    if liquid_id not in unknown_liquid_ids:
                        print(f"Failed to convert liquid ID '{liquid_id}' to liquid name.")
                        unknown_liquid_ids.add(liquid_id)

                row.append([liquid_name, infinite])
            result.append(row)
        return result

    def convert_world_to_tiled(self):
        try:
            # Load tiledConfig.json
            self.status_label.config(text="Loading configuration...", fg="orange")
            self.root.update()
            
            with open(self.config_path.get(), encoding="utf-8") as f:
                tiledConfig = json.load(f)['worldToTiled']
                material_id_to_name = tiledConfig['material']
                mod_id_to_name = tiledConfig['mod']
                liquid_id_to_name = tiledConfig['liquid']
                object_nodes = tiledConfig['wire']

            # World file to convert
            world_name = self.world_path.get()
            
            # Tileset list (using paths selected in UI)
            tileset_paths = [(path, os.path.splitext(os.path.basename(path))[0]) for path in self.tileset_paths]

            self.status_label.config(text="Reading world file...", fg="orange")
            self.root.update()

            with open(world_name, 'rb') as fh:
                mm = mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ)

                world = starbound.World(mm)
                world.read_metadata()

                # Initialize world tile array (width x height)
                world_width, world_height = world.width, world.height

                tile_map = np.empty((world_height, world_width), dtype=object)

                foreground = np.empty((world_height, world_width), dtype=object)
                liquid = np.empty((world_height, world_width), dtype=object)
                background = np.empty((world_height, world_width), dtype=object)

                # Extract chunk (region) coordinates
                chunk_list = list(world.get_all_regions_with_tiles())  # Convert generator to list

                # entity_list: list to accumulate results
                monster_list = []
                object_list = []
                npc_list = []

                # Storage space for object input/output points
                object_output_nodes = {}
                object_input_nodes = {}

                total_chunks = len(chunk_list)
                for i, (rx, ry) in enumerate(chunk_list):
                    if i % 10 == 0:  # Update status every 10 chunks
                        self.status_label.config(text=f"Processing chunks: {i}/{total_chunks}...", fg="orange")
                        self.root.update()
                    
                    tiles = world.get_tiles(rx, ry)  # This is a 32x32 Tile list
                    entities = self.safe_get_entities(world, rx, ry)  # Entities in this region

                    # Calculate world position coordinates
                    start_x = rx * 32
                    start_y = ry * 32

                    # Prevent tilemap range overflow (some regions may be cut off at the end)
                    for local_y in range(32):
                        for local_x in range(32):
                            wx, wy = start_x + local_x, start_y + local_y
                            if wx < world_width and wy < world_height:
                                idx = local_y * 32 + local_x  # flat list index
                                tile_map[wy, wx] = tiles[idx]

                    # Extract and accumulate entities
                    monsters, npcs, objects = self.extract_entities(entities, world_height, object_nodes, object_input_nodes, object_output_nodes)
                    monster_list.extend(monsters)
                    npc_list.extend(npcs)
                    object_list.extend(objects)

                self.status_label.config(text="Processing tile data...", fg="orange")
                self.root.update()
                
                for y in range(world_height):
                    for x in range(world_width):
                        tile = tile_map[y, x]
                        if tile is not None:
                            foreground[y, x] = [tile.foreground_material, tile.foreground_variant, tile.foreground_mod]
                            liquid[y, x] = [tile.liquid, tile.liquid_infinite]
                            background[y, x] = [tile.background_material, tile.background_variant, tile.background_mod]
                        else:
                            # Default values when tile is None (e.g., [0, 0, 0])
                            foreground[y, x] = [0, 0, 0]
                            liquid[y, x] = [0, 0]
                            background[y, x] = [0, 0, 0]

                self.status_label.config(text="Converting tile arrays...", fg="orange")
                self.root.update()
                
                foreground_material_input = self.convert_tile_array_to_material_input(foreground, material_id_to_name, mod_id_to_name)
                background_material_input = self.convert_tile_array_to_material_input(background, material_id_to_name, mod_id_to_name)
                liquid_input = self.convert_tile_array_to_liquid_input(liquid, liquid_id_to_name)

                self.status_label.config(text="Generating tilesets...", fg="orange")
                self.root.update()
                
                tilesets = self.generate_tilesets(tileset_paths)
                all_tilesets = [self.load_tileset(path, name) for path, name in tileset_paths]

                height = len(foreground_material_input)
                width = len(foreground_material_input[0]) if height > 0 else 0

                # Initialize missing tile map
                missing_tile_map = {}

                # Call conversion methods
                self.status_label.config(text="Processing material names...", fg="orange")
                self.root.update()
                
                front_result = self.material_names_to_tuples_with_color_variant(foreground_material_input, all_tilesets, missing_tile_map)
                back_result = self.material_names_to_tuples_with_color_variant(background_material_input, all_tilesets, missing_tile_map)
                liquid_result = self.liquid_names_to_tuples(liquid_input, all_tilesets, missing_tile_map)

                self.status_label.config(text="Generating missing tileset...", fg="orange")
                self.root.update()
                
                generated_tileset = self.generate_missing_tileset_from_map(missing_tile_map, "generated_tiles")

                # generated_tiles folder path
                filename = os.path.splitext(os.path.basename(world_name))[0] + ".json"
                generated_path = os.path.join(self.tileset_save_path.get(), filename)

                with open(generated_path, "w", encoding="utf-8") as f:
                    json.dump(generated_tileset, f, indent=4, ensure_ascii=False)

                print(f"Generated Tileset creation completed: {generated_path}")
                tileset_paths.append((generated_path, "generated_tiles"))

                # Regenerate tilesets
                tilesets = self.generate_tilesets(tileset_paths, relative_to=os.path.dirname(world_name))

                self.status_label.config(text="Encoding map data...", fg="orange")
                self.root.update()
                
                front_result_flipped = np.flipud(front_result)
                back_result_flipped = np.flipud(back_result)
                liquid_result_flipped = np.flipud(liquid_result)

                # Compression + base64 encoding
                front_base64_data = self.encode_map(front_result_flipped, tilesets)
                back_base64_data = self.encode_map(back_result_flipped, tilesets)
                liquid_base64_data = self.encode_map(liquid_result_flipped, tilesets)

                self.status_label.config(text="Creating Tiled map JSON...", fg="orange")
                self.root.update()
                
                self.create_tiled_map_json(
                    world_name, tileset_paths,
                    front_base64_data, back_base64_data, liquid_base64_data,
                    world_width, world_height,
                    tilesets,
                    monster_list, npc_list, object_list,
                    object_output_nodes, object_input_nodes
                )

                self.status_label.config(text="Conversion completed successfully!", fg="green")
                self.root.update()
                
                messagebox.showinfo("Completed", "Conversion has been completed.")
                
        except Exception as e:
            self.status_label.config(text="Conversion failed!", fg="red")
            self.root.update()
            messagebox.showerror("Error", f"Conversion failed: {str(e)}")
            print(f"Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StarboundToTiledUI(root)
    root.mainloop()