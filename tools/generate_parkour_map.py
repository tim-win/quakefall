#!/usr/bin/env python3
"""
Generate a parkour test course map for QuakeFall.
Output: maps/parkour1.map

Sections connected by corridors:
1. Wall Run Straightaway — two long parallel walls, pit beneath
2. Wall Run Curve — angled brush segments approximating a curve
3. Wall Chain Corridor — alternating walls with gaps
4. Double Jump Gaps — progressive pits requiring jump, double jump, speed
5. Slide Tunnel — downhill ramp into low-ceiling corridor
6. Ledge Grab Tower — vertical climb with chest-height ledges
7. Vault Course — series of waist-height obstacles
8. Mixed Course — combines everything
9. Tuning Arena — open room for isolated parameter testing

Q3 coordinate system: 1 unit ~= 1 inch. Player is 56 units tall, 30 units wide.
"""

import math

# Textures from demo pak
TEX_FLOOR = "base_floor/diamond2c"
TEX_WALL = "gothic_block/blocks17"
TEX_WALL2 = "gothic_block/blocks15"
TEX_WALL3 = "base_wall/metalfloor_wall_15"
TEX_ROOF = "gothic_block/blocks18b"
TEX_SKY = "skies/xtoxicsky_q3ctf3"
TEX_CAULK = "common/caulk"
TEX_LIGHT = "base_light/lt2_8000"
TEX_FLOOR2 = "base_floor/tilefloor7"
TEX_OBSTACLE = "gothic_block/blocks18b"

# Map constants
WALL_T = 16          # wall/brush thickness
FLOOR_T = 64         # floor thickness
CORRIDOR_W = 256     # corridor width
CORRIDOR_H = 256     # corridor height
SECTION_GAP = 128    # gap between sections (corridor length)
SKYBOX_H = 2048      # sky ceiling height


def brush_box(x1, y1, z1, x2, y2, z2, textures=None):
    if textures is None:
        textures = {'all': TEX_WALL}
    elif isinstance(textures, str):
        textures = {'all': textures}

    def tex(face):
        return textures.get(face, textures.get('all', TEX_CAULK))

    def p(x, y, z):
        return f"( {x:.3f} {y:.3f} {z:.3f} )"

    def face(p0, p1, p2, texture):
        return f"\t\t{p(*p0)} {p(*p1)} {p(*p2)} {texture} 0.00000000 0.00000000 0.00000000 0.50000000 0.50000000 0 0 0"

    lines = ["\t{"]
    lines.append(face((x1,y1,z2), (x1,y1,z1), (x1,y2,z1), tex('sides')))
    lines.append(face((x2,y2,z2), (x2,y2,z1), (x2,y1,z1), tex('sides')))
    lines.append(face((x2,y1,z1), (x1,y1,z1), (x1,y1,z2), tex('sides')))
    lines.append(face((x2,y2,z2), (x1,y2,z2), (x1,y2,z1), tex('sides')))
    lines.append(face((x1,y2,z1), (x1,y1,z1), (x2,y1,z1), tex('bottom')))
    lines.append(face((x2,y2,z2), (x2,y1,z2), (x1,y1,z2), tex('top')))
    lines.append("\t}")
    return "\n".join(lines)


def entity(classname, origin=None, extra_keys=None, brushes=None):
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


def room_floor(x1, y1, x2, y2, z=0):
    """Floor brush at z level."""
    return brush_box(x1, y1, z - FLOOR_T, x2, y2, z,
        {'top': TEX_FLOOR, 'bottom': TEX_CAULK, 'sides': TEX_CAULK})


def room_walls(x1, y1, x2, y2, z_floor=0, z_ceil=256, tex=TEX_WALL):
    """Four walls around a rectangular room."""
    t = WALL_T
    brushes = []
    texd = {'all': tex}
    # south wall
    brushes.append(brush_box(x1-t, y1-t, z_floor, x2+t, y1, z_ceil, texd))
    # north wall
    brushes.append(brush_box(x1-t, y2, z_floor, x2+t, y2+t, z_ceil, texd))
    # west wall
    brushes.append(brush_box(x1-t, y1, z_floor, x1, y2, z_ceil, texd))
    # east wall
    brushes.append(brush_box(x2, y1, z_floor, x2+t, y2, z_ceil, texd))
    return brushes


