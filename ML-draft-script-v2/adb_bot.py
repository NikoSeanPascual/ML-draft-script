import subprocess
import time
import os
import cv2
import numpy as np
import json
from engine import MLBBDraftEngine


class MLBBHardwareBot:
    def __init__(self):
        self.engine = MLBBDraftEngine()
        self.templates_dir = "templates"
        self.state_file = "draft_state.json"  # Shared state handler
        self.screen_width = 1920
        self.screen_height = 1080
        self._calibrate_screen_resolution()

        # Exact percentage scales matching the Tecno Spark 6 (20.5:9 ratio)
        self.coords_pct = {
            "search_bar": (0.34, 0.14),  # Pushed inward slightly more due to the narrow screen height
            "first_hero_slot": (0.18, 0.28),  # Shifted right to catch the first hero grid icon cleanly
            "confirm_button": (0.80, 0.88)  # Shifted left away from the edge bezel zone
        }

        # The 5 Enemy Slots tracking boxes
        # On a 20.5:9 screen, the draft portrait slots sit cleanly between 82% and 90% of your screen width
        self.enemy_slots_pct = [
            (0.82, 0.15, 0.90, 0.25),  # Slot 1 Bounding Box
            (0.82, 0.27, 0.90, 0.37),  # Slot 2 Bounding Box
            (0.82, 0.39, 0.90, 0.49),  # Slot 3 Bounding Box
            (0.82, 0.51, 0.90, 0.61),  # Slot 4 Bounding Box
            (0.82, 0.63, 0.90, 0.73),  # Slot 5 Bounding Box
        ]

    def _execute_adb(self, command):
        result = subprocess.run(f"adb shell {command}", shell=True, capture_output=True, text=True)
        return result.stdout

    def _calibrate_screen_resolution(self):
        print("📱 Calibrating device screen metrics...")
        output = self._execute_adb("wm size")
        if "Physical size:" in output:
            size_str = output.split(":")[-1].strip()
            w, h = map(int, size_str.split("x"))
            self.screen_width = max(w, h)
            self.screen_height = min(w, h)
            print(f"✅ Screen resolution successfully mapped to: {self.screen_width}x{self.screen_height}")
        else:
            print("⚠️ ADB device info not found. Defaulting to standard 1080p landscape canvas.")

    def get_real_coords(self, key):
        pct_x, pct_y = self.coords_pct[key]
        return int(pct_x * self.screen_width), int(pct_y * self.screen_height)

    def capture_frame(self):
        """Uses exec-out to securely pipe image frames without character carriage corruption."""
        pipe = subprocess.Popen("adb exec-out screencap -p", shell=True, stdout=subprocess.PIPE)
        image_bytes = pipe.stdout.read()
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        if image_array.size == 0:
            return None
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    def send_device_tap(self, key):
        x, y = self.get_real_coords(key)
        self._execute_adb(f"input tap {x} {y}")
        time.sleep(0.4)

    def send_device_text(self, text):
        safe_text = text.replace(" ", "%s")
        self._execute_adb(f"input text {safe_text}")
        time.sleep(0.6)

    def scan_slots_for_heroes(self, frame):
        if frame is None or not os.path.exists(self.templates_dir):
            return []

        detected_this_tick = []

        for idx, slot in enumerate(self.enemy_slots_pct):
            x1, y1 = int(slot[0] * self.screen_width), int(slot[1] * self.screen_height)
            x2, y2 = int(slot[2] * self.screen_width), int(slot[3] * self.screen_height)

            cropped_slot = frame[y1:y2, x1:x2]
            gray_slot = cv2.cvtColor(cropped_slot, cv2.COLOR_BGR2GRAY)

            for file in os.listdir(self.templates_dir):
                if not file.endswith('.png'):
                    continue

                template_path = os.path.join(self.templates_dir, file)
                template = cv2.imread(template_path, 0)

                if template is None:
                    continue

                slot_h, slot_w = gray_slot.shape[:2]
                temp_h, temp_w = template.shape[:2]

                if temp_h > slot_h or temp_w > slot_w:
                    # Scale the template down to fit comfortably inside the slot (e.g., matching the slot's height)
                    scale_factor = (slot_h - 4) / temp_h  # Leave a tiny 4-pixel buffer margin
                    new_w = int(temp_w * scale_factor)
                    new_h = int(temp_h * scale_factor)

                    # Double safety check to ensure it doesn't exceed width limits either
                    if new_w > slot_w:
                        scale_factor = (slot_w - 4) / temp_w
                        new_w = int(temp_w * scale_factor)
                        new_h = int(temp_h * scale_factor)

                    template = cv2.resize(template, (new_w, new_h), interpolation=cv2.INTER_AREA)

                res = cv2.matchTemplate(gray_slot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)

                if max_val >= 0.75:  # Lowered slightly from 0.82 to account for resolution stretching distortion
                    hero_name = file.replace('.png', '').lower()
                    detected_this_tick.append(hero_name)
                    break

        return detected_this_tick

    def _sync_state_to_file(self):
        """Saves current engine state so Streamlit can read data changes instantly."""
        state = {
            "enemies": list(self.engine.enemies),
            "allies": list(self.engine.allies),
            "banned": list(self.engine.banned)
        }
        with open(self.state_file, "w") as f:
            json.dump(state, f)

    def perform_auto_pick(self, hero_name):
        print(f"⚡ Command sequence triggered: Autolocking {hero_name.upper()}...")
        self.send_device_tap("search_bar")
        self.send_device_text(hero_name)
        self.send_device_tap("first_hero_slot")
        self.send_device_tap("confirm_button")
        print(f"🎯 Choice successfully locked over hardware abstraction tier!")

        # Log our pick locally and sync
        self.engine.log_ally(hero_name)
        self._sync_state_to_file()

    def start_monitoring_loop(self):
        print("\n🚀 System initialized and operational. Ready for draft lobby...")
        my_pick_completed = False

        while not my_pick_completed:
            frame = self.capture_frame()
            if frame is None:
                print("❌ Communication break: Check USB debugging connection.")
                time.sleep(2)
                continue

            current_visible_enemies = self.scan_slots_for_heroes(frame)

            new_enemy_found = False
            for enemy in current_visible_enemies:
                if enemy not in self.engine.enemies:
                    print(f"🔍 CV Discovery: New enemy locked in draft -> {enemy.title()}")
                    self.engine.log_enemy(enemy)
                    new_enemy_found = True

            if new_enemy_found:
                self._sync_state_to_file()  # Alert Streamlit UI
                best_picks = self.engine.calculate_recommendations()

                if best_picks:
                    top_recommendation = best_picks[0]['name']
                    score = best_picks[0]['score']
                    print(f"💡 Suggestion Matrix: {top_recommendation} ({score} pts)")

                    # 🚀 AUTOMATION ASSIGNMENT:
                    # If you want the bot to instantly auto-lock the top recommendation when it's your turn:
                    # In a real loop, you would check a pixel color to see if the "Select" button is glowing active.
                    # For testing, we can simulate an automatic pick trigger:
                    if len(self.engine.enemies) >= 1 and not self.engine.allies:
                        self.perform_auto_pick(top_recommendation)
                        my_pick_completed = True  # Gracefully exits the loop after locking your pick

            time.sleep(1.0)


if __name__ == "__main__":
    bot = MLBBHardwareBot()
    bot.start_monitoring_loop()
