# Ақылды киіз үй — Blender моделі (6 қанат, кереге биіктігі 1,5 м).
#
# Қолдану: Blender -> Scripting -> осы файлды ашып, "Run Script" басыңыз.
# Немесе терминалда:  blender --background --python kiiz_uy_model.py
#
# Нәтиже (скрипт жатқан папкаға):
#   kiiz_uy_model.blend  — Blender файлы
#   kiiz_uy_model.glb    — веб үшін 3D модель (glTF)
#   kiiz_uy_render.png   — Cycles рендері
#
# Объектілердің аты сайттағы бөліктермен сәйкес келеді:
#   kerege_*, esik_*, shanyraq_*, kuldireuish, uyk_###, tuyrlyq_*, uzik_*,
#   tundik_*, oshaq_*, tor_*, interior_*, datchik_*
import bpy
import math
import os
from mathutils import Vector

OUT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()

# ---------- өлшемдер (сайттағы формулалармен бірдей) ----------
KANAT, H = 6, 1.5
R = KANAT * 3.2 / (2 * math.pi)          # кереге радиусы ≈ 3,06 м
r = 0.3 + 0.12 * R                        # шаңырақ радиусы ≈ 0,67 м
TAN = math.tan(math.radians(32))          # шатыр еңісі 32°
HT = H + (R - r) * TAN                    # шаңырақ биіктігі ≈ 2,99 м
U = KANAT * 15                            # уық саны = 90

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
col = scene.collection


def P(rad, ang, y):
    """Сайттағы полярлық координата -> Blender (Z жоғары). Есік ang = π/2 жағында."""
    return Vector((rad * math.cos(ang), -rad * math.sin(ang), y))


def line_y(rad):
    return H + (R - rad) * TAN