def room_ceiling(x1, y1, x2, y2, z_ceil=256):
    """Ceiling brush."""
    return brush_box(x1 - WALL_T, y1 - WALL_T, z_ceil, x2 + WALL_T, y2 + WALL_T, z_ceil + WALL_T,
        {'bottom': TEX_ROOF, 'all': TEX_CAULK})


def corridor(x1, y1, x2, y2, z_floor=0, z_ceil=256, direction='y'):
    """Corridor with floor, walls, ceiling. Open at both ends along direction axis."""
    brushes = []
    brushes.append(room_floor(x1, y1, x2, y2, z_floor))
    brushes.append(room_ceiling(x1, y1, x2, y2, z_ceil))
    t = WALL_T
    if direction == 'y':
        # walls on east/west sides
        brushes.append(brush_box(x1-t, y1, z_floor, x1, y2, z_ceil, TEX_WALL))
        brushes.append(brush_box(x2, y1, z_floor, x2+t, y2, z_ceil, TEX_WALL))
    else:
        # walls on north/south sides
        brushes.append(brush_box(x1, y1-t, z_floor, x2, y1, z_ceil, TEX_WALL))
        brushes.append(brush_box(x1, y2, z_floor, x2, y2+t, z_ceil, TEX_WALL))
    return brushes


