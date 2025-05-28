import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPointF
from PyQt5.QtGui import QPixmap, QFont, QPainter, QPen, QBrush, QColor, QPolygonF
import pymunk
import pymunk.pygame_util
import os

class BattleDiceGUI(QMainWindow):
    def __init__(self, dice_types=[4, 8, 12], target=14, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Battle Dice - GUI Edition")
        self.setGeometry(100, 100, 900, 700)
        self.dice_types = dice_types
        self.target = target
        self.dice_bodies = []
        self.dice_graphics = []
        self.dice_results = [1 for _ in dice_types]
        self.selected_dice = set()
        self.rerolls_left = 3
        self.init_ui()
        self.init_physics()

    def init_ui(self):
        # Main widget and layout
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.vbox = QVBoxLayout(self.central)

        # Info label
        self.info_label = QLabel(f"Target: {self.target} | Rerolls left: {self.rerolls_left}")
        self.info_label.setFont(QFont('Arial', 16))
        self.vbox.addWidget(self.info_label)

        # Graphics view for dice
        self.scene = QGraphicsScene(0, 0, 800, 400)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.vbox.addWidget(self.view)

        # Buttons (must be defined before dice for event handler)
        self.button_box = QHBoxLayout()
        self.roll_button = QPushButton("Roll Dice")
        self.roll_button.clicked.connect(self.roll_dice)
        self.button_box.addWidget(self.roll_button)
        self.reroll_button = QPushButton("Reroll Selected")
        self.reroll_button.clicked.connect(self.reroll_selected)
        self.reroll_button.setEnabled(False)
        self.button_box.addWidget(self.reroll_button)
        self.vbox.addLayout(self.button_box)

        # Dice shapes by sides
        self.dice_labels = []
        self.dice_items = []
        for i, sides in enumerate(self.dice_types):
            points = self._regular_polygon_points(sides, 30, QPointF(30, 30))
            polygon = QPolygonF(points)
            item = QGraphicsPolygonItem(polygon)
            item.setBrush(QBrush(Qt.white))
            item.setPen(QPen(Qt.black, 2))
            item.setPos(100 + i*200, 170)
            item.setFlag(QGraphicsPolygonItem.ItemIsSelectable, True)
            item.setData(0, i)  # store index
            item.setZValue(1)
            self.scene.addItem(item)
            self.dice_items.append(item)
            label = QLabel(f"d{sides}: ?")
            label.setFont(QFont('Arial', 14))
            self.vbox.addWidget(label)
            self.dice_labels.append(label)
        self.view.show()
        self.scene.mousePressEvent = self.handle_dice_click

    def _regular_polygon_points(self, sides, radius, center):
        from math import pi, cos, sin
        points = []
        for i in range(sides):
            angle = 2 * pi * i / sides - pi/2
            x = center.x() + radius * cos(angle)
            y = center.y() + radius * sin(angle)
            points.append(QPointF(x, y))
        return points

    def handle_dice_click(self, event):
        pos = event.scenePos()
        any_change = False
        for i, item in enumerate(self.dice_items):
            if item.contains(item.mapFromScene(pos)):
                if i in self.selected_dice:
                    self.selected_dice.remove(i)
                    item.setBrush(QBrush(Qt.white))
                else:
                    self.selected_dice.add(i)
                    item.setBrush(QBrush(QColor(200, 255, 200)))
                any_change = True
        self.scene.update()
        # Enable reroll button if at least one die is selected and rerolls are left
        if self.rerolls_left > 0 and len(self.selected_dice) > 0:
            self.reroll_button.setEnabled(True)
        else:
            self.reroll_button.setEnabled(False)
        QGraphicsScene.mousePressEvent(self.scene, event)

    def init_physics(self):
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 900.0)
        # Add floor (ground)
        floor = pymunk.Segment(self.space.static_body, (0, 390), (800, 390), 5)
        floor.friction = 0.8
        floor.elasticity = 0.6  # Make ground bouncy
        self.space.add(floor)
        # Add left wall
        left_wall = pymunk.Segment(self.space.static_body, (0, 0), (0, 400), 5)
        left_wall.friction = 0.8
        left_wall.elasticity = 0.6
        self.space.add(left_wall)
        # Add right wall
        right_wall = pymunk.Segment(self.space.static_body, (800, 0), (800, 400), 5)
        right_wall.friction = 0.8
        right_wall.elasticity = 0.6
        self.space.add(right_wall)

    def roll_dice(self):
        self.clear_dice()
        self.dice_bodies = []
        self.dice_results = []
        for i, sides in enumerate(self.dice_types):
            body = pymunk.Body(1, pymunk.moment_for_box(1, (60, 60)))
            x = 150 + i*200 + random.randint(-20, 20)
            y = 50
            body.position = (x, y)
            body.angle = random.uniform(0, 3.14)
            # Give dice a strong upward and sideways impulse for bounciness
            body.apply_impulse_at_local_point((random.uniform(-120, 120), random.uniform(350, 500)))
            shape = pymunk.Poly.create_box(body, (60, 60))
            shape.friction = 0.9
            shape.elasticity = 0.5  # More realistic bounce
            shape.collision_type = 1
            shape.filter = pymunk.ShapeFilter(group=1)
            self.space.add(body, shape)
            self.dice_bodies.append((body, sides))
        # Add top wall to prevent dice from going off the top
        if not hasattr(self, 'top_wall'):
            self.top_wall = pymunk.Segment(self.space.static_body, (0, 0), (800, 0), 5)
            self.top_wall.friction = 0.8
            self.top_wall.elasticity = 0.5
            self.space.add(self.top_wall)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)
        self.roll_button.setEnabled(False)
        self.reroll_button.setEnabled(False)
        self.info_label.setText(f"Rolling... Target: {self.target}")

    def update_physics(self):
        self.space.step(1/60.0)
        for i, (body, sides) in enumerate(self.dice_bodies):
            # Clamp dice to stay within the screen horizontally
            if body.position.x < 30:
                body.position = (30, body.position.y)
                body.velocity = (abs(body.velocity.x), body.velocity.y)
            elif body.position.x > 770:
                body.position = (770, body.position.y)
                body.velocity = (-abs(body.velocity.x), body.velocity.y)
            # Clamp dice to stay within the screen vertically
            if body.position.y < 30:
                body.position = (body.position.x, 30)
                body.velocity = (body.velocity.x, abs(body.velocity.y))
            pos = body.position
            self.dice_items[i].setPos(pos.x, pos.y)
            self.dice_items[i].setRotation(body.angle * 180 / 3.14159)
        # Only stop if all dice are on the ground (not wall) and moving slowly
        def is_on_ground(body):
            # Consider on ground if y is near floor and not near left/right wall
            return body.position.y > 370 and 30 < body.position.x < 770
        if all(is_on_ground(body) and abs(body.velocity.y) < 5 and abs(body.velocity.x) < 5 for body, _ in self.dice_bodies):
            self.timer.stop()
            self.show_dice_results()

    def show_dice_results(self):
        # Assign random value for each die (simulate physics result)
        self.dice_results = []  # Reset to correct length
        for i, (body, sides) in enumerate(self.dice_bodies):
            val = random.randint(1, sides)
            self.dice_results.append(val)
            self.dice_labels[i].setText(f"d{sides}: {val}")
            # Highlight selection state
            if i in self.selected_dice:
                self.dice_items[i].setBrush(QBrush(QColor(200, 255, 200)))
            else:
                self.dice_items[i].setBrush(QBrush(Qt.white))
        self.info_label.setText(f"Target: {self.target} | Rerolls left: {self.rerolls_left}")
        self.reroll_button.setEnabled(True)
        for item in self.dice_items:
            item.setEnabled(True)
            item.setOpacity(1.0)
            item.setAcceptedMouseButtons(Qt.LeftButton)
        self.scene.update()
        self.view.centerOn(self.dice_items[1])

    def reroll_selected(self):
        if self.rerolls_left <= 0 or not self.selected_dice:
            QMessageBox.information(self, "No rerolls", "No rerolls left or no dice selected.")
            return
        if len(self.dice_results) != len(self.dice_types):
            self.dice_results = [1 for _ in self.dice_types]
        for idx in self.selected_dice:
            body, sides = self.dice_bodies[idx]
            # Respawn die at top and give new momentum
            body.position = (150 + idx*200 + random.randint(-20, 20), 50)
            body.velocity = (0, 0)
            body.angle = random.uniform(0, 3.14)
            body.angular_velocity = random.uniform(-5, 5)
            body.apply_impulse_at_local_point((random.uniform(-120, 120), random.uniform(350, 500)))
        self.rerolls_left -= 1
        self.info_label.setText(f"Target: {self.target} | Rerolls left: {self.rerolls_left}")
        self.selected_dice.clear()
        for item in self.dice_items:
            item.setOpacity(1.0)
        self.reroll_button.setEnabled(False)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_physics)
        self.timer.start(16)

    def clear_dice(self):
        for item in self.dice_items:
            item.setPos(100 + self.dice_items.index(item)*200, 170)
            item.setRotation(0)
        self.dice_results = [1 for _ in self.dice_types]
        for label, sides in zip(self.dice_labels, self.dice_types):
            label.setText(f"d{sides}: ?")
        self.selected_dice.clear()

    # Add more methods for full game integration as needed

# To run standalone for testing:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BattleDiceGUI()
    gui.show()
    sys.exit(app.exec_())
