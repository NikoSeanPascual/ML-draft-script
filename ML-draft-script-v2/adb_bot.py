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

        self.coords_pct = {
            "search_bar": (0.26, 0.14),
            "first_hero_slot": (0.13, 0.28),
            "confirm_button": (0.85, 0.88)
        }

        # Bounding boxes for tracking enemy draft picks
        self.enemy_slots_pct = [
            (0.88, 0.15, 0.96, 0.25),
            (0.88, 0.27, 0.96, 0.37),
            (0.88, 0.39, 0.96, 0.49),
            (0.88, 0.51, 0.96, 0.61),
            (0.88, 0.63, 0.96, 0.73),
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

                if template is None or template.shape[0] > gray_slot.shape[0] or template.shape[1] > gray_slot.shape[1]:
                    continue

                res = cv2.matchTemplate(gray_slot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, _ = cv2.minMaxLoc(res)

                if max_val >= 0.82:  # Slight adjustment for varying screen resolutions
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
