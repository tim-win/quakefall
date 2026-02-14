#!/usr/bin/env python3
"""
Generate a simple city map for QuakeFall.
Output: a Q3 .map file with a city block layout.

Layout concept:
- 4x4 grid of city blocks separated by streets
- Buildings of varying heights on each block
- Wide main streets (titan-friendly) + narrow alleys (pilot-friendly)
- Open plaza in the center
- Spawn points and weapon pickups scattered around

Coordinate system:
- Q3 unit ~= 1 inch. Player is 56 units tall, 30 units wide.
- We'll work at a scale where:
  - Street width: 384 units (wide, ~3 titans side by side)
  - Alley width: 128 units (tight, pilot-only)
  - Building footprint: 512-1024 units
  - Building height: 256-1024 units
  - Total map: ~8000x8000 units
"""

import random
import math

random.seed(42)  # Reproducible layout

# Textures from the demo pak
TEX_FLOOR = "base_floor/diamond2c"
TEX_WALL = "gothic_block/blocks17"
TEX_WALL2 = "gothic_block/blocks15"
TEX_WALL3 = "base_wall/metalfloor_wall_15"
TEX_ROOF = "gothic_block/blocks18b"
TEX_SKY = "skies/xtoxicsky_q3ctf3"
TEX_CAULK = "common/caulk"
TEX_LIGHT = "base_light/lt2_8000"  # Light-emitting texture

# Map dimensions
GRID_SIZE = 4          # 4x4 blocks
BLOCK_SIZE = 1024      # Each block footprint
STREET_WIDTH = 384     # Main streets between blocks
MAP_FLOOR = 0          # Ground level
SKYBOX_HEIGHT = 2048   # Ceiling of the sky
WALL_THICKNESS = 16    # Brush thickness for walls
FLOOR_THICKNESS = 64   # Ground slab thickness

# Calculate total map size
TOTAL_SIZE = GRID_SIZE * BLOCK_SIZE + (GRID_SIZE + 1) * STREET_WIDTH
MAP_MIN = -TOTAL_SIZE // 2
MAP_MAX = TOTAL_SIZE // 2


def brush_box(x1, y1, z1, x2, y2, z2, textures=None):
    """Generate a Q3 brush (axis-aligned box) from min/max coords.

    textures: dict with keys 'top','bottom','sides' or a single string for all faces.
    Default: caulk everything except what's visible.
    """
    if textures is None:
        textures = {'all': TEX_WALL}
    elif isinstance(textures, str):
        textures = {'all': textures}

    def tex(face):
        return textures.get(face, textures.get('all', TEX_CAULK))

    # Q3 brush: 6 planes defined by 3 points each + texture info
    # Winding order derived from decompiled q3dm1 reference map.
    # q3map2 PlaneFromPoints uses cross(p2-p0, p1-p0) — normals point outward.

    def p(x, y, z):
        return f"( {x:.3f} {y:.3f} {z:.3f} )"

    def face(p0, p1, p2, texture):
        return f"\t\t{p(*p0)} {p(*p1)} {p(*p2)} {texture} 0.00000000 0.00000000 0.00000000 0.50000000 0.50000000 0 0 0"

    lines = ["\t{"]
    # Left face   (x = x1, normal -X): (x1,y1,z2) (x1,y1,z1) (x1,y2,z1)
    lines.append(face((x1,y1,z2), (x1,y1,z1), (x1,y2,z1), tex('sides')))
    # Right face  (x = x2, normal +X): (x2,y2,z2) (x2,y2,z1) (x2,y1,z1)
    lines.append(face((x2,y2,z2), (x2,y2,z1), (x2,y1,z1), tex('sides')))
    # Back face   (y = y1, normal -Y): (x2,y1,z1) (x1,y1,z1) (x1,y1,z2)
    lines.append(face((x2,y1,z1), (x1,y1,z1), (x1,y1,z2), tex('sides')))
    # Front face  (y = y2, normal +Y): (x2,y2,z2) (x1,y2,z2) (x1,y2,z1)
    lines.append(face((x2,y2,z2), (x1,y2,z2), (x1,y2,z1), tex('sides')))
    # Bottom face (z = z1, normal -Z): (x1,y2,z1) (x1,y1,z1) (x2,y1,z1)
    lines.append(face((x1,y2,z1), (x1,y1,z1), (x2,y1,z1), tex('bottom')))
    # Top face    (z = z2, normal +Z): (x2,y2,z2) (x2,y1,z2) (x1,y1,z2)
    lines.append(face((x2,y2,z2), (x2,y1,z2), (x1,y1,z2), tex('top')))
    lines.append("\t}")
    return "\n".join(lines)


