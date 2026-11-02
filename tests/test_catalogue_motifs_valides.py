"""Un motif invalide dans le catalogue fait planter toute la recherche : tous doivent compiler."""
import json
import re
import unittest


class MotifsValides(unittest.TestCase):
    def test_tous_les_motifs_compilent(self):
        cat = json.load(open('config/catalogue_documents.json', encoding='utf-8'))
        for path, md in cat.items():
            motifs = list(md.get('motifs') or []) + list(md.get('exclure_motifs') or []) + list(md.get('centrer_motifs') or [])
            motifs += list(md.get('reponse_directe_motifs') or [])
            for r in md.get('reponses_directes') or []:
                motifs += list(r.get('motifs') or [])
            for t in md.get('tutoriels') or []:
                motifs += list(t.get('motifs') or [])
            for m in motifs:
                with self.subTest(path=path, motif=m[:60]):
                    re.compile(m)
