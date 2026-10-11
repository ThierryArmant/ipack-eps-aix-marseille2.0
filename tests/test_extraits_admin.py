import unittest
from pathlib import Path


class ExtraitsAdminTests(unittest.TestCase):
    """Les passages transmis à l'IA ne s'affichent qu'en mode admin."""

    def test_extraits_reserves_admin(self):
        code = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
        self.assertIn('if m.get("extraits") and st.session_state.get("is_admin", False):', code)
        self.assertIn('"extraits": extraits_doc if origine_reponse == "ia" and st.session_state.get("is_admin", False) else ""', code)


if __name__ == '__main__':
    unittest.main()
