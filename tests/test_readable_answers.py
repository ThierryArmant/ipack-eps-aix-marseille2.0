import html
import re
import unittest
from short_answer import readable_text


class ReadableAnswersTests(unittest.TestCase):
    def test_formatting_preserves_all_text_including_condition_and_reserved_tokens(self):
        examples=[
            'Si le dossier est validé, ouvrez [EPS] > [Dossier] ; prévenez le service avant transfert.',
            'À vérifier : https://exemple.fr/a;b et « ne pas supprimer ; attendre » ; gardez 4,5.',
            'Si seuls quelques élèves sont concernés, ne rien supprimer. <script>alerte</script>',
            'Aucune procédure ne confirme ce dépôt.\nContactez votre service.']
        for text in examples:
            rendered=readable_text(text)
            original=html.unescape(re.sub(r'</?strong>|<br>','',rendered))
            self.assertEqual(original,text)
            self.assertNotIn('<script>',rendered)

    def test_condition_and_menu_are_visible_without_breaking_a_menu_path(self):
        out=readable_text('Si le dossier est validé, ouvrez [EPS] > [Dossier] ; enregistrez.')
        self.assertIn('<strong>Si le dossier est validé,</strong><br>',out)
        self.assertIn('<strong>[EPS]</strong> &gt; <strong>[Dossier]</strong>',out)
        self.assertIn(';<br>',out)


if __name__=='__main__':unittest.main()
