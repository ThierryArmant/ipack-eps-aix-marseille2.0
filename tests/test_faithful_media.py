import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from exact_source_answer import media_text
from generation_runtime import load_runtime


class FaithfulMediaTests(unittest.TestCase):
    def audit(self, focused):
        return {'exact_extracts': {'display_version': 'exact-focus-v1',
            'focused_passage_ids': focused,
            'selected_sources': [{'id': 'D1', 'passages': [
                {'id': 'D1P1', 'text': 'Action : suivi des lots.'},
                {'id': 'D1P2', 'text': 'Autre opération : https://www.youtube.com/watch?v=qEvM8o5JxIE'},
                {'id': 'D1P3', 'text': 'Tutoriel propre à cette étape : action.mp4'}]}]}}

    def app_videos(self, audit, body):
        tree = ast.parse(Path('app.py').read_text())
        nodes = None
        for parent in ast.walk(tree):
            for field in ('body', 'orelse'):
                siblings = getattr(parent, field, [])
                if not isinstance(siblings, list):
                    continue
                for n, node in enumerate(siblings):
                    if (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name)
                            and t.id == '_texte_medias' for t in node.targets)):
                        nodes = siblings[n:n+3]
        self.assertIsNotNone(nodes)
        state = SimpleNamespace(messages_hub=[])
        env = dict(_generation_runtime=load_runtime(), diagnostic_ia=audit,
                   texte_final=body, VIDEOS_TUTOS={'action.mp4':'https://video.example/action'},
                   st=SimpleNamespace(session_state=state), est_dnb=False, mode='examens', re=re)
        exec(compile(ast.Module(body=nodes, type_ignores=[]), 'app.py', 'exec'), env)
        return [m['content'] for m in state.messages_hub]

    def test_real_app_does_not_promote_media_from_unfocused_context(self):
        audit = self.audit(['D1P1'])
        body = 'Action : suivi des lots.<details>action.mp4 https://www.youtube.com/watch?v=qEvM8o5JxIE</details>'
        self.assertEqual(self.app_videos(audit, body), [])
        self.assertIn('action.mp4', body)  # le contexte documentaire reste intact
        self.assertEqual(audit['exact_extracts']['automatic_media_passage_ids'], ['D1P1'])

    def test_real_app_keeps_video_in_a_selected_passage(self):
        self.assertEqual(self.app_videos(self.audit(['D1P2']), 'Autre contexte'),
                         ['https://www.youtube.com/watch?v=qEvM8o5JxIE'])
        self.assertEqual(self.app_videos(self.audit(['D1P3']), 'Autre contexte'),
                         ['https://video.example/action'])

    def test_normal_and_legacy_full_source_answers_keep_previous_media_behavior(self):
        body = 'https://www.youtube.com/watch?v=qEvM8o5JxIE'
        for audit in [None, {}, {'exact_extracts':{'display_version':'exact-display-v2'}}]:
            self.assertEqual(media_text(audit, body), body)
            self.assertEqual(self.app_videos(audit, body), [body])


if __name__ == '__main__':
    unittest.main()
