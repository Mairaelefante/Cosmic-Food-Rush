"""Cosmic Food Truck Rush

A complete Panda3D arcade prototype built with procedural geometry only.
Run with: python main.py
"""

from __future__ import annotations

try:
    from direct.gui.OnscreenText import OnscreenText
    from direct.showbase.ShowBase import ShowBase
    from direct.task.Task import Task
    from panda3d.core import (
        AmbientLight,
        ClockObject,
        DirectionalLight,
        Geom,
        GeomNode,
        GeomTriangles,
        GeomVertexData,
        GeomVertexFormat,
        GeomVertexWriter,
        LineSegs,
        NodePath,
        PointLight,
        TextNode,
        TransparencyAttrib,
        Vec3,
        Vec4,
        loadPrcFileData,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - friendly runtime error
    raise SystemExit(
        "Panda3D is required to run Cosmic Food Truck Rush.\n"
        "Install it with: python -m pip install panda3d\n"
        "Then run: python main.py"
    ) from exc

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union


# Window setup before ShowBase is created.
loadPrcFileData("", "window-title Cosmic Food Truck Rush")
loadPrcFileData("", "win-size 1280 800")
loadPrcFileData("", "sync-video true")
loadPrcFileData("", "show-frame-rate-meter false")


Color = Tuple[float, float, float, float]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def vec4(color: Union[Color, Tuple[float, float, float], Vec4]) -> Vec4:
    if isinstance(color, Vec4):
        return color
    if len(color) == 3:
        return Vec4(color[0], color[1], color[2], 1.0)
    return Vec4(color[0], color[1], color[2], color[3])


def xy_distance(a: Vec3, b: Vec3) -> float:
    return math.hypot(a.getX() - b.getX(), a.getY() - b.getY())


def xy_direction(from_pos: Vec3, to_pos: Vec3) -> Tuple[float, float, float]:
    dx = to_pos.getX() - from_pos.getX()
    dy = to_pos.getY() - from_pos.getY()
    length = math.hypot(dx, dy)
    if length <= 0.0001:
        return 0.0, 0.0, 0.0
    return dx / length, dy / length, length


def write_vertex(
    vertex_writer: GeomVertexWriter,
    normal_writer: GeomVertexWriter,
    color_writer: GeomVertexWriter,
    position: Tuple[float, float, float],
    normal: Tuple[float, float, float],
    color: Vec4,
) -> None:
    vertex_writer.addData3f(position[0], position[1], position[2])
    normal_writer.addData3f(normal[0], normal[1], normal[2])
    color_writer.addData4f(color[0], color[1], color[2], color[3])


def make_cuboid(
    parent: NodePath,
    name: str,
    sx: float,
    sy: float,
    sz: float,
    color: Union[Color, Tuple[float, float, float], Vec4],
    pos: Union[Tuple[float, float, float], Vec3] = (0, 0, 0),
    hpr: Union[Tuple[float, float, float], Vec3] = (0, 0, 0),
    two_sided: bool = False,
    unlit: bool = False,
) -> NodePath:
    """Create a colored cuboid mesh centered at the local origin."""
    c = vec4(color)
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UHStatic)

    hx, hy, hz = sx / 2.0, sy / 2.0, sz / 2.0
    faces = [
        ((0, 0, 1), [(-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]),
        ((0, 0, -1), [(-hx, hy, -hz), (hx, hy, -hz), (hx, -hy, -hz), (-hx, -hy, -hz)]),
        ((0, 1, 0), [(-hx, hy, -hz), (-hx, hy, hz), (hx, hy, hz), (hx, hy, -hz)]),
        ((0, -1, 0), [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, -hy, hz), (-hx, -hy, hz)]),
        ((1, 0, 0), [(hx, -hy, -hz), (hx, hy, -hz), (hx, hy, hz), (hx, -hy, hz)]),
        ((-1, 0, 0), [(-hx, -hy, -hz), (-hx, -hy, hz), (-hx, hy, hz), (-hx, hy, -hz)]),
    ]
    vertex_count = 0
    for normal, vertices in faces:
        base = vertex_count
        for vertex in vertices:
            write_vertex(vw, nw, cw, vertex, normal, c)
            vertex_count += 1
        tris.addVertices(base, base + 1, base + 2)
        tris.closePrimitive()
        tris.addVertices(base, base + 2, base + 3)
        tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = parent.attachNewNode(node)
    np.setPos(pos)
    np.setHpr(hpr)
    if two_sided:
        np.setTwoSided(True)
    if c[3] < 0.999:
        np.setTransparency(TransparencyAttrib.MAlpha)
    if unlit:
        np.setLightOff(1)
    return np


def make_cylinder(
    parent: NodePath,
    name: str,
    radius: float,
    height: float,
    color: Union[Color, Tuple[float, float, float], Vec4],
    pos: Union[Tuple[float, float, float], Vec3] = (0, 0, 0),
    hpr: Union[Tuple[float, float, float], Vec3] = (0, 0, 0),
    segments: int = 24,
    unlit: bool = False,
) -> NodePath:
    """Create a vertical colored cylinder centered at the local origin."""
    c = vec4(color)
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UHStatic)
    hz = height / 2.0
    vertex_count = 0

    # Side faces
    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        x0, y0 = radius * math.cos(a0), radius * math.sin(a0)
        x1, y1 = radius * math.cos(a1), radius * math.sin(a1)
        n0 = (math.cos(a0), math.sin(a0), 0)
        n1 = (math.cos(a1), math.sin(a1), 0)
        base = vertex_count
        write_vertex(vw, nw, cw, (x0, y0, -hz), n0, c)
        write_vertex(vw, nw, cw, (x1, y1, -hz), n1, c)
        write_vertex(vw, nw, cw, (x1, y1, hz), n1, c)
        write_vertex(vw, nw, cw, (x0, y0, hz), n0, c)
        vertex_count += 4
        tris.addVertices(base, base + 1, base + 2)
        tris.closePrimitive()
        tris.addVertices(base, base + 2, base + 3)
        tris.closePrimitive()

    # Top and bottom caps
    top_center = vertex_count
    write_vertex(vw, nw, cw, (0, 0, hz), (0, 0, 1), c)
    vertex_count += 1
    bottom_center = vertex_count
    write_vertex(vw, nw, cw, (0, 0, -hz), (0, 0, -1), c)
    vertex_count += 1

    for i in range(segments):
        a0 = 2.0 * math.pi * i / segments
        a1 = 2.0 * math.pi * (i + 1) / segments
        x0, y0 = radius * math.cos(a0), radius * math.sin(a0)
        x1, y1 = radius * math.cos(a1), radius * math.sin(a1)

        base_top = vertex_count
        write_vertex(vw, nw, cw, (x0, y0, hz), (0, 0, 1), c)
        write_vertex(vw, nw, cw, (x1, y1, hz), (0, 0, 1), c)
        vertex_count += 2
        tris.addVertices(top_center, base_top, base_top + 1)
        tris.closePrimitive()

        base_bottom = vertex_count
        write_vertex(vw, nw, cw, (x1, y1, -hz), (0, 0, -1), c)
        write_vertex(vw, nw, cw, (x0, y0, -hz), (0, 0, -1), c)
        vertex_count += 2
        tris.addVertices(bottom_center, base_bottom, base_bottom + 1)
        tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = parent.attachNewNode(node)
    np.setPos(pos)
    np.setHpr(hpr)
    if c[3] < 0.999:
        np.setTransparency(TransparencyAttrib.MAlpha)
    if unlit:
        np.setLightOff(1)
    return np


