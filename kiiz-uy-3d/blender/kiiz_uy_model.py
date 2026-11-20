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
    "baskur": material("baskur", (0.55, 0.08, 0.06), 0, 0.9),
    "tuskiiz": material("tuskiiz", (0.25, 0.05, 0.08), 0, 0.9),
    "sirmaq": material("sirmaq", (0.55, 0.10, 0.06), 0, 1),
    "juk_red": material("juk_red", (0.62, 0.10, 0.08), 0, 0.9),
    "juk_blue": material("juk_blue", (0.10, 0.22, 0.50), 0, 0.9),
    "juk_green": material("juk_green", (0.12, 0.40, 0.22), 0, 0.9),
    "juk_yellow": material("juk_yellow", (0.85, 0.62, 0.12), 0, 0.9),
    "juk_white": material("juk_white", (0.88, 0.86, 0.80), 0, 0.9),
    "qazan": material("qazan", (0.07, 0.07, 0.07), 0.7, 0.5),
    "dht": material("dht", (0.92, 0.92, 0.90), 0, 0.5),
    "pcb": material("pcb", (0.02, 0.33, 0.55), 0.1, 0.5),
    "chip": material("chip", (0.03, 0.03, 0.03), 0.2, 0.4),
    "metal": material("metal", (0.75, 0.75, 0.78), 0.9, 0.3),
    "lcd": material("lcd", (0.10, 0.30, 0.85), 0, 0.3, emission=(0.10, 0.30, 0.85)),
    "servo": material("servo", (0.05, 0.25, 0.70), 0, 0.5),
    "wire_red": material("wire_red", (0.75, 0.05, 0.05), 0, 0.6),
    "wire_black": material("wire_black", (0.02, 0.02, 0.02), 0, 0.6),
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

# үзік баулары: шаңырақтан етекке дейін сыртынан тартылған 8 бау
for k in range(8):
    a = math.pi / 2 + math.pi / 8 + k * math.pi / 4
    pts = [P(rad, a, line_y(rad) + lift + 0.02) for rad in [rt + 0.05 + (rb - rt - 0.1) * i / 10 for i in range(11)]]
    tube(f"uzik_rope_{k}", pts, 0.016, "rope")

# БАСҚҰР: керегенің жоғарғы жағын іштен айнала байлайтын оюлы белдеу
bv, bf, buv = [], [], []
n = 120
for i in range(n + 1):
    a = a0 + 0.02 + (a1 - a0 - 0.04) * i / n
    for k, zz in enumerate((H - 0.30, H - 0.08)):
        bv.append(P(R - 0.045, a, zz))
        buv.append((i / n, k))
for i in range(n):
    q = i * 2
    bf.append((q, q + 2, q + 3, q + 1))
make_obj("baskur_band", bv, bf, "baskur", uvs=buv)

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

# ошақ үстіндегі үш аяқ және қазан
bv, bf = [], []
seg_q, rows = 32, 9
for i in range(rows):
    t = i / (rows - 1) * math.pi / 2
    rr, zz = 0.30 * math.sin(t) + 0.0001, 0.76 - 0.27 * math.cos(t)
    for k in range(seg_q):
        a = 2 * math.pi * k / seg_q
        bv.append(Vector((rr * math.cos(a), rr * math.sin(a), zz)))
for i in range(rows - 1):
    for k in range(seg_q):
        a, b = i * seg_q + k, i * seg_q + (k + 1) % seg_q
        bf.append((a, b, b + seg_q, a + seg_q))
make_obj("oshaq_qazan", bv, bf, "qazan")
torus("oshaq_qazan_rim", 0.305, 0.018, (0, 0, 0.76), "qazan", seg=32)
tv, tf = [], []
v, f = tube_data([Vector((0.34 * math.cos(2 * math.pi * k / 40), 0.34 * math.sin(2 * math.pi * k / 40), 0.6)) for k in range(41)], 0.015, 6)
tv += v; tf += f
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.3
    v, f = tube_data([Vector((0.34 * math.cos(a), 0.34 * math.sin(a), 0.6)), Vector((0.44 * math.cos(a), 0.44 * math.sin(a), 0.0))], 0.016, 6, base=len(tv))
    tv += v; tf += f
make_obj("oshaq_tripod", tv, tf, "qazan")

cube("tor_chest", (1.3, 0.55, 0.55), (0, R - 0.55, 0.3), "chest")
cube("tor_trim", (1.34, 0.58, 0.06), (0, R - 0.55, 0.5), "gold")
# жүк: сандық үстіне үйілген көрпелер мен жастықтар
z = 0.53
for i, (m, w) in enumerate([("juk_red", 1.20), ("juk_blue", 1.16), ("juk_yellow", 1.22), ("juk_green", 1.14), ("juk_red", 1.18), ("juk_white", 1.10)]):
    cube(f"tor_juk_{i}", (w, 0.48 - 0.01 * (i % 2), 0.075), (0.01 * ((i % 3) - 1), R - 0.55, z + 0.0375), m)
    z += 0.075
