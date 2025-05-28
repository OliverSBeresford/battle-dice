from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import AmbientLight, DirectionalLight, LVector3, LPoint3, TextNode, TransformState, WindowProperties
from panda3d.bullet import BulletWorld, BulletRigidBodyNode, BulletBoxShape
from direct.gui.DirectGui import DirectButton, OnscreenText
#import pybullet as p
import random
import sys
import os

class Dice3DApp(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        # Bird's eye view: camera above, looking straight down
        self.setBackgroundColor(0.1, 0.1, 0.15)
        props = WindowProperties()
        props.setSize(1400, 1000)
        self.win.requestProperties(props)
        self.camera.setPos(0, 0, 30)
        self.camera.setHpr(0, -90, 0)

        # Lighting
        ambient = AmbientLight('ambient')
        ambient.setColor((0.5, 0.5, 0.5, 1))
        self.render.setLight(self.render.attachNewNode(ambient))
        dlight = DirectionalLight('dlight')
        dlight.setColor((0.7, 0.7, 0.7, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        self.render.setLight(dlnp)

        # Physics world
        self.bullet_world = BulletWorld()
        self.bullet_world.setGravity(LVector3(0, 0, -9.81))

        # Floor
        floor_shape = BulletBoxShape(LVector3(8, 8, 0.5))
        floor_node = BulletRigidBodyNode('Floor')
        floor_node.addShape(floor_shape)
        floor_np = self.render.attachNewNode(floor_node)
        floor_np.setPos(0, 0, 0)  # Set Z to 0 so the top of the floor is at z=0.5
        floor_node.setMass(0)
        floor_node.setFriction(2.0)
        floor_node.setRestitution(0.15)
        self.bullet_world.attachRigidBody(floor_node)
        # Add a visible floor quad
        from panda3d.core import CardMaker
        cm = CardMaker('floor-card')
        cm.setFrame(-8, 8, -8, 8)
        floor_card = self.render.attachNewNode(cm.generate())
        floor_card.setPos(0, 0, 0.01)  # Slightly above the physics floor to avoid z-fighting
        floor_card.setHpr(0, 0, 0)
        floor_card.setColor(1, 1, 1, 1)  # White floor
        floor_card.setTransparency(True)
        floor_card.setBin('background', 0)
        floor_card.setDepthWrite(False)

        # Adjust wall positions and sizes to fully enclose the box
        wall_thickness = 1.0  # Thicker walls for better collision
        wall_height = 10
        wall_length = 16
        # Left wall
        left_wall_shape = BulletBoxShape(LVector3(wall_thickness / 2, wall_length / 2, wall_height))
        left_wall_node = BulletRigidBodyNode('LeftWall')
        left_wall_node.addShape(left_wall_shape)
        left_wall_node.setMass(0)
        left_wall_node.setFriction(2.0)
        left_wall_node.setRestitution(0.15)
        left_wall_np = self.render.attachNewNode(left_wall_node)
        left_wall_np.setPos(-8 + wall_thickness / 2, 0, wall_height)
        self.bullet_world.attachRigidBody(left_wall_node)
        # Right wall
        right_wall_shape = BulletBoxShape(LVector3(wall_thickness / 2, wall_length / 2, wall_height))
        right_wall_node = BulletRigidBodyNode('RightWall')
        right_wall_node.addShape(right_wall_shape)
        right_wall_node.setMass(0)
        right_wall_node.setFriction(2.0)
        right_wall_node.setRestitution(0.15)
        right_wall_np = self.render.attachNewNode(right_wall_node)
        right_wall_np.setPos(8 - wall_thickness / 2, 0, wall_height)
        self.bullet_world.attachRigidBody(right_wall_node)
        # Top wall
        top_wall_shape = BulletBoxShape(LVector3(wall_length / 2, wall_thickness / 2, wall_height))
        top_wall_node = BulletRigidBodyNode('TopWall')
        top_wall_node.addShape(top_wall_shape)
        top_wall_node.setMass(0)
        top_wall_node.setFriction(2.0)
        top_wall_node.setRestitution(0.15)
        top_wall_np = self.render.attachNewNode(top_wall_node)
        top_wall_np.setPos(0, 8 - wall_thickness / 2, wall_height)
        self.bullet_world.attachRigidBody(top_wall_node)
        # Bottom wall
        bottom_wall_shape = BulletBoxShape(LVector3(wall_length / 2, wall_thickness / 2, wall_height))
        bottom_wall_node = BulletRigidBodyNode('BottomWall')
        bottom_wall_node.addShape(bottom_wall_shape)
        bottom_wall_node.setMass(0)
        bottom_wall_node.setFriction(2.0)
        bottom_wall_node.setRestitution(0.15)
        bottom_wall_np = self.render.attachNewNode(bottom_wall_node)
        bottom_wall_np.setPos(0, -8 + wall_thickness / 2, wall_height)
        self.bullet_world.attachRigidBody(bottom_wall_node)

        # Dice
        self.dice_types = [6, 6, 6]  # Use cubes for simplicity
        self.dice_nodes = []
        self.dice_models = []
        self.dice_results = [1 for _ in self.dice_types]
        self.selected_dice = set()
        self.rerolls_left = 3

        self.create_dice()

        # GUI
        self.info_text = OnscreenText(text=f"Rerolls left: {self.rerolls_left}", pos=(0, 0.9), scale=0.07, fg=(1,1,1,1))
        self.roll_button = DirectButton(text="Roll Dice", scale=0.07, pos=(0,0,0.8), command=self.roll_dice)
        self.reroll_button = DirectButton(text="Reroll Selected", scale=0.07, pos=(0,0,0.7), command=self.reroll_selected)
        self.reroll_button["state"] = "disabled"

        # Mouse picking
        self.accept("mouse1", self.on_mouse_click)

        # Task for physics update
        self.taskMgr.add(self.update, "update")

    def create_dice(self):
        for i, sides in enumerate(self.dice_types):
            shape = BulletBoxShape(LVector3(0.5, 0.5, 0.5))
            node = BulletRigidBodyNode(f"Dice{i}")
            node.setMass(100.0)
            node.addShape(shape)
            node.setFriction(2.0)
            # Set restitution: less bouncy with each other, more with ground
            node.setRestitution(0.03)  # Default for dice
            np = self.render.attachNewNode(node)
            np.setPos(-2 + i*2, 0, 2)
            self.bullet_world.attachRigidBody(node)
            # Try to load an STL file for the die model, fallback to box if not found
            stl_path = "models/die.stl"
            if os.path.exists(stl_path):
                model = self.loader.loadModel(stl_path)
                # Auto-scale STL so its bounding box fits a 1x1x1 cube (like the default box)
                bounds = model.getTightBounds()
                if bounds is not None:
                    min_pt, max_pt = bounds
                    size = max_pt - min_pt
                    max_dim = max(size[0], size[1], size[2])
                    if max_dim > 0:
                        scale = 1.0 / max_dim
                        model.setScale(scale)
                    else:
                        model.setScale(1)
                else:
                    model.setScale(1)
            else:
                model = self.loader.loadModel("models/box")
                model.setScale(1)
            model.reparentTo(np)
            self.dice_nodes.append(node)
            self.dice_models.append(np)

    def roll_dice(self):
        # All dice spawn close together, but with more spacing
        side = random.choice([-1, 1])
        base_x = side * (8 + random.uniform(0, 2))
        base_y = -6
        for i, node in enumerate(self.dice_nodes):
            # Larger random offset for each die
            x = base_x + random.uniform(-1.2, 1.2)
            y = base_y + random.uniform(-1.2, 1.2)
            node.setTransform(TransformState.makePosHpr(
                LVector3(x, y, 2 + random.uniform(0, 0.3)),
                LVector3(random.uniform(-20, 20), random.uniform(-20, 20), random.uniform(-20, 20))
            ))
            node.clearForces()
            # Always launch horizontally toward center (x=0), with slight upward velocity
            dir_to_center = -side  # If on left, side=-1, so dir_to_center=1 (right); if on right, side=1, so dir_to_center=-1 (left)
            node.setLinearVelocity(LVector3(
                dir_to_center * random.uniform(4, 6),  # always toward center
                random.uniform(3, 6),
                random.uniform(0.3, 1.0)
            ))
            node.setAngularVelocity(LVector3(0, 0, 0))
        self.rerolls_left = 3
        self.selected_dice.clear()
        self.info_text.setText(f"Rerolls left: {self.rerolls_left}")
        self.reroll_button["state"] = "disabled"

    def reroll_selected(self):
        if self.rerolls_left <= 0 or not self.selected_dice:
            return
        side = random.choice([-1, 1])
        base_x = side * (8 + random.uniform(0, 2))
        base_y = -6
        for idx in self.selected_dice:
            x = base_x + random.uniform(-1.2, 1.2)
            y = base_y + random.uniform(-1.2, 1.2)
            node = self.dice_nodes[idx]
            node.setTransform(TransformState.makePosHpr(
                LVector3(x, y, 2 + random.uniform(0, 0.3)),
                LVector3(random.uniform(-20, 20), random.uniform(-20, 20), random.uniform(-20, 20))
            ))
            node.clearForces()
            dir_to_center = -side
            node.setLinearVelocity(LVector3(
                dir_to_center * random.uniform(4, 6),
                random.uniform(3, 6),
                random.uniform(0.3, 1.0)
            ))
            node.setAngularVelocity(LVector3(0, 0, 0))
        self.rerolls_left -= 1
        self.info_text.setText(f"Rerolls left: {self.rerolls_left}")
        self.selected_dice.clear()
        if self.rerolls_left <= 0:
            self.reroll_button["state"] = "disabled"

    def on_mouse_click(self):
        if not self.mouseWatcherNode.hasMouse():
            return
        mpos = self.mouseWatcherNode.getMouse()
        picker_ray = self.camLens.extrude(mpos, LPoint3(), LPoint3())
        from panda3d.core import CollisionRay, CollisionNode, CollisionTraverser, CollisionHandlerQueue
        picker = CollisionRay()
        picker.setFromLens(self.camNode, mpos.getX(), mpos.getY())
        picker_node = CollisionNode('mouseRay')
        picker_node.addSolid(picker)
        picker_np = self.camera.attachNewNode(picker_node)
        handler = CollisionHandlerQueue()
        traverser = CollisionTraverser()
        traverser.addCollider(picker_np, handler)
        for i, np in enumerate(self.dice_models):
            np.setTag("dice", str(i))
        traverser.traverse(self.render)
        if handler.getNumEntries() > 0:
            handler.sortEntries()
            picked = handler.getEntry(0).getIntoNodePath()
            if picked.hasNetTag("dice"):
                idx = int(picked.getNetTag("dice"))
                if idx in self.selected_dice:
                    self.selected_dice.remove(idx)
                    self.dice_models[idx].setColor(1,1,1,1)
                else:
                    self.selected_dice.add(idx)
                    self.dice_models[idx].setColor(0.5,1,0.5,1)
                if self.selected_dice and self.rerolls_left > 0:
                    self.reroll_button["state"] = "normal"
                else:
                    self.reroll_button["state"] = "disabled"
        picker_np.removeNode()

    def update(self, task):
        dt = globalClock.getDt()
        self.bullet_world.doPhysics(dt, 10, 1.0/180.0)
        return task.cont

if __name__ == "__main__":
    app = Dice3DApp()
    app.run()