# ---------- материалдар ----------
def material(name, color, metallic=0.0, roughness=0.6, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = 4.0
    return m


MAT = {
    "wood": material("wood", (0.52, 0.32, 0.15), 0, 0.7),
    "wood_dark": material("wood_dark", (0.29, 0.16, 0.07), 0, 0.75),
    "uyk_red": material("uyk_red", (0.55, 0.09, 0.05), 0, 0.55),
    "kiiz_wall": material("kiiz_wall", (0.80, 0.74, 0.62), 0, 0.95),
    "kiiz_roof": material("kiiz_roof", (0.76, 0.70, 0.58), 0, 0.95),
    "kiiz_tundik": material("kiiz_tundik", (0.70, 0.64, 0.52), 0, 0.95),
    "rope": material("rope", (0.24, 0.14, 0.07), 0, 1),
    "door": material("door", (0.62, 0.24, 0.08), 0, 0.5),
    "gold": material("gold", (0.80, 0.60, 0.20), 0.6, 0.35),
    "carpet": material("carpet", (0.45, 0.07, 0.05), 0, 1),
    "stone": material("stone", (0.36, 0.35, 0.33), 0, 1),
    "fire": material("fire", (1.0, 0.45, 0.08), 0, 1, emission=(1.0, 0.5, 0.1)),
    "chest": material("chest", (0.45, 0.07, 0.05), 0, 0.45),
    "plastic": material("plastic", (0.08, 0.36, 0.48), 0, 0.45),
    "screen": material("screen", (0.2, 0.9, 0.4), 0, 0.3, emission=(0.2, 0.9, 0.4)),
}


# ---------- геометрия көмекшілері ----------
def make_obj(name, verts, faces, mat, uvs=None, smooth=True, loc=(0, 0, 0), parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    if uvs is not None:
        layer = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices:
                layer.data[li].uv = uvs[me.loops[li].vertex_index]
    me.update()
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.data.materials.append(MAT[mat])
    col.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def catmull(points, seg):
    """Catmull-Rom қисығы бойынша нүктелер (сайттағы CatmullRomCurve3 сияқты)."""
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        n = max(1, seg // (len(points) - 1))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(points[-1])
    return out


def tube_data(pts, radius, sides=6, base=0):
    """Нүктелер бойымен түтік (сырық): төбелер мен беттер."""
    verts, faces = [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        n = t.cross(ref).normalized()
        b = t.cross(n).normalized()
        for s in range(sides):
            a = 2 * math.pi * s / sides
            verts.append(p + radius * (math.cos(a) * n + math.sin(a) * b))
    for i in range(len(pts) - 1):
        for s in range(sides):
            a = base + i * sides + s
            c = base + i * sides + (s + 1) % sides
            faces.append((a, c, c + sides, a + sides))
    return verts, faces


def tube(name, pts, radius, mat, sides=6, loc=(0, 0, 0), parent=None):
    v, f = tube_data(pts, radius, sides)
    return make_obj(name, v, f, mat, loc=loc, parent=parent)


def cube(name, size, loc, mat, rot=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = size
    ob.data.materials.append(MAT[mat])
    if parent:
        ob.parent = parent
        ob.location = loc
    return ob


def torus(name, major, minor, loc, mat, rot=(0, 0, 0), parent=None, seg=64):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=seg, minor_segments=10, location=loc, rotation=rot)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(MAT[mat])
    bpy.ops.object.shade_smooth()
    if parent:
        ob.parent = parent
        ob.location = loc
    return ob


def empty(name, loc, rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.location = loc
    ob.rotation_euler = rot
    col.objects.link(ob)
    return ob


# ---------- КЕРЕГЕ: айқасқан тор (бір объект) ----------
dh = 0.55 / R
a0, a1 = math.pi / 2 + dh, math.pi / 2 + 2 * math.pi - dh
heads = KANAT * 14
step = (a1 - a0) / heads
span = H * 0.95 / R
kv, kf = [], []
for d in (0, 1):
    th = a0 - span
    while th <= a1 + 1e-6:
        if d == 0:
            t0, t1 = max(0, (a0 - th) / span), min(1, (a1 - th) / span)
        else:
            t0, t1 = max(0, (th + span - a1) / span), min(1, (th + span - a0) / span)
        if t1 - t0 >= 0.04:
            pts = []
            for i in range(7):
                t = t0 + (t1 - t0) * i / 6
                ang = th + span - span * t if d else th + span * t
                pts.append(P(R + (0.018 if d else -0.018), ang, H * t))
            v, f = tube_data(pts, 0.022, 6, base=len(kv))
            kv += v
            kf += f
        th += step
make_obj("kerege_lattice", kv, kf, "wood")

# ---------- ЕСІК ----------
dw = 0.5
door_y = -R          # есік Blender-де -Y жағында


def door_pt(x, y, z=0.0):
    return (x, door_y - z, y)


cube("esik_post_L", (0.09, 0.1, H), door_pt(-dw, H / 2), "wood_dark")
cube("esik_post_R", (0.09, 0.1, H), door_pt(dw, H / 2), "wood_dark")
cube("esik_lintel", (2 * dw + 0.09, 0.1, 0.1), door_pt(0, H - 0.05), "wood_dark")
cube("esik_sill", (2 * dw + 0.09, 0.12, 0.08), door_pt(0, 0.04), "wood_dark")
pw, ph = dw - 0.05, H - 0.2
for s, side in ((-1, "L"), (1, "R")):
    hinge = empty(f"esik_hinge_{side}", door_pt(s * (dw - 0.045), 0, 0.02), (0, 0, s * -0.55))
    cube(f"esik_panel_{side}", (pw, 0.04, ph), (-s * pw / 2, 0, 0.08 + ph / 2), "door", parent=hinge)
    torus(f"esik_orn1_{side}", pw * 0.26, 0.018, (-s * pw / 2, -0.03, 0.08 + ph * 0.6), "gold", (math.pi / 2, 0, 0), parent=hinge, seg=24)
    torus(f"esik_orn2_{side}", pw * 0.14, 0.015, (-s * pw / 2, -0.03, 0.08 + ph * 0.25), "gold", (math.pi / 2, 0, 0), parent=hinge, seg=20)

# ---------- ШАҢЫРАҚ және КҮЛДІРЕУІШ ----------
torus("shanyraq_ring", r, 0.07, (0, 0, HT), "wood_dark")
torus("shanyraq_ring2", r + 0.1, 0.035, (0, 0, HT - 0.03), "wood")
kv, kf = [], []
for rot in (0, math.pi / 2):
    for fr in (-0.45, 0, 0.45):
        d = fr * r
        c = math.sqrt(r * r - d * d)
        hgt = 0.3 * r
        pts = []
        for i in range(11):
            x = -c + 2 * c * i / 10
            yy = hgt * (1 - (x / c) ** 2)
            # сайттағы координата (x, y, d), Y осінің айналасында rot бұрышқа бұрылған
            X = x * math.cos(rot) + d * math.sin(rot)
            Z = -x * math.sin(rot) + d * math.cos(rot)
            pts.append(Vector((X, -Z, HT + yy)))
        v, f = tube_data(pts, 0.03, 6, base=len(kv))
        kv += v
        kf += f
make_obj("kuldireuish", kv, kf, "wood")

# ---------- УЫҚТАР (әрқайсысы бөлек, анимация үшін) ----------
for j in range(U):
    ang = math.pi / 2 + (j + 0.5) * 2 * math.pi / U
    prof = [(R + 0.03, H - 0.38), (R + 0.01, H - 0.05), (R - 0.3, line_y(R - 0.3) + 0.03),
            ((R + r) / 2, line_y((R + r) / 2) + 0.02), (r + 0.04, HT)]
    pts = catmull([P(rad, ang, y) for rad, y in prof], 12)
    tube(f"uyk_{j:03d}", pts, 0.028, "uyk_red", sides=6)

# ---------- ТУЫРЛЫҚ (қабырға киізі), баулар, түрілген етек ----------
dhF = 0.56 / (R + 0.05)
seg = 96
wv, wf, wuv = [], [], []
for i in range(seg + 1):
    th = dhF + (2 * math.pi - 2 * dhF) * i / seg
    x, z = (R + 0.05) * math.sin(th), (R + 0.05) * math.cos(th)    # сайттағы цилиндр (x = r·sinθ, z = r·cosθ)
    for k, hy in enumerate((-(H + 0.1) / 2, (H + 0.1) / 2)):
        wv.append(Vector((x, -z, hy)))
        wuv.append((i / seg, k))
for i in range(seg):
    a = i * 2
    wf.append((a, a + 2, a + 3, a + 1))
make_obj("tuyrlyq_wall", wv, wf, "kiiz_wall", uvs=wuv, loc=(0, 0, (H + 0.1) / 2))


def arc_pts(rad, z, n=96):
    return [P(rad, math.pi / 2 + dhF + (2 * math.pi - 2 * dhF) * i / n, z) for i in range(n + 1)]


tube("tuyrlyq_rope_low", arc_pts(R + 0.065, H * 0.3), 0.015, "rope")
tube("tuyrlyq_rope_high", arc_pts(R + 0.065, H * 0.68), 0.015, "rope")
roll = tube("tuyrlyq_roll", arc_pts(R + 0.1, 0), 0.07, "kiiz_wall", sides=10)
roll.hide_render = True        # тек жазғы режимде көрінеді (сайтта)

# ---------- ҮЗІК (шатыр киізі) ----------
lift, rb, rt = 0.13, R + 0.2, r + 0.1
yb, yt = line_y(rb) + lift, line_y(rt) + lift
rv, rf, ruv = [], [], []
for i in range(seg + 1):
    th = 2 * math.pi * i / seg
    for k, (rad, zz) in enumerate(((rb, yb), (rt, yt))):
        rv.append(Vector((rad * math.sin(th), -rad * math.cos(th), zz)))
        ruv.append((i / seg, k))
for i in range(seg):
    a = i * 2
    rf.append((a, a + 2, a + 3, a + 1))
make_obj("uzik_roof", rv, rf, "kiiz_roof", uvs=ruv)

# ---------- ТҮНДІК (топсамен ашылады) ----------
tr = r + 0.3
pivot = empty("tundik_pivot", (tr, 0, HT + 0.1))
tv, tf, tuv = [], [], []
for k in range(5):
    th = math.pi / 4 + k * math.pi / 2
    for j, (rad, yy) in enumerate(((tr, 0.0), (0.04, 0.22))):
        x, z = rad * math.sin(th) - tr, rad * math.cos(th)
        tv.append(Vector((x, -z, yy)))
        tuv.append((k / 4, j))
for k in range(4):
    a = k * 2
    tf.append((a, a + 2, a + 3, a + 1))
make_obj("tundik_cap", tv, tf, "kiiz_tundik", uvs=tuv, smooth=False, parent=pivot)

# ---------- ІШКІ ЖАБДЫҚ: кілем, ошақ, төр ----------
cv, cf, cuv = [Vector((0, 0, 0.01))], [], [(0.5, 0.5)]
cr = R - 0.08
for i in range(64):
    a = 2 * math.pi * i / 64
    cv.append(Vector((cr * math.cos(a), cr * math.sin(a), 0.01)))
    cuv.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
for i in range(64):
    cf.append((0, 1 + i, 1 + (i + 1) % 64))
make_obj("interior_carpet", cv, cf, "carpet", uvs=cuv, smooth=False)

stones = []
for i in range(11):
    a = i / 11 * 2 * math.pi
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.1 + (i % 3) * 0.012, location=(0.36 * math.cos(a), -0.36 * math.sin(a), 0.07), rotation=(i * 0.7, i * 1.3, 0))
    stones.append(bpy.context.active_object)
bpy.ops.object.select_all(action="DESELECT")
for s in stones:
    s.select_set(True)
bpy.context.view_layer.objects.active = stones[0]
bpy.ops.object.join()
st = bpy.context.active_object
st.name = "oshaq_stones"
st.data.materials.clear()
st.data.materials.append(MAT["stone"])
bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.16, depth=0.42, location=(0, 0, 0.23))
fire = bpy.context.active_object
fire.name = "oshaq_fire"
fire.data.materials.append(MAT["fire"])

cube("tor_chest", (1.3, 0.55, 0.55), (0, R - 0.55, 0.3), "chest")
cube("tor_trim", (1.34, 0.58, 0.06), (0, R - 0.55, 0.5), "gold")
cube("tor_blankets", (1.2, 0.5, 0.35), (0, R - 0.55, 0.75), "door")

# ---------- ДАТЧИК (кереге үстінде, ошаққа қарап тұр) ----------
s_ang = math.pi / 2 - 2.3
spos = P(R - 0.1, s_ang, 1.15)
box = cube("datchik_box", (0.16, 0.06, 0.22), tuple(spos), "plastic", rot=(0, 0, math.pi / 2 - s_ang))
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.52, 0.18), rotation=(-math.pi / 2, 0, 0))
scr = bpy.context.active_object
scr.name = "datchik_screen"
scr.scale = (0.75, 0.32, 1)
scr.data.materials.append(MAT["screen"])
scr.parent = box
scr.location = (0, 0.52, 0.18)
cube("datchik_grill", (0.62, 0.17, 0.27), (0, 0.5, -0.25), "wood_dark", parent=box)

# ---------- жер, жарық, камера (тек Blender рендері үшін) ----------
bpy.ops.mesh.primitive_circle_add(vertices=64, radius=14, fill_type="NGON", location=(0, 0, -0.005))
ground = bpy.context.active_object
ground.name = "render_ground"
ground.data.materials.append(material("render_ground", (0.36, 0.40, 0.22), 0, 1))
bpy.ops.object.light_add(type="SUN", location=(8, -6, 12))
sun = bpy.context.active_object
sun.name = "render_sun"
sun.data.energy = 3.2
sun.rotation_euler = (math.radians(45), 0, math.radians(35))
world = bpy.data.worlds.new("sky")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.70, 0.88, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
bpy.ops.object.camera_add(location=(7.5, -8.5, 4.6))
cam = bpy.context.active_object
cam.name = "render_camera"
cam.data.lens = 35
tgt = empty("render_target", (0, 0, 1.3))
c = cam.constraints.new("TRACK_TO")
c.target = tgt
c.track_axis = "TRACK_NEGATIVE_Z"
c.up_axis = "UP_Y"
scene.camera = cam

# ---------- сақтау ----------
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "kiiz_uy_model.blend"))
# вебке тек киіз үйдің өзі шығады (жер, жарық, камера кірмейді)
bpy.ops.object.select_all(action="DESELECT")
for ob in scene.objects:
    if not ob.name.startswith("render_"):
        ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "kiiz_uy_model.glb"), export_format="GLB", use_selection=True,
                          export_lights=False, export_cameras=False, export_apply=True)
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 48
scene.view_settings.view_transform = "Standard"
scene.render.resolution_x = 1280
scene.render.resolution_y = 800
scene.render.filepath = os.path.join(OUT, "kiiz_uy_render.png")
bpy.ops.render.render(write_still=True)
print("Дайын:", OUT, "уық:", U, "R =", round(R, 3), "Ht =", round(HT, 3))