def generate_map():
    brushes = []
    entities = []

    # Map is laid out along the Y axis. Each section advances in +Y.
    # Current Y position tracker
    cy = 0

    # =========================================================
    # SECTION 0: SPAWN AREA
    # =========================================================
    sx1, sy1 = -256, cy
    sx2, sy2 = 256, cy + 512
    brushes.append(room_floor(sx1, sy1, sx2, sy2))
    brushes.extend(room_walls(sx1, sy1, sx2, sy2, z_ceil=256))
    brushes.append(room_ceiling(sx1, sy1, sx2, sy2, 256))

    # Spawn points
    for i in range(4):
        x = -128 + (i % 2) * 256
        y = sy1 + 128 + (i // 2) * 256
        entities.append(entity("info_player_deathmatch",
            origin=(x, y, 24), extra_keys={"angle": "90"}))

    # Opening in north wall for corridor
    # (We'll leave a gap by not extending the north wall fully)
    # Actually, let's just cut the corridor opening — use three wall segments instead of full north wall
    # Replace the full north wall with segments leaving a corridor-width gap in center
    # We already added full walls above; let me handle this differently.
    # Actually, corridors between sections will just be open connections.
    # We build each section as a room, and connect them with short corridors.
    # The room_walls function makes full walls, so let me adjust the approach:
    # Build sections with open ends where corridors connect.

    # Simpler approach: each section is an open-topped trough (floor + side walls)
    # with the corridor connecting them. This avoids wall-gap complexity.

    cy = sy2

    # =========================================================
    # SECTION 1: WALL RUN STRAIGHTAWAY
    # Two long parallel walls with a pit beneath. Run along wall to cross.
    # =========================================================
    sec_x1, sec_y1 = -256, cy
    sec_x2, sec_y2 = 256, cy + 768
    wall_len = sec_y2 - sec_y1

    # Floor with a pit in the middle section
    # Entry floor
    brushes.append(room_floor(sec_x1, sec_y1, sec_x2, sec_y1 + 128))
    # Exit floor
    brushes.append(room_floor(sec_x1, sec_y2 - 128, sec_x2, sec_y2))
    # Pit (lower floor for death/damage)
    brushes.append(brush_box(sec_x1, sec_y1 + 128, -256, sec_x2, sec_y2 - 128, -192,
        {'top': TEX_FLOOR2, 'all': TEX_CAULK}))

    # Long parallel walls (for wall running)
    wall_h = 384
    # Left wall
    brushes.append(brush_box(sec_x1 - WALL_T, sec_y1, 0, sec_x1, sec_y2, wall_h, TEX_WALL2))
    # Right wall
    brushes.append(brush_box(sec_x2, sec_y1, 0, sec_x2 + WALL_T, sec_y2, wall_h, TEX_WALL2))

    # Ceiling
    brushes.append(room_ceiling(sec_x1, sec_y1, sec_x2, sec_y2, wall_h))

    # Light at entry
    entities.append(entity("light", origin=(0, sec_y1 + 64, wall_h - 32),
        extra_keys={"light": "300"}))

    cy = sec_y2

    # Short corridor
    brushes.extend(corridor(sec_x1, cy, sec_x2, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 2: WALL RUN CURVE
    # Angled brush segments approximating a curved wall.
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 768
    curve_x1, curve_x2 = -384, 384

    # Floor
    brushes.append(room_floor(curve_x1, sec_y1, curve_x2, sec_y2))

    # Outer wall on right side (straight)
    brushes.append(brush_box(curve_x2, sec_y1, 0, curve_x2 + WALL_T, sec_y2, 384, TEX_WALL))

    # Inner curved wall on left side (5 angled segments)
    num_segs = 6
    seg_len = (sec_y2 - sec_y1) / num_segs
    for i in range(num_segs):
        # Curve: wall x position varies as a sine wave
        x_offset = int(100 * math.sin(math.pi * i / (num_segs - 1)))
        y_start = int(sec_y1 + i * seg_len)
        y_end = int(sec_y1 + (i + 1) * seg_len)
        wx = curve_x1 + x_offset
        brushes.append(brush_box(wx - WALL_T, y_start, 0, wx, y_end, 384, TEX_WALL2))

    # Ceiling
    brushes.append(room_ceiling(curve_x1 - 128, sec_y1, curve_x2, sec_y2, 384))

    entities.append(entity("light", origin=(0, (sec_y1+sec_y2)//2, 350),
        extra_keys={"light": "400"}))

    cy = sec_y2

    # Corridor
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 3: WALL CHAIN CORRIDOR
    # Alternating walls with gaps. Wall run → wall jump → wall run.
    # =========================================================
    sec_y1 = cy
    chain_len = 1024
    sec_y2 = cy + chain_len
    chain_w = 384  # corridor width

    # Floor is a pit (death if you fall)
    brushes.append(brush_box(-chain_w//2, sec_y1, -256, chain_w//2, sec_y2, -192,
        {'top': TEX_FLOOR2, 'all': TEX_CAULK}))

    # Entry/exit platforms
    brushes.append(room_floor(-chain_w//2, sec_y1, chain_w//2, sec_y1 + 96))
    brushes.append(room_floor(-chain_w//2, sec_y2 - 96, chain_w//2, sec_y2))

    # Alternating wall segments
    seg_count = 4
    seg_h = 384
    seg_gap = chain_len // (seg_count + 1)
    for i in range(seg_count):
        seg_y = sec_y1 + (i + 1) * seg_gap - 64
        if i % 2 == 0:
            # Right wall segment
            brushes.append(brush_box(chain_w//2 - WALL_T, seg_y, 0,
                chain_w//2, seg_y + 192, seg_h, TEX_WALL3))
        else:
            # Left wall segment
            brushes.append(brush_box(-chain_w//2, seg_y, 0,
                -chain_w//2 + WALL_T, seg_y + 192, seg_h, TEX_WALL3))

    # Outer walls (full length, for boundary)
    brushes.append(brush_box(-chain_w//2 - WALL_T, sec_y1, -256, -chain_w//2, sec_y2, seg_h, TEX_WALL))
    brushes.append(brush_box(chain_w//2, sec_y1, -256, chain_w//2 + WALL_T, sec_y2, seg_h, TEX_WALL))
    brushes.append(room_ceiling(-chain_w//2, sec_y1, chain_w//2, sec_y2, seg_h))

    entities.append(entity("light", origin=(0, (sec_y1+sec_y2)//2, seg_h - 32),
        extra_keys={"light": "400"}))

    cy = sec_y2
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 4: DOUBLE JUMP GAPS
    # Progressive pits: normal jump, double jump, speed + double jump
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 1024
    gap_w = 512

    brushes.append(room_floor(-gap_w//2, sec_y1, gap_w//2, sec_y2))

    # Pit floor (below)
    brushes.append(brush_box(-gap_w//2, sec_y1, -256, gap_w//2, sec_y2, -192,
        {'top': TEX_FLOOR2, 'all': TEX_CAULK}))

    # Platform sections with gaps between them
    platforms = [
        (sec_y1, sec_y1 + 128),         # start platform
        (sec_y1 + 256, sec_y1 + 384),   # after normal jump gap (128 units)
        (sec_y1 + 576, sec_y1 + 704),   # after double jump gap (192 units)
        (sec_y1 + 896, sec_y2),          # final platform (after big gap, 192 units)
    ]
    for py1, py2 in platforms:
        brushes.append(brush_box(-gap_w//2, py1, 0, gap_w//2, py2, WALL_T,
            {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Walls and ceiling
    brushes.append(brush_box(-gap_w//2 - WALL_T, sec_y1, 0, -gap_w//2, sec_y2, 256, TEX_WALL))
    brushes.append(brush_box(gap_w//2, sec_y1, 0, gap_w//2 + WALL_T, sec_y2, 256, TEX_WALL))
    brushes.append(room_ceiling(-gap_w//2, sec_y1, gap_w//2, sec_y2, 256))

    entities.append(entity("light", origin=(0, (sec_y1+sec_y2)//2, 200),
        extra_keys={"light": "400"}))

    cy = sec_y2
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 5: SLIDE TUNNEL
    # Downhill ramp → low ceiling corridor → uphill exit
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 768
    slide_w = 384

    # Entry area (normal height)
    brushes.append(room_floor(-slide_w//2, sec_y1, slide_w//2, sec_y1 + 128))

    # Downhill ramp (descends 64 units over 128 units length)
    ramp_steps = 8
    for i in range(ramp_steps):
        ry1 = sec_y1 + 128 + i * 16
        ry2 = ry1 + 16
        rz = -i * 8
        brushes.append(brush_box(-slide_w//2, ry1, rz - WALL_T, slide_w//2, ry2, rz,
            {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Low tunnel floor (at -64)
    tunnel_y1 = sec_y1 + 128 + ramp_steps * 16
    tunnel_y2 = sec_y2 - 128 - ramp_steps * 16
    tunnel_z = -64
    brushes.append(brush_box(-slide_w//2, tunnel_y1, tunnel_z - WALL_T,
        slide_w//2, tunnel_y2, tunnel_z,
        {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Low ceiling (crouch height = 16 units above feet, feet at z=-24 relative to origin)
    # Player origin at tunnel_z + 24 (feet at tunnel_z), crouch height = 16
    # Ceiling at tunnel_z + 40 (allows crouched but not standing)
    low_ceil = tunnel_z + 48
    brushes.append(brush_box(-slide_w//2, tunnel_y1, low_ceil,
        slide_w//2, tunnel_y2, low_ceil + WALL_T, TEX_ROOF))

    # Uphill ramp (mirror of downhill)
    for i in range(ramp_steps):
        ry1 = tunnel_y2 + i * 16
        ry2 = ry1 + 16
        rz = tunnel_z + i * 8
        brushes.append(brush_box(-slide_w//2, ry1, rz - WALL_T, slide_w//2, ry2, rz,
            {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Exit area (normal height)
    brushes.append(room_floor(-slide_w//2, sec_y2 - 128, slide_w//2, sec_y2))

    # Side walls for entire section
    brushes.append(brush_box(-slide_w//2 - WALL_T, sec_y1, -128, -slide_w//2, sec_y2, 256, TEX_WALL))
    brushes.append(brush_box(slide_w//2, sec_y1, -128, slide_w//2 + WALL_T, sec_y2, 256, TEX_WALL))
    # Normal height ceiling for entry/exit areas
    brushes.append(room_ceiling(-slide_w//2, sec_y1, slide_w//2, sec_y1 + 128, 256))
    brushes.append(room_ceiling(-slide_w//2, sec_y2 - 128, slide_w//2, sec_y2, 256))

    entities.append(entity("light", origin=(0, sec_y1 + 64, 200),
        extra_keys={"light": "300"}))
    entities.append(entity("light", origin=(0, sec_y2 - 64, 200),
        extra_keys={"light": "300"}))

    cy = sec_y2
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 6: LEDGE GRAB TOWER
    # Vertical climb with ledges at chest height.
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 512
    tower_w = 384
    num_ledges = 4
    ledge_spacing = 72  # each ledge 72 units above previous (chest height = ~48+)

    # Ground floor
    brushes.append(room_floor(-tower_w//2, sec_y1, tower_w//2, sec_y2))

    # Ledge platforms (ascending, alternating sides)
    for i in range(num_ledges):
        lz = (i + 1) * ledge_spacing
        ly = sec_y1 + 64 + i * 96
        if i % 2 == 0:
            # Right side ledge
            brushes.append(brush_box(32, ly, lz, tower_w//2 - 32, ly + 96, lz + WALL_T,
                {'top': TEX_FLOOR, 'all': TEX_OBSTACLE}))
            # Back wall behind ledge
            brushes.append(brush_box(tower_w//2 - 32, ly, lz - 64,
                tower_w//2 - 16, ly + 96, lz + 64, TEX_WALL2))
        else:
            # Left side ledge
            brushes.append(brush_box(-tower_w//2 + 32, ly, lz, -32, ly + 96, lz + WALL_T,
                {'top': TEX_FLOOR, 'all': TEX_OBSTACLE}))
            brushes.append(brush_box(-tower_w//2 + 16, ly, lz - 64,
                -tower_w//2 + 32, ly + 96, lz + 64, TEX_WALL2))

    # Top platform
    top_z = (num_ledges + 1) * ledge_spacing
    brushes.append(brush_box(-tower_w//2, sec_y2 - 128, top_z,
        tower_w//2, sec_y2, top_z + WALL_T,
        {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Walls
    tower_h = top_z + 128
    brushes.append(brush_box(-tower_w//2 - WALL_T, sec_y1, 0, -tower_w//2, sec_y2, tower_h, TEX_WALL))
    brushes.append(brush_box(tower_w//2, sec_y1, 0, tower_w//2 + WALL_T, sec_y2, tower_h, TEX_WALL))
    brushes.append(brush_box(-tower_w//2, sec_y1 - WALL_T, 0, tower_w//2, sec_y1, tower_h, TEX_WALL))
    brushes.append(room_ceiling(-tower_w//2, sec_y1, tower_w//2, sec_y2, tower_h))

    # Drop-down back to ground level (opening in floor at exit)
    # Exit corridor starts from top platform height
    entities.append(entity("light", origin=(0, (sec_y1+sec_y2)//2, top_z + 64),
        extra_keys={"light": "400"}))

    cy = sec_y2
    # Ramp back down to ground level
    ramp_len = 256
    ramp_steps_down = 16
    for i in range(ramp_steps_down):
        ry1 = cy + i * (ramp_len // ramp_steps_down)
        ry2 = ry1 + (ramp_len // ramp_steps_down)
        rz = top_z - i * (top_z / ramp_steps_down)
        brushes.append(brush_box(-128, ry1, rz - WALL_T, 128, ry2, rz,
            {'top': TEX_FLOOR, 'all': TEX_CAULK}))
    # Walls along ramp
    brushes.append(brush_box(-128 - WALL_T, cy, 0, -128, cy + ramp_len, top_z + 128, TEX_WALL))
    brushes.append(brush_box(128, cy, 0, 128 + WALL_T, cy + ramp_len, top_z + 128, TEX_WALL))

    cy += ramp_len
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 7: VAULT COURSE
    # Series of waist-height obstacles in a row.
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 768
    vault_w = 384

    brushes.append(room_floor(-vault_w//2, sec_y1, vault_w//2, sec_y2))

    # Waist-height obstacles (height ~40 units, player can vault over)
    num_obstacles = 5
    obs_spacing = (sec_y2 - sec_y1 - 128) // (num_obstacles + 1)
    for i in range(num_obstacles):
        oy = sec_y1 + 64 + (i + 1) * obs_spacing
        # Obstacle: full width, 40 units tall, 32 units deep
        brushes.append(brush_box(-vault_w//4, oy - 16, 0,
            vault_w//4, oy + 16, 40, TEX_OBSTACLE))

    # Walls and ceiling
    brushes.append(brush_box(-vault_w//2 - WALL_T, sec_y1, 0, -vault_w//2, sec_y2, 256, TEX_WALL))
    brushes.append(brush_box(vault_w//2, sec_y1, 0, vault_w//2 + WALL_T, sec_y2, 256, TEX_WALL))
    brushes.append(room_ceiling(-vault_w//2, sec_y1, vault_w//2, sec_y2, 256))

    entities.append(entity("light", origin=(0, (sec_y1+sec_y2)//2, 200),
        extra_keys={"light": "400"}))

    cy = sec_y2
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 8: MIXED COURSE
    # Slide → double jump → wall run → wall jump → ledge grab → vault
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 1536
    mix_w = 512

    # Ground floor
    brushes.append(room_floor(-mix_w//2, sec_y1, mix_w//2, sec_y2))

    # 8a: Low barrier to slide under (at y+128)
    barrier_y = sec_y1 + 128
    brushes.append(brush_box(-mix_w//4, barrier_y, 48, mix_w//4, barrier_y + 16, 256, TEX_OBSTACLE))

    # 8b: Gap requiring double jump (at y+384)
    gap_y = sec_y1 + 384
    # Remove floor section (pit)
    brushes.append(brush_box(-mix_w//2, gap_y, -128, mix_w//2, gap_y + 192, -64,
        {'top': TEX_FLOOR2, 'all': TEX_CAULK}))

    # 8c: Wall run section (at y+640)
    wr_y = sec_y1 + 640
    # Wall on right side only, pit below
    brushes.append(brush_box(mix_w//2 - WALL_T, wr_y, 0, mix_w//2, wr_y + 256, 384, TEX_WALL2))
    # Pit below wall run area
    brushes.append(brush_box(-mix_w//2, wr_y, -128, mix_w//2, wr_y + 256, -64,
        {'top': TEX_FLOOR2, 'all': TEX_CAULK}))

    # 8d: Ledge grab at y+960
    ledge_y = sec_y1 + 960
    ledge_z = 80  # chest height
    brushes.append(brush_box(-64, ledge_y, ledge_z, 64, ledge_y + 96, ledge_z + WALL_T,
        {'top': TEX_FLOOR, 'all': TEX_OBSTACLE}))
    # Wall behind ledge
    brushes.append(brush_box(-64, ledge_y + 96, ledge_z - 64, 64, ledge_y + 112, ledge_z + 128, TEX_WALL2))

    # 8e: Vault obstacles at y+1152
    for i in range(3):
        vy = sec_y1 + 1152 + i * 96
        brushes.append(brush_box(-64, vy, 0, 64, vy + 24, 40, TEX_OBSTACLE))

    # 8f: Exit platform
    brushes.append(brush_box(-mix_w//2, sec_y2 - 64, 0, mix_w//2, sec_y2, WALL_T,
        {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Walls
    brushes.append(brush_box(-mix_w//2 - WALL_T, sec_y1, -128, -mix_w//2, sec_y2, 384, TEX_WALL))
    brushes.append(brush_box(mix_w//2, sec_y1, -128, mix_w//2 + WALL_T, sec_y2, 384, TEX_WALL))
    brushes.append(room_ceiling(-mix_w//2, sec_y1, mix_w//2, sec_y2, 384))

    entities.append(entity("light", origin=(0, (sec_y1+sec_y2)//2, 350),
        extra_keys={"light": "500"}))

    cy = sec_y2
    brushes.extend(corridor(-256, cy, 256, cy + SECTION_GAP, z_ceil=256))
    cy += SECTION_GAP

    # =========================================================
    # SECTION 9: TUNING ARENA
    # Open room with one wall, one ledge, one ramp.
    # =========================================================
    sec_y1 = cy
    sec_y2 = cy + 1024
    arena_w = 1024

    brushes.append(room_floor(-arena_w//2, sec_y1, arena_w//2, sec_y2))
    brushes.extend(room_walls(-arena_w//2, sec_y1, arena_w//2, sec_y2, z_ceil=512))
    brushes.append(room_ceiling(-arena_w//2, sec_y1, arena_w//2, sec_y2, 512))

    # Isolated wall for wall run testing
    brushes.append(brush_box(-arena_w//2 + 32, sec_y1 + 128, 0,
        -arena_w//2 + 48, sec_y1 + 640, 384, TEX_WALL2))

    # Ledge for grab testing
    brushes.append(brush_box(arena_w//4, sec_y1 + 256, 72,
        arena_w//4 + 128, sec_y1 + 384, 72 + WALL_T,
        {'top': TEX_FLOOR, 'all': TEX_OBSTACLE}))

    # Vault obstacle
    brushes.append(brush_box(-64, sec_y2 - 256, 0, 64, sec_y2 - 232, 40, TEX_OBSTACLE))

    # Ramp for slide testing
    ramp_steps_arena = 12
    for i in range(ramp_steps_arena):
        ry1 = sec_y1 + 640 + i * 24
        ry2 = ry1 + 24
        rz = i * 6
        brushes.append(brush_box(-128, ry1, rz, 128, ry2, rz + 8,
            {'top': TEX_FLOOR, 'all': TEX_CAULK}))

    # Lights
    for dy in range(3):
        entities.append(entity("light",
            origin=(0, sec_y1 + 128 + dy * 300, 450),
            extra_keys={"light": "400"}))

    # Spawn point in arena
    entities.append(entity("info_player_deathmatch",
        origin=(0, sec_y1 + 64, 24), extra_keys={"angle": "90"}))

    # =========================================================
    # SKYBOX
    # =========================================================
    map_min_x = -arena_w//2 - 256
    map_max_x = arena_w//2 + 256
    map_min_y = -256 - 256
    map_max_y = cy + 1024 + 256
    sky_t = 64

    # Ceiling
    brushes.append(brush_box(map_min_x - sky_t, map_min_y - sky_t, SKYBOX_H,
        map_max_x + sky_t, map_max_y + sky_t, SKYBOX_H + sky_t, TEX_SKY))
    # South
    brushes.append(brush_box(map_min_x - sky_t, map_min_y - sky_t, -FLOOR_T - 64,
        map_max_x + sky_t, map_min_y, SKYBOX_H + sky_t, TEX_SKY))
    # North
    brushes.append(brush_box(map_min_x - sky_t, map_max_y, -FLOOR_T - 64,
        map_max_x + sky_t, map_max_y + sky_t, SKYBOX_H + sky_t, TEX_SKY))
    # West
    brushes.append(brush_box(map_min_x - sky_t, map_min_y - sky_t, -FLOOR_T - 64,
        map_min_x, map_max_y + sky_t, SKYBOX_H + sky_t, TEX_SKY))
    # East
    brushes.append(brush_box(map_max_x, map_min_y - sky_t, -FLOOR_T - 64,
        map_max_x + sky_t, map_max_y + sky_t, SKYBOX_H + sky_t, TEX_SKY))
    # Bottom (below all pits)
    brushes.append(brush_box(map_min_x - sky_t, map_min_y - sky_t, -FLOOR_T - 128,
        map_max_x + sky_t, map_max_y + sky_t, -FLOOR_T - 64, TEX_SKY))

    # =========================================================
    # ASSEMBLE MAP FILE
    # =========================================================
    worldspawn = entity("worldspawn",
        extra_keys={"message": "Parkour Test Course", "music": ""},
        brushes=brushes)

    parts = [worldspawn] + entities
    return "\n".join(parts)


if __name__ == "__main__":
    import os
    map_content = generate_map()
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "maps", "parkour1.map")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as f:
        f.write(map_content)
    print(f"Generated {out_path}")
    print(f"Compile with: tools/compile_map.sh maps/parkour1.map")
