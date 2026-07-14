import unittest
import sys
import os
from pathlib import Path

# Append project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.aarkaa_engine import _get_model, request_domain, _gguf_coder_path
import gguf

class TestCoderRouting(unittest.TestCase):
    def test_gguf_coder_readable(self):
        # 1. Verify file exists on disk
        self.assertTrue(Path(_gguf_coder_path).exists(), f"Coder GGUF model not found at {_gguf_coder_path}")
        
        # 2. Verify it is a valid GGUF file
        try:
            reader = gguf.GGUFReader(str(_gguf_coder_path))
            arch = reader.fields.get('general.architecture')
            print(f"Verified Coder GGUF. Architecture: {arch}, Tensors: {len(reader.tensors)}")
            self.assertIsNotNone(arch)
        except Exception as e:
            self.fail(f"Failed to read Coder GGUF: {e}")

    def test_routing_by_context(self):
        import modules.aarkaa_engine as engine
        engine._is_stub = False
        # Set candidate gguf path
        for cand in engine._GGUF_CANDIDATES:
            if cand.exists():
                engine._gguf_file_path = cand
                break

        # By default, domain is 'general' which should load the base model
        request_domain.set("general")
        model = _get_model(force_gpu=True)
        self.assertIsNotNone(model)
        # Check that it is NOT the coder model (we'll check via lazy loading logs or instance caching)
        
        # Now set domain to 'technology' (coding)
        request_domain.set("technology")
        coder_model = _get_model(force_gpu=True)
        self.assertIsNotNone(coder_model)
        self.assertNotEqual(id(model), id(coder_model), "Base model and coder model should be separate instances")

if __name__ == "__main__":
    unittest.main()
