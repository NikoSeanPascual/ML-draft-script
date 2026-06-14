import json
import os

COUNTER_MATRIX = {
    "anti_dash": ["dash_heavy", "dive_burst", "dash_heavy_dps"],
    "anti_cc": ["aoe_cc", "burst_cc"],
    "disengage": ["aoe_cc", "dive_burst", "global_engage"],
    "single_pick": ["immobile_scaling", "long_range_sniper", "aoe_channeled"],
    "shredder": ["sustain_frontline", "shield_absorber"],
    "tank_shredder": ["sustain_frontline", "sustain_taunt"],
    "projectile_block": ["dps_poke", "long_range_sniper", "versatile_dps"],
    "anti_heal": ["sustain_frontline", "pocket_buff", "engage_healer"],
    "zone_control": ["immobile_scaling", "aoe_channeled"]
}

THREAT_MATRIX = {
    "immobile_scaling": ["single_pick", "dive_burst", "single_pick_burst"],
    "sustain_frontline": ["tank_shredder", "anti_heal", "shredder"],
    "shield_absorber": ["shredder", "burst_cc"],
    "dash_heavy": ["anti_dash", "single_target_lock"]
}

SYNERGY_MATRIX = {
    "aoe_cc": ["aoe_channeled", "grouped_punisher", "mobile_aoe_dps"],
    "pocket_buff": ["late_scaling_burst", "late_scaling_dps", "attack_speed_scaling", "dash_heavy"],
    "single_pick": ["dive_burst", "single_pick_burst", "cleanup_burst"],
    "global_engage": ["dive_burst", "global_teleport_cc"],
    "damage_sharing_cc": ["early_aoe_burst", "aoe_channeled"]
}


class MLBBDraftEngine:
    def __init__(self, json_path="mlbb_heroes.json"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        full_json_path = os.path.join(base_dir, json_path)

        self.heroes = self._load_heroes(full_json_path)
        self.banned = set()
        self.allies = set()
        self.enemies = set()

    def _load_heroes(self, path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing file: '{path}'")

        with open(path, 'r') as f:
            data = json.load(f)

        flattened_heroes = {}
        for role_group, hero_list in data.items():
            for hero in hero_list:
                flattened_heroes[hero['name'].lower()] = {
                    "name": hero['name'],
                    "primary_role": hero['primary_role'],
                    "secondary_roles": hero.get('secondary_roles', []),
                    "archetype": hero['archetype']
                }
        return flattened_heroes

    def get_hero(self, name):
        return self.heroes.get(name.lower())

    def log_ban(self, name):
        if self.get_hero(name): self.banned.add(name.lower())

    def log_ally(self, name):
        if self.get_hero(name): self.allies.add(name.lower())

    def log_enemy(self, name):
        if self.get_hero(name): self.enemies.add(name.lower())

    def get_filled_roles(self):
        """Returns a set of primary roles already claimed by locked allies."""
        return {self.heroes[ally]['primary_role'] for ally in self.allies if ally in self.heroes}

    def calculate_recommendations(self, target_role=None):
        recommendations = []
        filled_roles = self.get_filled_roles()

        for name, profile in self.heroes.items():
            # Skip if already picked or banned
            if name in self.banned or name in self.allies or name in self.enemies:
                continue

            # UI Filter: Allow selection if target role matches primary OR secondary options
            if target_role:
                if profile['primary_role'] != target_role and target_role not in profile['secondary_roles']:
                    continue

            score = 0.0
            arch = profile['archetype']
            reasons = []

            # ----------------------------------------------------------------
            # 🔄 NEW SMART FLEX ROLE LOGIC
            # ----------------------------------------------------------------
            if profile['primary_role'] in filled_roles:
                # Check if this hero can pivot to an unfilled secondary role
                available_flex = [r for r in profile['secondary_roles'] if r not in filled_roles]

                if available_flex:
                    # Minor penalty for pushing a hero out of their main role, but still highly viable
                    score -= 1.5
                    clean_flex = available_flex[0].replace('_', ' ').title()
                    reasons.append(f"Can flex to open role: {clean_flex}")
                else:
                    # Hard penalty if all their role options are completely filled
                    score -= 10.0
                    reasons.append(f"Role overlap ({profile['primary_role'].replace('_', ' ').title()})")
            # ----------------------------------------------------------------

            # Matchups: Counters Matrix
            for enemy_name in self.enemies:
                if enemy_name in self.heroes:
                    enemy_arch = self.heroes[enemy_name]['archetype']
                    if arch in COUNTER_MATRIX and enemy_arch in COUNTER_MATRIX[arch]:
                        score += 3.0
                        reasons.append(f"Counters {self.heroes[enemy_name]['name']}")

            # Matchups: Threat Matrix (Weaknesses)
            for enemy_name in self.enemies:
                if enemy_name in self.heroes:
                    enemy_arch = self.heroes[enemy_name]['archetype']
                    if arch in THREAT_MATRIX and enemy_arch in THREAT_MATRIX[arch]:
                        score -= 4.0
                        reasons.append(f"Weak against {self.heroes[enemy_name]['name']}")

            # Synergy Matrix
            for ally_name in self.allies:
                if ally_name in self.heroes:
                    ally_arch = self.heroes[ally_name]['archetype']
                    if arch in SYNERGY_MATRIX and ally_arch in SYNERGY_MATRIX[arch]:
                        score += 1.5
                        reasons.append(f"Synergizes with {self.heroes[ally_name]['name']}")
                    elif ally_arch in SYNERGY_MATRIX and arch in SYNERGY_MATRIX[ally_arch]:
                        score += 1.5
                        reasons.append(f"Synergizes with {self.heroes[ally_name]['name']}")

            recommendations.append({
                "name": profile['name'],
                "primary_role": profile['primary_role'],
                "secondary_roles": profile['secondary_roles'],
                "archetype": arch,
                "score": score,
                "reasons": reasons
            })

        return sorted(recommendations, key=lambda x: x['score'], reverse=True)
