import sys
sys.path.insert(0, '/home/ubuntu/aarkaai3b')
from skills.skill_registry import SkillRegistry

reg = SkillRegistry('/home/ubuntu/aarkaai3b/skills')
skills = reg.list_skills()
print("=== LOADED SKILLS ===")
for s in skills:
    print(f"- {s['name']} (is_core: {s['is_core']}) - {s['description']}")
