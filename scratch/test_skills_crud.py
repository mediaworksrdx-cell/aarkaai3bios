import sys
import os
import shutil

# Make sure we can import from workspace root
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from skills.skill_registry import SkillRegistry
from modules.tools.skill_tools import init_skill_registry, get_registry
from modules.tools import registry

def test_skills_crud():
    skills_dir = os.path.abspath(os.path.dirname(__file__) + "/../skills")
    reg = init_skill_registry(skills_dir)
    
    print("Core skills check:")
    print("Is pdf a core skill?", "pdf" in reg.CORE_SKILLS)
    
    test_skill_content = """---
name: test-temp-skill
description: A temporary skill for automated unit tests.
---
# Temp Skill
This is a test skill.
"""

    print("\n1. Testing ValidateSkillTool logic...")
    is_valid, msg = reg.validate_skill_content(test_skill_content)
    print("Validate result:", is_valid, msg)
    assert is_valid == True
    
    # Try invalid
    invalid_content = "Not frontmatter"
    is_valid_inv, msg_inv = reg.validate_skill_content(invalid_content)
    print("Validate invalid result:", is_valid_inv, msg_inv)
    assert is_valid_inv == False

    print("\n2. Testing CreateSkillTool logic...")
    res = reg.create_skill("test-temp-skill", test_skill_content)
    print("Create result:", res)
    assert "success" in res.lower()
    
    # Verify file was created
    skill_file_path = os.path.join(skills_dir, "user-skills", "default_user", "test-temp-skill", "SKILL.md")
    print("Skill file exists?", os.path.exists(skill_file_path))
    assert os.path.exists(skill_file_path)

    print("\n3. Testing UpdateSkillTool logic...")
    updated_content = """---
name: test-temp-skill
description: Updated description for temp skill.
---
# Temp Skill Updated
This is an updated test skill.
"""
    res = reg.update_skill("test-temp-skill", updated_content)
    print("Update result:", res)
    assert "success" in res.lower()
    
    # Try updating a core skill
    res_core_up = reg.update_skill("pdf", updated_content)
    print("Update core skill result:", res_core_up)
    assert "error" in res_core_up.lower()

    print("\n4. Testing DeleteSkillTool logic...")
    res = reg.delete_skill("test-temp-skill")
    print("Delete result:", res)
    assert "success" in res.lower()
    assert not os.path.exists(skill_file_path)

    # Try deleting a core skill
    res_core_del = reg.delete_skill("pdf")
    print("Delete core skill result:", res_core_del)
    assert "error" in res_core_del.lower()

    print("\nAll Skill CRUD checks passed successfully!")

if __name__ == "__main__":
    test_skills_crud()
