import unittest
from pathlib import Path
from documentary_review import source_packets, mark_excerpt
from source_scope import select_academy

class AlbertFiveCorrections(unittest.TestCase):
    def test_distribution_and_notification_are_distinct_evidence_units(self):
        path='data/ipack/fiches/ipack_102_4_erreurs_de_distribution_et_distribution_manuelle.txt'
        packets=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        manual=next(s['text'] for s in packets[0]['passages'] if s['text'].startswith('Procédure distincte'))
        notice=next(s['text'] for s in packets[0]['passages'] if s['text'].startswith('Opération après distribution'))
        self.assertIn('[Distribution manuelle]',manual)
        self.assertIn('[Ajouter dans un nouveau lot]',manual)
        self.assertNotIn('notification',manual)
        self.assertIn('notification',notice)
        self.assertNotIn('[Ajouter dans un nouveau lot]',notice)

    def test_shared_procedure_not_marked_unconfirmed_for_besancon(self):
        path='data/examens/complement_cyclades_protocoles_cas_enseignant.txt'
        packets=source_packets(mark_excerpt(Path(path).read_text(),path=path))
        selected,_=select_academy(packets,'Besançon')
        span=next(s for s in selected[0]['passages'] if s['text'].startswith("- C'est le chef d'établissement qui réaffecte"))
        self.assertEqual(span['scope']['nature'],['logiciel'])
        self.assertNotIn('not_confirmed_for',span['scope'])
        # Les retours locaux sur les protocoles adaptés gardent leur portée propre.
        local=next(s for s in selected[0]['passages'] if s['text'].startswith('À Aix-Marseille, le responsable SAV'))
        self.assertIn('not_confirmed_for',local['scope'])

    def test_export_copies_keep_habilitation_limit_without_granting_new_right(self):
        for path in ('data/examens/santorin_cas_pratiques/08_extraire_les_notes_saisies_dans_santorin.txt',
                     'data/examens/complement_saisie_santorin_cas_pratiques.txt'):
            text=Path(path).read_text()
            self.assertIn('Un enseignant ne peut extraire que ses propres notes',text)
            self.assertIn('référent établissement Santorin',text)
            self.assertIn('ne précise pas si tout autre rôle',text)