def make_sphere(
    parent: NodePath,
    name: str,
    radius: float,
    color: Union[Color, Tuple[float, float, float], Vec4],
    pos: Union[Tuple[float, float, float], Vec3] = (0, 0, 0),
    segments: int = 16,
    rings: int = 8,
    unlit: bool = False,
) -> NodePath:
    """Create a low-poly sphere mesh."""
    c = vec4(color)
    fmt = GeomVertexFormat.getV3n3c4()
    vdata = GeomVertexData(name, fmt, Geom.UHStatic)
    vw = GeomVertexWriter(vdata, "vertex")
    nw = GeomVertexWriter(vdata, "normal")
    cw = GeomVertexWriter(vdata, "color")
    tris = GeomTriangles(Geom.UHStatic)

    for i in range(rings + 1):
        phi = math.pi * i / rings
        z = math.cos(phi)
        ring_radius = math.sin(phi)
        for j in range(segments + 1):
            theta = 2.0 * math.pi * j / segments
            x = ring_radius * math.cos(theta)
            y = ring_radius * math.sin(theta)
            write_vertex(vw, nw, cw, (radius * x, radius * y, radius * z), (x, y, z), c)

    row = segments + 1
    for i in range(rings):
        for j in range(segments):
            a = i * row + j
            b = (i + 1) * row + j
            c_idx = b + 1
            d = a + 1
            if i != 0:
                tris.addVertices(a, b, d)
                tris.closePrimitive()
            if i != rings - 1:
                tris.addVertices(d, b, c_idx)
                tris.closePrimitive()

    geom = Geom(vdata)
    geom.addPrimitive(tris)
    node = GeomNode(name)
    node.addGeom(geom)
    np = parent.attachNewNode(node)
    np.setPos(pos)
    if c[3] < 0.999:
        np.setTransparency(TransparencyAttrib.MAlpha)
    if unlit:
        np.setLightOff(1)
    return np


def make_text(
    parent: NodePath,
    name: str,
    text: str,
    pos: Union[Tuple[float, float, float], Vec3],
    scale: float,
    color: Union[Color, Tuple[float, float, float], Vec4] = (1, 1, 1, 1),
    align: int = TextNode.ACenter,
    billboard: bool = True,
) -> Tuple[NodePath, TextNode]:
    tn = TextNode(name)
    tn.setText(text)
    tn.setAlign(align)
    c = vec4(color)
    tn.setTextColor(c[0], c[1], c[2], c[3])
    np = parent.attachNewNode(tn)
    np.setPos(pos)
    np.setScale(scale)
    np.setLightOff(1)
    if billboard:
        np.setBillboardPointEye()
    return np, tn


def make_line_circle(
    parent: NodePath,
    name: str,
    radius: float,
    color: Union[Color, Tuple[float, float, float], Vec4],
    pos: Union[Tuple[float, float, float], Vec3] = (0, 0, 0),
    segments: int = 64,
    thickness: float = 2.5,
) -> NodePath:
    c = vec4(color)
    ls = LineSegs(name)
    ls.setThickness(thickness)
    ls.setColor(c[0], c[1], c[2], c[3])
    first = True
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        x, y = radius * math.cos(a), radius * math.sin(a)
        if first:
            ls.moveTo(x, y, 0)
            first = False
        else:
            ls.drawTo(x, y, 0)
    np = parent.attachNewNode(ls.create())
    np.setPos(pos)
    np.setLightOff(1)
    if c[3] < 0.999:
        np.setTransparency(TransparencyAttrib.MAlpha)
    return np


def make_neon_line(
    parent: NodePath,
    name: str,
    points: List[Tuple[float, float, float]],
    color: Union[Color, Tuple[float, float, float], Vec4],
    thickness: float = 3.0,
) -> NodePath:
    c = vec4(color)
    ls = LineSegs(name)
    ls.setThickness(thickness)
    ls.setColor(c[0], c[1], c[2], c[3])
    if points:
        ls.moveTo(points[0][0], points[0][1], points[0][2])
        for p in points[1:]:
            ls.drawTo(p[0], p[1], p[2])
    np = parent.attachNewNode(ls.create())
    np.setLightOff(1)
    return np


@dataclass
class FoodStation:
    item_id: str
    name: str
    short: str
    pos: Vec3
    radius: float
    node: NodePath


@dataclass
class CustomerSpot:
    index: int
    spot_name: str
    pos: Vec3
    root: NodePath
    alien_node: NodePath
    order_label_np: NodePath
    order_text: TextNode
    feedback_label_np: NodePath
    feedback_text: TextNode
    bar_root: NodePath
    bar_fill: NodePath
    active: bool = False
    order_id: str = ""
    patience: float = 0.0
    max_patience: float = 25.0
    respawn_timer: float = 0.0
    feedback_timer: float = 0.0


@dataclass
class ConveyorHazard:
    pos: Vec3
    half_size: Tuple[float, float]
    direction: Vec3
    strength: float


@dataclass
class SauceHazard:
    pos: Vec3
    radius: float


@dataclass
class DeliveryBot:
    node: NodePath
    path: List[Vec3]
    speed: float
    target_index: int = 1
    hit_cooldown: float = 0.0