for k, x in enumerate((-0.27, 0.27)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1, location=(x, R - 0.58, z + 0.08))
    pil = bpy.context.active_object
    pil.name = f"tor_pillow_{k}"
    pil.scale = (0.27, 0.19, 0.09)
    pil.data.materials.append(MAT["juk_white"])
    bpy.ops.object.shade_smooth()

# тұскиіз: төрдегі кереге бетіне ілінген кестелі кілем
tv, tf, tuv = [], [], []
n = 24
for i in range(n + 1):
    a = 3 * math.pi / 2 - 0.42 + 0.84 * i / n
    for k, zz in enumerate((0.62, 1.18)):
        tv.append(P(R - 0.07, a, zz))
        tuv.append((i / n, k))
for i in range(n):
    q = i * 2
    tf.append((q, q + 2, q + 3, q + 1))
make_obj("tor_tuskiiz", tv, tf, "tuskiiz", uvs=tuv)

# сырмақ: төрдің алдындағы оюлы киіз төсеніш
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, R - 1.75, 0.018))
sm = bpy.context.active_object
sm.name = "interior_sirmaq"
sm.scale = (1.8, 1.05, 1)
sm.data.materials.append(MAT["sirmaq"])

# ---------- ДАТЧИК (кереге үстінде, ошаққа қарап тұр) ----------
s_ang = math.pi / 2 - 2.3
spos = P(R - 0.1, s_ang, 1.15)
box = cube("datchik_box", (0.10, 0.05, 0.16), tuple(spos), "dht", rot=(0, 0, math.pi / 2 - s_ang))
for gi in range(4):                                            # DHT22 торлы беті
    cube(f"datchik_grill_{gi}", (0.8, 0.12, 0.08), (0, 0.5, 0.3 - gi * 0.2), "chip", parent=box)


# ---------- ARDUINO ЖҮЙЕСІ: Uno, LCD 1602, зуммер, SG90 серво, сымдар ----------
def on_wall(name, size, ang, z, mat, depth_off=0.13):
    return cube(name, size, tuple(P(R - depth_off, ang, z)), mat, rot=(0, 0, math.pi / 2 - ang))


ub = s_ang + 0.13
on_wall("arduino_uno", (0.27, 0.025, 0.2), ub, 0.82, "pcb")
on_wall("arduino_chip", (0.12, 0.02, 0.03), ub, 0.80, "chip", 0.145)
on_wall("arduino_usb", (0.05, 0.03, 0.04), ub + 0.035, 0.90, "metal", 0.145)
on_wall("arduino_header", (0.2, 0.02, 0.015), ub, 0.715, "chip", 0.145)
lb = s_ang - 0.15
on_wall("arduino_lcd", (0.22, 0.03, 0.09), lb, 1.14, "pcb")
on_wall("arduino_lcd_frame", (0.18, 0.031, 0.055), lb, 1.14, "chip", 0.133)
lp = P(R - 0.155, lb, 1.14)
bpy.ops.mesh.primitive_plane_add(size=1, location=tuple(lp), rotation=(math.pi / 2, 0, math.pi / 2 - lb + math.pi))
lcd = bpy.context.active_object
lcd.name = "arduino_lcd_screen"
lcd.scale = (0.16, 0.042, 1)
lcd.data.materials.append(MAT["lcd"])
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.028, depth=0.03, location=tuple(P(R - 0.14, ub + 0.11, 1.0)), rotation=(math.pi / 2, 0, math.pi / 2 - (ub + 0.11)))
bz = bpy.context.active_object
bz.name = "arduino_buzzer"
bz.data.materials.append(MAT["chip"])
# SG90 серво шаңырақтың астында, түндік топсасының жанында
cube("arduino_servo", (0.075, 0.035, 0.07), (r + 0.06, 0, HT - 0.13), "servo")
cube("arduino_servo_horn", (0.09, 0.012, 0.01), (r + 0.09, 0, HT - 0.09), "juk_white")
# сымдар: датчик -> Uno -> LCD, Uno -> кереге басымен -> уық бойымен -> серво
for wi, (mat, off) in enumerate((("wire_red", 0.0), ("wire_black", 0.014))):
    rr = R - 0.12 - off
    path = [P(rr, ub, 0.93), P(rr, ub, H - 0.1)]
    a_end = 2 * math.pi - 2 * math.pi            # уық 0 бұрышта (j = 67) жатыр
    for i in range(1, 13):
        path.append(P(rr, ub + (a_end - ub) * i / 12, H - 0.1))
    for i in range(1, 11):
        rad = R - 0.25 - (R - 0.25 - (r + 0.12)) * i / 10
        path.append(P(rad, off * 0.6, line_y(rad) - 0.07))
    path.append(Vector((r + 0.08, off * 0.6, HT - 0.12)))
    tube(f"arduino_wire_{wi}", path, 0.007, mat)
    tube(f"arduino_wire_s{wi}", catmull([P(rr, ub, 0.9), P(rr - 0.01, (ub + s_ang) / 2, 1.0), P(R - 0.12 - off, s_ang, 1.07)], 10), 0.006, mat)
    tube(f"arduino_wire_l{wi}", catmull([P(rr, ub, 0.92), P(rr - 0.01, (ub + lb) / 2, 1.05), P(R - 0.12 - off, lb, 1.09)], 10), 0.006, mat)

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