def entity(classname, origin=None, extra_keys=None, brushes=None):
    """Generate a Q3 entity."""
    lines = ["{"]
    lines.append(f'\t"classname" "{classname}"')
    if origin:
        lines.append(f'\t"origin" "{origin[0]} {origin[1]} {origin[2]}"')
    if extra_keys:
        for k, v in extra_keys.items():
            lines.append(f'\t"{k}" "{v}"')
    if brushes:
        for b in brushes:
            lines.append(b)
    lines.append("}")
    return "\n".join(lines)


def generate_map():
    worldspawn_brushes = []
    entities = []

    # =====================================================
    # GROUND PLANE - big flat floor
    # =====================================================
    worldspawn_brushes.append(brush_box(
        MAP_MIN - 512, MAP_MIN - 512, -FLOOR_THICKNESS,
        MAP_MAX + 512, MAP_MAX + 512, MAP_FLOOR,
        {'top': TEX_FLOOR, 'bottom': TEX_CAULK, 'sides': TEX_CAULK}
    ))

    # =====================================================
    # SKYBOX - big hollow box around everything
    # =====================================================
    sky_margin = 512
    sx1 = MAP_MIN - sky_margin
    sy1 = MAP_MIN - sky_margin
    sx2 = MAP_MAX + sky_margin
    sy2 = MAP_MAX + sky_margin
    sz2 = SKYBOX_HEIGHT
    sky_t = 64  # wall thickness

    # Sky ceiling — extend to overlap with walls
    worldspawn_brushes.append(brush_box(
        sx1 - sky_t, sy1 - sky_t, sz2, sx2 + sky_t, sy2 + sky_t, sz2 + sky_t,
        TEX_SKY
    ))
    # Sky walls (4 sides) — extend side walls to overlap at corners
    worldspawn_brushes.append(brush_box(sx1 - sky_t, sy1 - sky_t, -FLOOR_THICKNESS, sx2 + sky_t, sy1, sz2 + sky_t, TEX_SKY))  # south
    worldspawn_brushes.append(brush_box(sx1 - sky_t, sy2, -FLOOR_THICKNESS, sx2 + sky_t, sy2 + sky_t, sz2 + sky_t, TEX_SKY))  # north
    worldspawn_brushes.append(brush_box(sx1 - sky_t, sy1 - sky_t, -FLOOR_THICKNESS, sx1, sy2 + sky_t, sz2 + sky_t, TEX_SKY))  # west
    worldspawn_brushes.append(brush_box(sx2, sy1 - sky_t, -FLOOR_THICKNESS, sx2 + sky_t, sy2 + sky_t, sz2 + sky_t, TEX_SKY))  # east

    # =====================================================
    # BUILDINGS - on each grid block
    # =====================================================
    building_configs = []

    wall_textures = [TEX_WALL, TEX_WALL2, TEX_WALL3]

    for gx in range(GRID_SIZE):
        for gy in range(GRID_SIZE):
            # Block origin (bottom-left corner)
            bx = MAP_MIN + STREET_WIDTH + gx * (BLOCK_SIZE + STREET_WIDTH)
            by = MAP_MIN + STREET_WIDTH + gy * (BLOCK_SIZE + STREET_WIDTH)

            # Center 2x2 blocks form an open plaza
            if gx in (1, 2) and gy in (1, 2):
                # Plaza - no buildings, just open ground
                # Add some low walls/cover
                if gx == 1 and gy == 1:
                    # Low wall for cover
                    worldspawn_brushes.append(brush_box(
                        bx + 256, by + 256, MAP_FLOOR, bx + 768, by + 288, 64,
                        {'top': TEX_ROOF, 'sides': TEX_WALL, 'bottom': TEX_CAULK}
                    ))
                elif gx == 2 and gy == 2:
                    worldspawn_brushes.append(brush_box(
                        bx + 256, by + 512, MAP_FLOOR, bx + 768, by + 544, 64,
                        {'top': TEX_ROOF, 'sides': TEX_WALL, 'bottom': TEX_CAULK}
                    ))
                continue

            # Pick building height based on position
            if (gx + gy) % 3 == 0:
                height = random.randint(512, 1024)
            elif (gx + gy) % 3 == 1:
                height = random.randint(256, 512)
            else:
                height = random.randint(384, 768)

            wall_tex = wall_textures[(gx * GRID_SIZE + gy) % len(wall_textures)]

            # Building: 4 walls + roof (hollow inside)
            # Inset slightly from block edge for sidewalk feel
            inset = 32
            bx1 = bx + inset
            by1 = by + inset
            bx2 = bx + BLOCK_SIZE - inset
            by2 = by + BLOCK_SIZE - inset

            tex = {'top': TEX_ROOF, 'sides': wall_tex, 'bottom': TEX_CAULK}

            # South wall
            worldspawn_brushes.append(brush_box(
                bx1, by1, MAP_FLOOR, bx2, by1 + WALL_THICKNESS, height, tex
            ))
            # North wall
            worldspawn_brushes.append(brush_box(
                bx1, by2 - WALL_THICKNESS, MAP_FLOOR, bx2, by2, height, tex
            ))
            # West wall
            worldspawn_brushes.append(brush_box(
                bx1, by1, MAP_FLOOR, bx1 + WALL_THICKNESS, by2, height, tex
            ))
            # East wall
            worldspawn_brushes.append(brush_box(
                bx2 - WALL_THICKNESS, by1, MAP_FLOOR, bx2, by2, height, tex
            ))
            # Roof
            worldspawn_brushes.append(brush_box(
                bx1, by1, height, bx2, by2, height + WALL_THICKNESS,
                {'top': TEX_CAULK, 'bottom': TEX_ROOF, 'sides': wall_tex}
            ))

            # Door opening on south side (cut a gap)
            # We'll make the south wall in two pieces with a gap
            # Actually, let's replace the south wall with two segments leaving a door
            door_width = 128
            door_height = 192  # tall enough for a player (56 units tall)
            door_center = (bx1 + bx2) // 2

            # Remove the south wall we just added and replace with two segments + door header
            worldspawn_brushes.pop(-5)  # Remove the full south wall

            # Left segment of south wall
            worldspawn_brushes.append(brush_box(
                bx1, by1, MAP_FLOOR, door_center - door_width // 2, by1 + WALL_THICKNESS, height, tex
            ))
            # Right segment of south wall
            worldspawn_brushes.append(brush_box(
                door_center + door_width // 2, by1, MAP_FLOOR, bx2, by1 + WALL_THICKNESS, height, tex
            ))
            # Door header (above the opening)
            worldspawn_brushes.append(brush_box(
                door_center - door_width // 2, by1, door_height,
                door_center + door_width // 2, by1 + WALL_THICKNESS, height, tex
            ))

            # Also add a door on the east side for a second entrance
            worldspawn_brushes.pop(-5)  # Remove the full east wall
            worldspawn_brushes.append(brush_box(
                bx2 - WALL_THICKNESS, by1, MAP_FLOOR, bx2, door_center - door_width // 2 - by1 + by1, height, tex
            ))
            # Wait, door position on east wall is Y-axis. Let me recalculate.
            east_door_y = (by1 + by2) // 2
            # Remove that bad brush
            worldspawn_brushes.pop()

            # East wall - bottom segment
            worldspawn_brushes.append(brush_box(
                bx2 - WALL_THICKNESS, by1, MAP_FLOOR, bx2, east_door_y - door_width // 2, height, tex
            ))
            # East wall - top segment
            worldspawn_brushes.append(brush_box(
                bx2 - WALL_THICKNESS, east_door_y + door_width // 2, MAP_FLOOR, bx2, by2, height, tex
            ))
            # East wall - door header
            worldspawn_brushes.append(brush_box(
                bx2 - WALL_THICKNESS, east_door_y - door_width // 2, door_height,
                bx2, east_door_y + door_width // 2, height, tex
            ))

            # Interior floor platform at half height (accessible ledge inside)
            platform_h = height // 2
            if height > 384:
                worldspawn_brushes.append(brush_box(
                    bx1 + WALL_THICKNESS, by1 + WALL_THICKNESS, platform_h,
                    bx1 + BLOCK_SIZE // 3, by2 - WALL_THICKNESS, platform_h + WALL_THICKNESS,
                    {'top': TEX_FLOOR, 'bottom': TEX_CAULK, 'sides': TEX_CAULK}
                ))

            building_configs.append({
                'x': bx, 'y': by, 'height': height,
                'door_south': (door_center, by1, MAP_FLOOR),
                'door_east': (bx2, east_door_y, MAP_FLOOR),
            })

    # =====================================================
    # RAMPS between buildings (connecting rooftops)
    # =====================================================
    # Add a few ramps/stairs at street intersections
    # Simple ramp: a slanted brush. Q3 doesn't do angled brushes easily,
    # so we'll use stair-steps instead.

    def add_stairs(x, y, z_start, z_end, direction, width=128):
        """Add stair steps. direction: 'x+', 'x-', 'y+', 'y-'"""
        n_steps = max(1, (z_end - z_start) // 16)
        step_h = (z_end - z_start) / n_steps
        step_d = 16  # depth per step

        for i in range(n_steps):
            sz = z_start + int(i * step_h)
            ez = z_start + int((i + 1) * step_h)

            if direction == 'y+':
                worldspawn_brushes.append(brush_box(
                    x, y + i * step_d, MAP_FLOOR, x + width, y + (i + 1) * step_d, ez,
                    {'top': TEX_FLOOR, 'sides': TEX_WALL3, 'bottom': TEX_CAULK}
                ))
            elif direction == 'x+':
                worldspawn_brushes.append(brush_box(
                    x + i * step_d, y, MAP_FLOOR, x + (i + 1) * step_d, y + width, ez,
                    {'top': TEX_FLOOR, 'sides': TEX_WALL3, 'bottom': TEX_CAULK}
                ))

    # Stairs leading up to a couple of the shorter buildings
    # Near building at grid (0,0)
    b00_x = MAP_MIN + STREET_WIDTH
    b00_y = MAP_MIN + STREET_WIDTH
    add_stairs(b00_x - 192, b00_y + 256, MAP_FLOOR, 256, 'x+', 128)

    # Near building at grid (3,3)
    b33_x = MAP_MIN + STREET_WIDTH + 3 * (BLOCK_SIZE + STREET_WIDTH)
    b33_y = MAP_MIN + STREET_WIDTH + 3 * (BLOCK_SIZE + STREET_WIDTH)
    add_stairs(b33_x + 256, b33_y - 192, MAP_FLOOR, 256, 'y+', 128)

    # =====================================================
    # STREET LIGHTS (light entities along streets)
    # =====================================================
    for gx in range(GRID_SIZE + 1):
        for gy in range(GRID_SIZE + 1):
            # Light at each intersection
            lx = MAP_MIN + STREET_WIDTH // 2 + gx * (BLOCK_SIZE + STREET_WIDTH)
            ly = MAP_MIN + STREET_WIDTH // 2 + gy * (BLOCK_SIZE + STREET_WIDTH)
            entities.append(entity("light", origin=(lx, ly, 400), extra_keys={
                "light": "1500",
                "_color": "1 0.95 0.85"
            }))

    # Additional fill lights for ground-level visibility (stay within map bounds)
    for x_off in range(5):
        for y_off in range(5):
            lx = MAP_MIN + 500 + x_off * ((MAP_MAX - MAP_MIN - 1000) // 4)
            ly = MAP_MIN + 500 + y_off * ((MAP_MAX - MAP_MIN - 1000) // 4)
            entities.append(entity("light", origin=(lx, ly, 300), extra_keys={
                "light": "800",
                "_color": "1 0.95 0.9"
            }))

    # =====================================================
    # SPAWN POINTS - scattered around streets and plaza
    # =====================================================
    spawn_locations = []

    # Spawns along the main streets
    for i in range(8):
        sx = MAP_MIN + STREET_WIDTH // 2 + (i % 4) * (BLOCK_SIZE + STREET_WIDTH)
        sy = MAP_MIN + STREET_WIDTH // 2 + (i // 4 + 1) * (BLOCK_SIZE + STREET_WIDTH)
        spawn_locations.append((sx, sy, MAP_FLOOR + 24))

    # Spawns in the central plaza
    plaza_cx = 0  # Center of map
    plaza_cy = 0
    for angle_idx in range(4):
        angle = angle_idx * 90 + 45
        rad = math.radians(angle)
        sx = int(plaza_cx + 400 * math.cos(rad))
        sy = int(plaza_cy + 400 * math.sin(rad))
        spawn_locations.append((sx, sy, MAP_FLOOR + 24))

    # Spawns near building entrances
    for bc in building_configs[:4]:
        sx, sy, sz = bc['door_south']
        spawn_locations.append((sx, sy - 64, MAP_FLOOR + 24))

    for i, loc in enumerate(spawn_locations):
        angle = (i * 60) % 360
        entities.append(entity("info_player_deathmatch", origin=loc, extra_keys={
            "angle": str(angle)
        }))

    # =====================================================
    # WEAPON PICKUPS
    # =====================================================
    weapon_spots = [
        # Railgun on a rooftop (reward for climbing)
        ("weapon_railgun", (b00_x + 512, b00_y + 512, 300)),
        # Rocket launcher in the plaza
        ("weapon_rocketlauncher", (plaza_cx, plaza_cy, MAP_FLOOR + 24)),
        # Lightning gun in an alley
        ("weapon_lightning", (MAP_MIN + STREET_WIDTH + BLOCK_SIZE + STREET_WIDTH // 2,
                              MAP_MIN + STREET_WIDTH // 2, MAP_FLOOR + 24)),
        # Shotgun near a building entrance
        ("weapon_shotgun", (b33_x + 512, b33_y - 128, MAP_FLOOR + 24)),
        # Plasma gun on the other side
        ("weapon_plasmagun", (MAP_MIN + STREET_WIDTH // 2,
                               MAP_MAX - STREET_WIDTH // 2, MAP_FLOOR + 24)),
        # Grenade launcher mid-map
        ("weapon_grenadelauncher", (plaza_cx + 600, plaza_cy - 600, MAP_FLOOR + 24)),
    ]

    for classname, origin in weapon_spots:
        entities.append(entity(classname, origin=origin))

    # Ammo boxes near weapons
    ammo_types = [
        ("ammo_slugs", weapon_spots[0][1]),
        ("ammo_rockets", weapon_spots[1][1]),
        ("ammo_lightning", weapon_spots[2][1]),
        ("ammo_shells", weapon_spots[3][1]),
        ("ammo_cells", weapon_spots[4][1]),
        ("ammo_grenades", weapon_spots[5][1]),
    ]
    for classname, near in ammo_types:
        ox = near[0] + 64
        oy = near[1] + 64
        entities.append(entity(classname, origin=(ox, oy, near[2])))

    # Health and armor pickups
    health_spots = [
        (plaza_cx - 300, plaza_cy + 300, MAP_FLOOR + 24),
        (plaza_cx + 300, plaza_cy - 300, MAP_FLOOR + 24),
        (MAP_MIN + STREET_WIDTH // 2 + 2 * (BLOCK_SIZE + STREET_WIDTH),
         MAP_MIN + STREET_WIDTH // 2, MAP_FLOOR + 24),
    ]
    for loc in health_spots:
        entities.append(entity("item_health_large", origin=loc))

    armor_spots = [
        (plaza_cx, plaza_cy + 500, MAP_FLOOR + 24),
        (MAP_MAX - STREET_WIDTH // 2, MAP_MAX - STREET_WIDTH // 2, MAP_FLOOR + 24),
    ]
    for loc in armor_spots:
        entities.append(entity("item_armor_body", origin=loc))

    # =====================================================
    # ASSEMBLE THE .MAP FILE
    # =====================================================
    lines = []

    # Worldspawn entity (contains all structural brushes)
    lines.append("// entity 0")
    lines.append("{")
    lines.append('\t"classname" "worldspawn"')
    lines.append('\t"message" "QuakeFall City"')
    lines.append('\t"music" "music/sonic5.wav"')
    for i, b in enumerate(worldspawn_brushes):
        lines.append(f"\n\t// brush {i}")
        lines.append(b)
    lines.append("}")

    # All other entities
    for e in entities:
        lines.append(e)

    return "\n".join(lines)


if __name__ == "__main__":
    import os

    map_content = generate_map()

    # Write to maps directory
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "maps")
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(out_dir, "qfcity1.map")
    with open(out_path, "w") as f:
        f.write(map_content)

    # Count things
    brush_count = map_content.count("  {")  # brush opening braces (indented)
    entity_count = map_content.count('"classname"') - 1  # minus worldspawn
    print(f"Generated {out_path}")
    print(f"  Brushes: {brush_count}")
    print(f"  Entities: {entity_count}")
    print(f"  File size: {len(map_content)} bytes")