class CosmicFoodTruckRush(ShowBase):
    """Main Panda3D game application."""

    def __init__(self) -> None:
        super().__init__()
        self.disableMouse()
        self.clock = ClockObject.getGlobalClock()
        self.world_limit = 20.5

        random.seed()

        self.food_catalog: Dict[str, Dict[str, object]] = {
            "SPACE_TACOS": {
                "name": "Space Tacos",
                "short": "TACOS",
                "color": (1.00, 0.54, 0.10, 1),
            },
            "NEBULA_NOODLES": {
                "name": "Nebula Noodles",
                "short": "NOODLES",
                "color": (0.85, 0.32, 1.00, 1),
            },
            "GALAXY_SODA": {
                "name": "Galaxy Soda",
                "short": "SODA",
                "color": (0.05, 0.90, 1.00, 1),
            },
            "COMET_CAKE": {
                "name": "Comet Cake",
                "short": "CAKE",
                "color": (1.00, 0.30, 0.68, 1),
            },
            "MOON_SOUP": {
                "name": "Moon Soup",
                "short": "SOUP",
                "color": (0.20, 1.00, 0.55, 1),
            },
            "GLOW_FRUIT": {
                "name": "Glowing Fruit",
                "short": "FRUIT",
                "color": (0.72, 1.00, 0.10, 1),
            },
        }

        self.food_stations: List[FoodStation] = []
        self.customer_spots: List[CustomerSpot] = []
        self.conveyors: List[ConveyorHazard] = []
        self.sauce_puddles: List[SauceHazard] = []
        self.bots: List[DeliveryBot] = []

        self.player_np: Optional[NodePath] = None
        self.player_pos = Vec3(0, -3, 0)
        self.carried_order: Optional[str] = None
        self.carry_text: Optional[TextNode] = None

        self.keys: Dict[str, bool] = {
            "forward": False,
            "back": False,
            "left": False,
            "right": False,
        }

        self.state = "playing"
        self.score = 0
        self.completed_orders = 0
        self.left_customers = 0
        self.target_orders = 8
        self.max_left_customers = 4
        self.round_time_max = 150.0
        self.round_time = self.round_time_max
        self.message_timer = 0.0
        self.warning_timer = 0.0
        self.was_in_sauce = False
        self.interaction_radius = 2.35
        self.delivery_radius = 2.65
        self.bot_collision_cooldown = 0.0

        self.scene_root = self.render.attachNewNode("cosmic_market_scene")

        self.setup_camera()
        self.setup_lights()
        self.create_market_scene()
        self.create_player_truck()
        self.create_food_stations()
        self.create_customer_spots()
        self.create_hazards()
        self.create_hud()
        self.setup_controls()
        self.reset_game()
        self.taskMgr.add(self.update, "cosmic_food_truck_rush_update")

    # ---------------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------------
    def setup_camera(self) -> None:
        self.win.setClearColor(Vec4(0.015, 0.005, 0.055, 1))
        self.camLens.setFov(66)
        self.camera.setPos(0, -32, 24)
        self.camera.lookAt(0, 0, 0.5)

    def setup_lights(self) -> None:
        ambient = AmbientLight("soft_nebula_ambient")
        ambient.setColor(Vec4(0.34, 0.32, 0.48, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        key = DirectionalLight("warm_market_key")
        key.setColor(Vec4(0.95, 0.80, 0.62, 1))
        key_np = self.render.attachNewNode(key)
        key_np.setHpr(-35, -55, 0)
        self.render.setLight(key_np)

        fill = DirectionalLight("cool_neon_fill")
        fill.setColor(Vec4(0.25, 0.65, 1.0, 1))
        fill_np = self.render.attachNewNode(fill)
        fill_np.setHpr(145, -35, 0)
        self.render.setLight(fill_np)

        for name, pos, color in [
            ("pink_roof_glow", Vec3(-9, -9, 6), (1.0, 0.22, 0.75, 1)),
            ("cyan_market_glow", Vec3(8, -6, 6), (0.0, 0.95, 1.0, 1)),
            ("green_fruit_glow", Vec3(-13, 2, 5), (0.3, 1.0, 0.45, 1)),
        ]:
            light = PointLight(name)
            light.setColor(Vec4(*color))
            light.setAttenuation(Vec3(1, 0.035, 0.006))
            light_np = self.render.attachNewNode(light)
            light_np.setPos(pos)
            self.render.setLight(light_np)

    def setup_controls(self) -> None:
        bindings = {
            "w": "forward",
            "arrow_up": "forward",
            "s": "back",
            "arrow_down": "back",
            "a": "left",
            "arrow_left": "left",
            "d": "right",
            "arrow_right": "right",
        }
        for key, action in bindings.items():
            self.accept(key, self.set_key, [action, True])
            self.accept(f"{key}-up", self.set_key, [action, False])
        self.accept("e", self.try_interact)
        self.accept("space", self.try_interact)
        self.accept("r", self.restart_if_finished)
        self.accept("escape", self.userExit)

    def set_key(self, key: str, value: bool) -> None:
        self.keys[key] = value

    # ---------------------------------------------------------------------
    # World creation
    # ---------------------------------------------------------------------
    def create_market_scene(self) -> None:
        root = self.scene_root

        # Floor and delivery route.
        make_cuboid(root, "star_tile_floor", 45, 45, 0.12, (0.075, 0.045, 0.13, 1), pos=(0, 0, -0.08))
        for x in range(-20, 21, 5):
            make_neon_line(root, f"floor_line_x_{x}", [(x, -21, 0.02), (x, 21, 0.02)], (0.06, 0.42, 0.62, 0.35), 1.0)
        for y in range(-20, 21, 5):
            make_neon_line(root, f"floor_line_y_{y}", [(-21, y, 0.02), (21, y, 0.02)], (0.42, 0.07, 0.58, 0.35), 1.0)
        make_line_circle(root, "central_plaza_neon_ring", 8.6, (0.0, 0.95, 1.0, 0.55), pos=(0, 0, 0.05), thickness=3.0)
        make_line_circle(root, "central_plaza_orbit_ring", 13.8, (1.0, 0.42, 0.08, 0.45), pos=(0, 0, 0.055), thickness=2.4)

        # Decorative market stalls around the playable loop.
        stall_specs = [
            ("BUG JUICE", (-19, -12, 0), 0, (0.23, 0.75, 0.92, 1), (1.0, 0.42, 0.12, 1)),
            ("STAR SPICES", (-19, 4, 0), 0, (0.55, 0.30, 0.88, 1), (0.22, 1.0, 0.55, 1)),
            ("MOON MUNCH", (18, -15, 0), 0, (0.95, 0.32, 0.55, 1), (0.10, 0.95, 1.0, 1)),
            ("ORB TEA", (19, 3, 0), 0, (0.16, 0.80, 0.42, 1), (1.0, 0.86, 0.18, 1)),
            ("PLASMA PICKLES", (-6, 19, 0), 90, (0.86, 0.42, 0.18, 1), (0.70, 1.0, 0.12, 1)),
            ("SATURN SNACKS", (9, 19, 0), 90, (0.12, 0.62, 0.92, 1), (1.0, 0.30, 0.95, 1)),
        ]
        for label, pos, heading, body_color, trim_color in stall_specs:
            self.create_background_stall(root, label, Vec3(*pos), heading, body_color, trim_color)

        # Hanging lanterns and alien market clutter.
        for i, (x, y) in enumerate([(-17, -2), (-10, 15), (0, 18), (14, 14), (17, -4), (-13, -16), (8, -18)]):
            make_cylinder(root, f"lantern_post_{i}", 0.08, 3.0, (0.20, 0.18, 0.30, 1), pos=(x, y, 1.5))
            make_sphere(root, f"lantern_glow_{i}", 0.38, (1.0, 0.68, 0.18, 1), pos=(x, y, 3.15), unlit=True)
            make_line_circle(root, f"lantern_ring_{i}", 0.48, (0.0, 0.9, 1.0, 0.65), pos=(x, y, 3.15), thickness=2)

        # Sky stars and chunky planets. Humanity invented empty backgrounds, so this refuses.
        sky = root.attachNewNode("procedural_star_sky")
        for i in range(80):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(25, 48)
            x = math.cos(angle) * radius
            y = math.sin(angle) * radius
            z = random.uniform(8, 24)
            size = random.uniform(0.035, 0.11)
            color = random.choice([
                (0.95, 0.95, 1.0, 1),
                (0.20, 0.95, 1.0, 1),
                (1.0, 0.42, 0.95, 1),
                (1.0, 0.88, 0.30, 1),
            ])
            make_sphere(sky, f"star_{i}", size, color, pos=(x, y, z), segments=8, rings=4, unlit=True)

        planet_a = make_sphere(root, "purple_planet", 1.65, (0.43, 0.18, 0.88, 1), pos=(14, 24, 14), unlit=True)
        make_cylinder(planet_a, "flat_saturnish_ring", 2.35, 0.045, (0.95, 0.45, 1.0, 0.35), pos=(0, 0, 0), hpr=(0, 72, 0), segments=48, unlit=True)
        make_sphere(root, "tiny_blue_planet", 0.78, (0.10, 0.72, 1.0, 1), pos=(-19, 24, 11), unlit=True)

        # Big market title sign floating in the background.
        sign_root = root.attachNewNode("market_title_sign")
        sign_root.setPos(0, 19.8, 5.5)
        make_cuboid(sign_root, "title_backing", 10.5, 0.25, 2.0, (0.10, 0.05, 0.16, 1), unlit=True)
        make_cuboid(sign_root, "title_neon_trim", 10.9, 0.12, 2.25, (1.0, 0.46, 0.06, 1), pos=(0, -0.08, 0), unlit=True)
        make_text(sign_root, "title_text", "COSMIC FOOD TRUCK RUSH", (0, -0.18, 0.35), 0.52, (1.0, 0.72, 0.18, 1), billboard=True)
        make_text(sign_root, "title_sub", "Serve fast. Do not anger the tentacles.", (0, -0.18, -0.55), 0.28, (0.35, 1.0, 1.0, 1), billboard=True)

    def create_background_stall(
        self,
        parent: NodePath,
        label: str,
        pos: Vec3,
        heading: float,
        body_color: Color,
        trim_color: Color,
    ) -> None:
        stall = parent.attachNewNode(f"stall_{label}")
        stall.setPos(pos)
        stall.setH(heading)
        make_cuboid(stall, "counter", 4.6, 2.0, 1.0, body_color, pos=(0, 0, 0.55))
        make_cuboid(stall, "counter_top", 4.9, 2.15, 0.22, trim_color, pos=(0, 0, 1.15), unlit=True)
        make_cuboid(stall, "awning", 5.3, 2.45, 0.26, (0.12, 0.06, 0.20, 1), pos=(0, 0, 2.25))
        for offset in [-1.8, -0.9, 0.0, 0.9, 1.8]:
            make_cuboid(stall, f"awning_stripe_{offset}", 0.45, 2.52, 0.30, trim_color, pos=(offset, 0, 2.32), unlit=True)
        make_text(stall, "stall_label", label, (0, -1.22, 2.72), 0.33, trim_color, billboard=True)
        for j in range(4):
            make_sphere(stall, f"display_orb_{j}", 0.22, random.choice([(1, 0.25, 0.55, 1), (0.2, 1, 0.75, 1), (1, 0.82, 0.18, 1)]), pos=(-1.45 + j * 0.95, -0.75, 1.42), unlit=True)

    def create_player_truck(self) -> None:
        truck = self.scene_root.attachNewNode("player_food_truck")
        self.player_np = truck

        # Floating truck body.
        make_cuboid(truck, "truck_body", 2.65, 1.55, 1.05, (0.92, 0.86, 0.74, 1), pos=(0, 0, 0.83))
        make_cuboid(truck, "truck_bottom_trim", 2.78, 1.66, 0.22, (0.05, 0.72, 0.85, 1), pos=(0, 0, 0.32), unlit=True)
        make_cuboid(truck, "truck_orange_nose", 1.18, 0.18, 0.56, (1.0, 0.44, 0.08, 1), pos=(0, 0.86, 0.84), unlit=True)
        make_cuboid(truck, "truck_window", 1.45, 0.08, 0.48, (0.05, 0.20, 0.33, 0.92), pos=(-0.40, 0.84, 1.16), unlit=True)
        make_cuboid(truck, "service_window", 0.08, 0.90, 0.54, (0.04, 0.25, 0.30, 1), pos=(1.36, -0.20, 1.03), unlit=True)
        make_cuboid(truck, "service_counter", 0.22, 1.22, 0.12, (1.0, 0.60, 0.18, 1), pos=(1.50, -0.20, 0.66), unlit=True)

        for i, (x, y) in enumerate([(-1.05, -0.62), (1.05, -0.62), (-1.05, 0.62), (1.05, 0.62)]):
            make_cylinder(truck, f"hover_disk_{i}", 0.34, 0.10, (0.0, 0.95, 1.0, 1), pos=(x, y, 0.05), segments=24, unlit=True)
            make_line_circle(truck, f"hover_ring_{i}", 0.42, (0.0, 1.0, 1.0, 0.70), pos=(x, y, 0.11), thickness=2.0)

        # Headlights and smile-like grille.
        make_sphere(truck, "left_headlight", 0.19, (1.0, 0.83, 0.30, 1), pos=(-0.78, 0.95, 0.62), unlit=True)
        make_sphere(truck, "right_headlight", 0.19, (1.0, 0.83, 0.30, 1), pos=(0.78, 0.95, 0.62), unlit=True)
        make_cuboid(truck, "smile_grille", 1.0, 0.08, 0.09, (0.0, 0.95, 1.0, 1), pos=(0, 1.0, 0.32), unlit=True)

        # Roof sign and carried-order display.
        make_cuboid(truck, "roof_pylon", 0.18, 0.18, 0.56, (0.24, 0.18, 0.32, 1), pos=(0, 0, 1.58))
        make_cuboid(truck, "roof_sign_back", 2.15, 0.16, 0.72, (0.12, 0.04, 0.16, 1), pos=(0, 0, 2.0), unlit=True)
        make_text(truck, "roof_sign_text", "COSMIC\nTRUCK", (0, -0.12, 1.92), 0.26, (1.0, 0.55, 0.12, 1), billboard=True)
        _, self.carry_text = make_text(truck, "carry_text", "CARRY: EMPTY", (0, 0, 2.72), 0.35, (0.35, 1.0, 1.0, 1), billboard=True)

    def create_food_stations(self) -> None:
        station_specs = [
            ("SPACE_TACOS", Vec3(-15, -8, 0), "TACO POD"),
            ("NEBULA_NOODLES", Vec3(-7, -13, 0), "NOODLE NEBULA"),
            ("GALAXY_SODA", Vec3(2, -13, 0), "SODA COMET"),
            ("COMET_CAKE", Vec3(11, -11, 0), "CAKE DOCK"),
            ("MOON_SOUP", Vec3(16, -4, 0), "SOUP MOON"),
            ("GLOW_FRUIT", Vec3(-16, 1, 0), "FRUIT ORBIT"),
        ]
        for item_id, pos, sign in station_specs:
            info = self.food_catalog[item_id]
            station = self.scene_root.attachNewNode(f"station_{item_id}")
            station.setPos(pos)
            color = info["color"]  # type: ignore[index]
            make_line_circle(station, "pickup_radius_neon", 1.95, color, pos=(0, 0, 0.08), thickness=2.8)
            make_cylinder(station, "station_plinth", 1.22, 0.34, (0.12, 0.08, 0.18, 1), pos=(0, 0, 0.17), segments=32)
            make_cuboid(station, "station_counter", 2.25, 1.55, 0.62, (0.16, 0.10, 0.22, 1), pos=(0, 0, 0.72))
            make_cuboid(station, "station_counter_trim", 2.44, 1.72, 0.18, color, pos=(0, 0, 1.08), unlit=True)
            make_cylinder(station, "sign_post", 0.07, 1.65, (0.25, 0.22, 0.35, 1), pos=(-0.98, 0.62, 1.78))
            make_cuboid(station, "station_sign", 2.45, 0.14, 0.58, (0.07, 0.03, 0.12, 1), pos=(0, 0.68, 2.45), unlit=True)
            make_text(station, "station_label", f"{sign}\n{info['short']}", (0, 0.56, 2.35), 0.26, color, billboard=True)
            self.create_food_prop(station, item_id, color)  # type: ignore[arg-type]
            self.food_stations.append(
                FoodStation(item_id=item_id, name=str(info["name"]), short=str(info["short"]), pos=pos, radius=2.05, node=station)
            )

    def create_food_prop(self, parent: NodePath, item_id: str, color: Union[Color, Tuple[float, float, float]]) -> None:
        c = vec4(color)
        if item_id == "SPACE_TACOS":
            make_cylinder(parent, "taco_shell", 0.48, 0.18, (1.0, 0.72, 0.18, 1), pos=(0, -0.06, 1.45), hpr=(0, 90, 0), segments=28, unlit=True)
            for i in range(5):
                make_sphere(parent, f"taco_filling_{i}", 0.12, random.choice([(0.20, 1.0, 0.38, 1), (1.0, 0.24, 0.18, 1), (0.55, 0.22, 0.05, 1)]), pos=(-0.34 + i * 0.17, -0.07, 1.55), unlit=True)
        elif item_id == "NEBULA_NOODLES":
            make_cylinder(parent, "noodle_bowl", 0.55, 0.26, (0.12, 0.55, 0.78, 1), pos=(0, -0.08, 1.36), segments=32)
            for i in range(7):
                make_cuboid(parent, f"noodle_strand_{i}", 0.08, 0.62, 0.06, c, pos=(-0.32 + i * 0.10, -0.08, 1.56), hpr=(random.uniform(-16, 16), 0, random.uniform(-8, 8)), unlit=True)
        elif item_id == "GALAXY_SODA":
            make_cylinder(parent, "soda_cup", 0.36, 0.70, (0.05, 0.22, 0.30, 1), pos=(0, -0.08, 1.50), segments=24)
            make_cylinder(parent, "soda_glow", 0.31, 0.10, c, pos=(0, -0.08, 1.90), segments=24, unlit=True)
            make_cuboid(parent, "soda_straw", 0.06, 0.06, 0.75, (1.0, 0.25, 0.75, 1), pos=(0.18, -0.08, 2.08), hpr=(20, 0, 0), unlit=True)
        elif item_id == "COMET_CAKE":
            make_cuboid(parent, "cake_layer_1", 0.90, 0.70, 0.25, (1.0, 0.76, 0.22, 1), pos=(0, -0.08, 1.34), unlit=True)
            make_cuboid(parent, "cake_layer_2", 0.72, 0.56, 0.25, c, pos=(0, -0.08, 1.62), unlit=True)
            make_sphere(parent, "cake_star", 0.16, (1.0, 1.0, 0.38, 1), pos=(0, -0.08, 1.89), unlit=True)
        elif item_id == "MOON_SOUP":
            make_cylinder(parent, "soup_bowl", 0.55, 0.25, (0.12, 0.72, 0.50, 1), pos=(0, -0.08, 1.35), segments=32)
            make_sphere(parent, "soup_orb", 0.33, c, pos=(0, -0.08, 1.58), unlit=True)
            for i in range(3):
                make_sphere(parent, f"soup_bubble_{i}", 0.08, (0.85, 1.0, 0.75, 1), pos=(-0.18 + i * 0.18, -0.02, 1.88 + 0.08 * i), unlit=True)
        elif item_id == "GLOW_FRUIT":
            for i, (x, y, z) in enumerate([(0, -0.10, 1.42), (-0.25, -0.05, 1.50), (0.25, -0.08, 1.55), (0.05, 0.12, 1.70)]):
                make_sphere(parent, f"fruit_{i}", 0.22, c, pos=(x, y, z), unlit=True)
            make_cuboid(parent, "fruit_crate", 1.0, 0.72, 0.18, (0.35, 0.16, 0.08, 1), pos=(0, -0.08, 1.23))

    def create_customer_spots(self) -> None:
        spot_specs = [
            ("Zorp", Vec3(-13, 9, 0), (0.30, 0.95, 0.42, 1), 0),
            ("Mibble", Vec3(-3, 13, 0), (0.86, 0.30, 1.00, 1), 1),
            ("Gloopi", Vec3(8, 11, 0), (0.15, 0.86, 1.00, 1), 2),
            ("Nara-9", Vec3(15, 5, 0), (1.00, 0.58, 0.22, 1), 3),
        ]
        for index, (name, pos, color, style) in enumerate(spot_specs):
            root = self.scene_root.attachNewNode(f"customer_spot_{index}")
            root.setPos(pos)
            make_line_circle(root, "customer_wait_ring", 1.55, (1.0, 0.38, 1.0, 0.55), pos=(0, 0, 0.06), thickness=2.8)
            make_cylinder(root, "customer_spot_pad", 1.05, 0.13, (0.14, 0.08, 0.20, 1), pos=(0, 0, 0.07), segments=32)
            make_text(root, "spot_name", name, (0, -0.95, 0.35), 0.22, (1.0, 0.88, 0.42, 1), billboard=True)
            alien = root.attachNewNode(f"alien_{name}")
            self.build_alien(alien, style, color)

            order_np, order_text = make_text(root, "order_label", "", (0, 0, 3.15), 0.28, (1, 1, 1, 1), billboard=True)
            feedback_np, feedback_text = make_text(root, "feedback_label", "", (0, 0, 3.85), 0.33, (1, 0.65, 0.2, 1), billboard=True)

            bar_root = root.attachNewNode("patience_bar")
            bar_root.setPos(0, 0, 2.65)
            bar_root.setBillboardPointEye()
            make_cuboid(bar_root, "bar_back", 1.65, 0.08, 0.16, (0.05, 0.03, 0.07, 1), pos=(0, 0, 0), unlit=True)
            bar_fill = make_cuboid(bar_root, "bar_fill", 1.48, 0.10, 0.19, (1.0, 1.0, 1.0, 1), pos=(0, -0.02, 0.01), unlit=True)

            self.customer_spots.append(
                CustomerSpot(
                    index=index,
                    spot_name=name,
                    pos=pos,
                    root=root,
                    alien_node=alien,
                    order_label_np=order_np,
                    order_text=order_text,
                    feedback_label_np=feedback_np,
                    feedback_text=feedback_text,
                    bar_root=bar_root,
                    bar_fill=bar_fill,
                )
            )

    def build_alien(self, parent: NodePath, style: int, color: Color) -> None:
        # Body and head.
        if style == 0:
            make_sphere(parent, "body", 0.62, color, pos=(0, 0, 0.82))
            make_sphere(parent, "head", 0.46, (0.54, 1.0, 0.62, 1), pos=(0, 0, 1.55))
            for i, x in enumerate([-0.23, 0.0, 0.23]):
                make_sphere(parent, f"eye_{i}", 0.08, (0.02, 0.03, 0.05, 1), pos=(x, -0.37, 1.62), unlit=True)
            for i, x in enumerate([-0.28, 0.28]):
                make_cuboid(parent, f"antenna_{i}", 0.06, 0.06, 0.65, (0.34, 1.0, 0.48, 1), pos=(x, 0, 2.10), hpr=(20 if x < 0 else -20, 0, 0), unlit=True)
                make_sphere(parent, f"antenna_tip_{i}", 0.11, (1.0, 0.38, 0.95, 1), pos=(x * 1.35, -0.08, 2.42), unlit=True)
        elif style == 1:
            make_cylinder(parent, "tube_body", 0.42, 1.08, color, pos=(0, 0, 0.88), segments=18)
            make_sphere(parent, "bubble_head", 0.54, (0.96, 0.62, 1.0, 1), pos=(0, 0, 1.68))
            for i, x in enumerate([-0.18, 0.18]):
                make_sphere(parent, f"big_eye_{i}", 0.12, (0.0, 0.04, 0.08, 1), pos=(x, -0.43, 1.73), unlit=True)
                make_sphere(parent, f"pupil_glow_{i}", 0.045, (0.0, 1.0, 1.0, 1), pos=(x + 0.02, -0.52, 1.76), unlit=True)
            for i in range(4):
                angle = i * 90
                make_cuboid(parent, f"little_leg_{i}", 0.10, 0.42, 0.10, color, pos=(0, 0, 0.25), hpr=(angle, 0, 0))
        elif style == 2:
            make_sphere(parent, "squat_body", 0.70, color, pos=(0, 0, 0.72))
            make_sphere(parent, "single_eye", 0.22, (0.02, 0.02, 0.05, 1), pos=(0, -0.57, 1.03), unlit=True)
            make_sphere(parent, "single_eye_glow", 0.08, (0.20, 1.0, 1.0, 1), pos=(0.05, -0.68, 1.08), unlit=True)
            for i in range(5):
                a = -60 + i * 30
                make_cuboid(parent, f"frill_{i}", 0.09, 0.48, 0.12, (1.0, 0.40, 0.95, 1), pos=(0, 0, 1.34), hpr=(a, 0, 0), unlit=True)
        else:
            make_cylinder(parent, "robotic_alien_body", 0.52, 0.88, color, pos=(0, 0, 0.82), segments=6)
            make_cuboid(parent, "square_head", 0.86, 0.62, 0.52, (1.0, 0.70, 0.32, 1), pos=(0, 0, 1.45))
            make_sphere(parent, "eye_left", 0.09, (0.0, 1.0, 1.0, 1), pos=(-0.20, -0.35, 1.50), unlit=True)
            make_sphere(parent, "eye_right", 0.09, (0.0, 1.0, 1.0, 1), pos=(0.20, -0.35, 1.50), unlit=True)
            make_cuboid(parent, "tiny_mouth", 0.36, 0.04, 0.05, (0.08, 0.02, 0.05, 1), pos=(0, -0.35, 1.32), unlit=True)
            make_cylinder(parent, "head_dish", 0.34, 0.07, (0.8, 0.9, 1.0, 1), pos=(0, 0, 1.85), hpr=(0, 68, 0), segments=24, unlit=True)

    def create_hazards(self) -> None:
        # Slippery sauce puddles slow the truck and can spill carried orders.
        for i, (x, y, r) in enumerate([(-4.6, -2.2, 1.85), (9.2, 1.0, 1.65), (-10.8, 3.7, 1.55)]):
            make_cylinder(self.scene_root, f"glowing_sauce_puddle_{i}", r, 0.035, (1.0, 0.26, 0.58, 0.46), pos=(x, y, 0.03), segments=48, unlit=True)
            make_line_circle(self.scene_root, f"sauce_warning_ring_{i}", r, (1.0, 0.24, 0.72, 0.78), pos=(x, y, 0.08), thickness=3)
            make_text(self.scene_root, f"sauce_label_{i}", "SLIPPERY\nSAUCE", (x, y, 0.65), 0.22, (1.0, 0.50, 0.84, 1), billboard=True)
            self.sauce_puddles.append(SauceHazard(pos=Vec3(x, y, 0), radius=r))

        # Conveyor belts shove the truck sideways through the market.
        self.create_conveyor(Vec3(0, -4.4, 0), half_size=(4.8, 1.1), direction=Vec3(1, 0, 0), label="CONVEYOR >>")
        self.create_conveyor(Vec3(5.6, 5.2, 0), half_size=(1.1, 4.2), direction=Vec3(0, -1, 0), label="VORTEX BELT")

        # Moving bots are a third complication: they bounce meals off the cart.
        bot_paths = [
            [Vec3(-16, -1, 0), Vec3(16, -1, 0)],
            [Vec3(12, -7, 0), Vec3(12, 10, 0), Vec3(-8, 10, 0), Vec3(-8, -7, 0)],
        ]
        for i, path in enumerate(bot_paths):
            node = self.scene_root.attachNewNode(f"delivery_bot_{i}")
            node.setPos(path[0])
            self.build_delivery_bot(node, i)
            self.bots.append(DeliveryBot(node=node, path=path, speed=3.0 + i * 0.6))

    def create_conveyor(self, pos: Vec3, half_size: Tuple[float, float], direction: Vec3, label: str) -> None:
        root = self.scene_root.attachNewNode(f"conveyor_{label}")
        root.setPos(pos)
        make_cuboid(root, "conveyor_base", half_size[0] * 2.0, half_size[1] * 2.0, 0.10, (0.07, 0.11, 0.18, 1), pos=(0, 0, 0.03))
        make_cuboid(root, "conveyor_neon_edge", half_size[0] * 2.08, 0.12, 0.13, (0.0, 0.92, 1.0, 1), pos=(0, -half_size[1], 0.11), unlit=True)
        make_cuboid(root, "conveyor_neon_edge_2", half_size[0] * 2.08, 0.12, 0.13, (0.0, 0.92, 1.0, 1), pos=(0, half_size[1], 0.11), unlit=True)
        make_cuboid(root, "conveyor_side_edge", 0.12, half_size[1] * 2.08, 0.13, (1.0, 0.42, 0.10, 1), pos=(-half_size[0], 0, 0.12), unlit=True)
        make_cuboid(root, "conveyor_side_edge_2", 0.12, half_size[1] * 2.08, 0.13, (1.0, 0.42, 0.10, 1), pos=(half_size[0], 0, 0.12), unlit=True)

        # Repeating arrow blocks imply direction without pretending this is a UI design dissertation.
        arrow_color = (1.0, 0.85, 0.15, 1)
        for n in range(-3, 4):
            offset = n * 1.25
            if abs(direction.getX()) > 0:
                make_cuboid(root, f"belt_arrow_body_{n}", 0.68, 0.15, 0.12, arrow_color, pos=(offset, 0, 0.22), unlit=True)
                make_cuboid(root, f"belt_arrow_tip_{n}", 0.30, 0.38, 0.12, arrow_color, pos=(offset + 0.42 * (1 if direction.getX() > 0 else -1), 0, 0.22), hpr=(45, 0, 0), unlit=True)
            else:
                make_cuboid(root, f"belt_arrow_body_{n}", 0.15, 0.68, 0.12, arrow_color, pos=(0, offset, 0.22), unlit=True)
                make_cuboid(root, f"belt_arrow_tip_{n}", 0.38, 0.30, 0.12, arrow_color, pos=(0, offset + 0.42 * (1 if direction.getY() > 0 else -1), 0.22), hpr=(45, 0, 0), unlit=True)
        make_text(root, "conveyor_label", label, (0, 0, 0.75), 0.23, (0.55, 1.0, 1.0, 1), billboard=True)
        self.conveyors.append(ConveyorHazard(pos=pos, half_size=half_size, direction=direction, strength=4.5))

    def build_delivery_bot(self, parent: NodePath, index: int) -> None:
        color = (0.78, 0.82, 0.94, 1) if index == 0 else (0.70, 1.0, 0.66, 1)
        make_cylinder(parent, "bot_hover", 0.45, 0.10, (0.0, 0.95, 1.0, 1), pos=(0, 0, 0.15), segments=24, unlit=True)
        make_sphere(parent, "bot_body", 0.50, color, pos=(0, 0, 0.72))
        make_cuboid(parent, "bot_face", 0.62, 0.09, 0.25, (0.02, 0.05, 0.08, 1), pos=(0, -0.44, 0.78), unlit=True)
        make_sphere(parent, "bot_eye_l", 0.055, (0.0, 1.0, 1.0, 1), pos=(-0.18, -0.50, 0.82), unlit=True)
        make_sphere(parent, "bot_eye_r", 0.055, (0.0, 1.0, 1.0, 1), pos=(0.18, -0.50, 0.82), unlit=True)
        make_cuboid(parent, "bot_antenna", 0.07, 0.07, 0.55, (1.0, 0.35, 0.80, 1), pos=(0, 0, 1.25), unlit=True)
        make_sphere(parent, "bot_antenna_tip", 0.11, (1.0, 0.82, 0.18, 1), pos=(0, 0, 1.58), unlit=True)
        make_text(parent, "bot_label", "DELIVERY\nBOT", (0, 0, 2.05), 0.19, (1.0, 0.75, 0.30, 1), billboard=True)

    def create_hud(self) -> None:
        self.hud_text = OnscreenText(
            text="",
            pos=(-1.32, 0.93),
            scale=0.044,
            fg=(0.86, 1.0, 1.0, 1),
            align=TextNode.ALeft,
            mayChange=True,
        )
        self.orders_text = OnscreenText(
            text="",
            pos=(1.32, 0.93),
            scale=0.039,
            fg=(1.0, 0.90, 0.62, 1),
            align=TextNode.ARight,
            mayChange=True,
        )
        self.prompt_text = OnscreenText(
            text="",
            pos=(0, -0.92),
            scale=0.050,
            fg=(1.0, 1.0, 1.0, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.message_text = OnscreenText(
            text="",
            pos=(0, 0.76),
            scale=0.058,
            fg=(1.0, 0.86, 0.28, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.warning_text = OnscreenText(
            text="",
            pos=(0, 0.65),
            scale=0.046,
            fg=(1.0, 0.38, 0.65, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.end_text = OnscreenText(
            text="",
            pos=(0, 0.10),
            scale=0.083,
            fg=(1.0, 0.94, 0.48, 1),
            align=TextNode.ACenter,
            mayChange=True,
        )
        self.end_text.hide()

    # ---------------------------------------------------------------------
    # Game state
    # ---------------------------------------------------------------------
    def reset_game(self) -> None:
        self.state = "playing"
        self.score = 0
        self.completed_orders = 0
        self.left_customers = 0
        self.round_time = self.round_time_max
        self.carried_order = None
        self.message_timer = 0.0
        self.warning_timer = 0.0
        self.was_in_sauce = False
        self.bot_collision_cooldown = 0.0
        self.player_pos = Vec3(0, -3.2, 0)
        if self.player_np is not None:
            self.player_np.setPos(self.player_pos)
            self.player_np.setH(0)
        self.update_carry_label()
        self.end_text.hide()
        self.message_text.setText("Service started! Load food at a station, then deliver matching orders.")
        self.message_timer = 4.0

        for bot in self.bots:
            bot.node.setPos(bot.path[0])
            bot.target_index = 1 if len(bot.path) > 1 else 0
            bot.hit_cooldown = 0

        for c in self.customer_spots:
            c.active = False
            c.respawn_timer = 0
            c.feedback_timer = 0
            c.order_id = ""
            c.patience = 0
            c.alien_node.hide()
            c.order_label_np.hide()
            c.bar_root.hide()
            c.feedback_text.setText("")
            self.spawn_customer(c)
        self.update_hud()

    def restart_if_finished(self) -> None:
        if self.state != "playing":
            self.reset_game()

    def spawn_customer(self, customer: CustomerSpot) -> None:
        if self.state != "playing":
            return
        order_id = random.choice(list(self.food_catalog.keys()))
        customer.active = True
        customer.order_id = order_id
        customer.max_patience = random.uniform(24.0, 34.0)
        customer.patience = customer.max_patience
        customer.respawn_timer = 0.0
        customer.alien_node.show()
        customer.order_label_np.show()
        customer.bar_root.show()
        customer.feedback_text.setText("")
        customer.feedback_timer = 0.0
        info = self.food_catalog[order_id]
        customer.order_text.setText(f"WANTS\n{info['short']}")
        customer.order_text.setTextColor(1.0, 1.0, 1.0, 1.0)
        self.update_customer_bar(customer)

    def despawn_customer_for_respawn(self, customer: CustomerSpot, delay: float) -> None:
        customer.active = False
        customer.respawn_timer = delay
        customer.order_id = ""
        customer.alien_node.hide()
        customer.order_label_np.hide()
        customer.bar_root.hide()

    def set_customer_feedback(self, customer: CustomerSpot, text: str, color: Color, duration: float = 1.6) -> None:
        customer.feedback_text.setText(text)
        c = vec4(color)
        customer.feedback_text.setTextColor(c[0], c[1], c[2], c[3])
        customer.feedback_timer = duration

    def set_message(self, text: str, duration: float = 2.2) -> None:
        self.message_text.setText(text)
        self.message_timer = duration

    def update_carry_label(self) -> None:
        if self.carry_text is None:
            return
        if self.carried_order is None:
            self.carry_text.setText("CARRY: EMPTY")
            self.carry_text.setTextColor(0.35, 1.0, 1.0, 1)
        else:
            info = self.food_catalog[self.carried_order]
            color = vec4(info["color"])  # type: ignore[arg-type]
            self.carry_text.setText(f"CARRY: {info['short']}")
            self.carry_text.setTextColor(color[0], color[1], color[2], 1)

    def finish_game(self, success: bool, reason: str) -> None:
        if self.state != "playing":
            return
        self.state = "success" if success else "failure"
        if success:
            text = (
                "SERVICE SAVED!\n"
                f"You completed {self.completed_orders}/{self.target_orders} correct orders.\n"
                f"Score: {self.score}\n\n"
                "Press R to replay"
            )
        else:
            text = (
                "SHIFT FAILED!\n"
                f"{reason}\n"
                f"Completed: {self.completed_orders}/{self.target_orders}    Score: {self.score}\n\n"
                "Press R to try again"
            )
        self.end_text.setText(text)
        self.end_text.show()
        self.prompt_text.setText("Press R to restart the round")

    # ---------------------------------------------------------------------
    # Interaction and update loop
    # ---------------------------------------------------------------------
    def try_interact(self) -> None:
        if self.state != "playing":
            return

        nearest_customer = self.get_nearest_active_customer(self.delivery_radius)
        if nearest_customer is not None:
            if self.carried_order is None:
                self.set_message(f"{nearest_customer.spot_name} is waiting. Load the right food first.")
                return
            self.deliver_to_customer(nearest_customer)
            return

        nearest_station = self.get_nearest_station(self.interaction_radius)
        if nearest_station is not None:
            self.carried_order = nearest_station.item_id
            self.update_carry_label()
            self.set_message(f"Loaded {nearest_station.name}. Now find a matching customer!")
            return

        self.set_message("Move close to a food station or alien customer, then press E or SPACE.")

    def get_nearest_station(self, radius: float) -> Optional[FoodStation]:
        best: Optional[FoodStation] = None
        best_dist = radius
        for station in self.food_stations:
            dist = xy_distance(self.player_pos, station.pos)
            if dist <= min(best_dist, station.radius):
                best = station
                best_dist = dist
        return best

    def get_nearest_active_customer(self, radius: float) -> Optional[CustomerSpot]:
        best: Optional[CustomerSpot] = None
        best_dist = radius
        for customer in self.customer_spots:
            if not customer.active:
                continue
            dist = xy_distance(self.player_pos, customer.pos)
            if dist <= best_dist:
                best = customer
                best_dist = dist
        return best

    def deliver_to_customer(self, customer: CustomerSpot) -> None:
        if self.carried_order is None or not customer.active:
            return
        delivered = self.carried_order
        expected = customer.order_id
        delivered_name = str(self.food_catalog[delivered]["short"])
        expected_name = str(self.food_catalog[expected]["short"])
        self.carried_order = None
        self.update_carry_label()

        if delivered == expected:
            time_bonus = int(max(0, customer.patience) * 2)
            points = 100 + time_bonus
            self.score += points
            self.completed_orders += 1
            self.set_customer_feedback(customer, f"YUM! +{points}", (0.35, 1.0, 0.45, 1), 2.0)
            self.set_message(f"Correct delivery: {delivered_name}! +{points} points")
            self.despawn_customer_for_respawn(customer, random.uniform(2.0, 4.4))
            if self.completed_orders >= self.target_orders:
                self.finish_game(True, "Objective complete")
        else:
            self.score -= 30
            customer.patience = max(0.0, customer.patience - 8.0)
            self.set_customer_feedback(customer, f"WRONG!\nWanted {expected_name}", (1.0, 0.23, 0.50, 1), 2.2)
            self.set_message(f"Wrong order. Delivered {delivered_name}, but they wanted {expected_name}. -30 points")
            self.update_customer_bar(customer)
            if customer.patience <= 0:
                self.customer_leaves(customer, reason="Wrong food was the last straw")

    def customer_leaves(self, customer: CustomerSpot, reason: str = "They waited too long") -> None:
        if not customer.active:
            return
        self.left_customers += 1
        self.score -= 45
        self.set_customer_feedback(customer, "LEFT\nHUNGRY", (1.0, 0.18, 0.35, 1), 2.4)
        self.set_message(f"{customer.spot_name} left hungry. {reason}. -45 points")
        self.despawn_customer_for_respawn(customer, random.uniform(3.0, 5.6))
        if self.left_customers >= self.max_left_customers:
            self.finish_game(False, "Too many customers left hungry.")

    def update(self, task: Task) -> int:
        dt = min(self.clock.getDt(), 0.05)
        if self.state == "playing":
            self.round_time -= dt
            if self.round_time <= 0:
                self.round_time = 0
                if self.completed_orders >= self.target_orders:
                    self.finish_game(True, "Round timer ended after objective completion")
                else:
                    self.finish_game(False, "The round timer ran out.")
            self.update_player(dt)
            self.update_hazards(dt)
            self.update_customers(dt)
        else:
            self.update_bots(dt, active_collisions=False)

        self.update_camera(dt)
        self.update_messages(dt)
        self.update_prompt()
        self.update_hud()
        return Task.cont

    def update_player(self, dt: float) -> None:
        dx = 0.0
        dy = 0.0
        if self.keys["forward"]:
            dy += 1.0
        if self.keys["back"]:
            dy -= 1.0
        if self.keys["left"]:
            dx -= 1.0
        if self.keys["right"]:
            dx += 1.0

        length = math.hypot(dx, dy)
        if length > 0:
            dx /= length
            dy /= length

        in_sauce = any(xy_distance(self.player_pos, hazard.pos) <= hazard.radius for hazard in self.sauce_puddles)
        speed_multiplier = 0.50 if in_sauce else 1.0
        if in_sauce:
            self.warning_text.setText("SLIPPERY SAUCE: truck slowed")
            self.warning_timer = 0.25
            if not self.was_in_sauce and self.carried_order is not None and random.random() < 0.35:
                spilled = str(self.food_catalog[self.carried_order]["short"])
                self.carried_order = None
                self.update_carry_label()
                self.set_message(f"Sauce spill! The {spilled} went on a tiny tragic journey.")
        self.was_in_sauce = in_sauce

        speed = 8.0 * speed_multiplier
        if length > 0:
            self.player_pos.setX(self.player_pos.getX() + dx * speed * dt)
            self.player_pos.setY(self.player_pos.getY() + dy * speed * dt)
            # H=0 faces +Y in this model.
            heading = math.degrees(math.atan2(-dx, dy))
            if self.player_np is not None:
                self.player_np.setH(heading)

        # Conveyor belts apply after input, because apparently floor panels have opinions.
        for belt in self.conveyors:
            if (
                abs(self.player_pos.getX() - belt.pos.getX()) <= belt.half_size[0]
                and abs(self.player_pos.getY() - belt.pos.getY()) <= belt.half_size[1]
            ):
                self.player_pos.setX(self.player_pos.getX() + belt.direction.getX() * belt.strength * dt)
                self.player_pos.setY(self.player_pos.getY() + belt.direction.getY() * belt.strength * dt)
                self.warning_text.setText("CONVEYOR BELT: being pushed")
                self.warning_timer = 0.25

        self.player_pos.setX(clamp(self.player_pos.getX(), -self.world_limit, self.world_limit))
        self.player_pos.setY(clamp(self.player_pos.getY(), -self.world_limit, self.world_limit))
        if self.player_np is not None:
            self.player_np.setPos(self.player_pos)

    def update_hazards(self, dt: float) -> None:
        self.update_bots(dt, active_collisions=True)
        if self.warning_timer > 0:
            self.warning_timer -= dt
            if self.warning_timer <= 0:
                self.warning_text.setText("")

    def update_bots(self, dt: float, active_collisions: bool) -> None:
        for bot in self.bots:
            if bot.hit_cooldown > 0:
                bot.hit_cooldown -= dt
            target = bot.path[bot.target_index]
            x_dir, y_dir, distance = xy_direction(bot.node.getPos(), target)
            if distance < 0.18:
                bot.target_index = (bot.target_index + 1) % len(bot.path)
                target = bot.path[bot.target_index]
                x_dir, y_dir, distance = xy_direction(bot.node.getPos(), target)
            bot.node.setX(bot.node.getX() + x_dir * bot.speed * dt)
            bot.node.setY(bot.node.getY() + y_dir * bot.speed * dt)
            if distance > 0.05:
                bot.node.setH(math.degrees(math.atan2(-x_dir, y_dir)))

            if active_collisions and bot.hit_cooldown <= 0 and xy_distance(self.player_pos, bot.node.getPos()) < 1.15:
                bot.hit_cooldown = 1.4
                away_x, away_y, away_len = xy_direction(bot.node.getPos(), self.player_pos)
                if away_len <= 0.01:
                    away_x, away_y = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                self.player_pos.setX(self.player_pos.getX() + away_x * 1.45)
                self.player_pos.setY(self.player_pos.getY() + away_y * 1.45)
                if self.player_np is not None:
                    self.player_np.setPos(self.player_pos)
                if self.carried_order is not None:
                    dropped = str(self.food_catalog[self.carried_order]["short"])
                    self.carried_order = None
                    self.update_carry_label()
                    self.set_message(f"Delivery bot collision! Dropped {dropped}. Machines remain insufferable.")
                else:
                    self.set_message("Delivery bot collision! The truck got bounced.")
                self.warning_text.setText("DELIVERY BOT: collision")
                self.warning_timer = 0.8

    def update_customers(self, dt: float) -> None:
        for customer in self.customer_spots:
            if customer.feedback_timer > 0:
                customer.feedback_timer -= dt
                if customer.feedback_timer <= 0:
                    customer.feedback_text.setText("")

            if customer.active:
                customer.patience -= dt
                self.update_customer_bar(customer)
                if customer.patience <= 0:
                    self.customer_leaves(customer, reason="Patience reached zero")
            else:
                if customer.respawn_timer > 0 and self.state == "playing":
                    customer.respawn_timer -= dt
                    if customer.respawn_timer <= 0:
                        self.spawn_customer(customer)

    def update_customer_bar(self, customer: CustomerSpot) -> None:
        if customer.max_patience <= 0:
            ratio = 0
        else:
            ratio = clamp(customer.patience / customer.max_patience, 0.0, 1.0)
        customer.bar_fill.setScale(max(0.02, ratio), 1.0, 1.0)
        if ratio > 0.58:
            customer.bar_fill.setColorScale(0.24, 1.0, 0.40, 1.0)
        elif ratio > 0.28:
            customer.bar_fill.setColorScale(1.0, 0.82, 0.18, 1.0)
        else:
            customer.bar_fill.setColorScale(1.0, 0.18, 0.32, 1.0)
        if customer.active and customer.order_id:
            info = self.food_catalog[customer.order_id]
            customer.order_text.setText(f"WANTS\n{info['short']}\n{int(max(0, customer.patience))}s")

    def update_messages(self, dt: float) -> None:
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_text.setText("")

    def update_prompt(self) -> None:
        if self.state != "playing":
            self.prompt_text.setText("Press R to restart the round")
            return

        customer = self.get_nearest_active_customer(self.delivery_radius)
        if customer is not None:
            if self.carried_order is None:
                self.prompt_text.setText(f"{customer.spot_name} wants {self.food_catalog[customer.order_id]['short']} - load food first")
            else:
                self.prompt_text.setText(f"Press E/SPACE to deliver {self.food_catalog[self.carried_order]['short']} to {customer.spot_name}")
            return

        station = self.get_nearest_station(self.interaction_radius)
        if station is not None:
            self.prompt_text.setText(f"Press E/SPACE to load {station.short} from {station.name}")
            return

        self.prompt_text.setText("WASD/Arrows move  |  E/SPACE interact  |  R restarts after win/fail")

    def update_hud(self) -> None:
        carried = "EMPTY" if self.carried_order is None else str(self.food_catalog[self.carried_order]["short"])
        time_left = int(math.ceil(self.round_time))
        self.hud_text.setText(
            "COSMIC FOOD TRUCK RUSH\n"
            "Objective: complete 8 correct orders\n"
            f"Score: {self.score}\n"
            f"Completed: {self.completed_orders}/{self.target_orders}\n"
            f"Customers left hungry: {self.left_customers}/{self.max_left_customers}\n"
            f"Round timer: {time_left}s\n"
            f"Carrying: {carried}\n"
            "Hazards: sauce slows/spills, belts push, bots bump"
        )

        order_lines = ["ACTIVE ORDERS"]
        for customer in self.customer_spots:
            if customer.active:
                food = self.food_catalog[customer.order_id]
                patience_pct = int(clamp(customer.patience / customer.max_patience, 0, 1) * 100)
                order_lines.append(f"{customer.spot_name}: {food['short']}  {patience_pct}%")
            else:
                if customer.respawn_timer > 0:
                    order_lines.append(f"{customer.spot_name}: arriving in {int(math.ceil(customer.respawn_timer))}s")
                else:
                    order_lines.append(f"{customer.spot_name}: waiting...")
        self.orders_text.setText("\n".join(order_lines))

    def update_camera(self, dt: float) -> None:
        if self.player_np is None:
            return
        target_pos = Vec3(self.player_pos.getX() * 0.35, self.player_pos.getY() - 31.0, 23.5)
        current = self.camera.getPos()
        lerp = min(1.0, dt * 2.2)
        new_pos = current + (target_pos - current) * lerp
        self.camera.setPos(new_pos)
        self.camera.lookAt(self.player_pos + Vec3(0, 0, 0.85))


if __name__ == "__main__":
    app = CosmicFoodTruckRush()
    app.run()
