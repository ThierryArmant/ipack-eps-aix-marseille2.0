"""Régressions issues des formulations observées dans le rejeu."""
import unittest
from claim_guards import unsupported_certainty

class DocumentarySilenceTests(unittest.TestCase):

    def test_absence_de_signature_ne_prouve_pas_une_interdiction(self):
        proof = ["Les sources ne prévoient pas de signature des familles."]
        assert unsupported_certainty("Les familles ne doivent pas signer le document.", proof)
        assert unsupported_certainty("Les familles ne doivent pas signer.", ["Aucun texte des sources ne prévoit de faire signer les familles."])
        assert not unsupported_certainty("Les sources ne prévoient pas de signature des familles.", proof)
        assert not unsupported_certainty("Demandez confirmation au service des examens.", proof)
    
    def test_absence_documentaire_ne_prouve_pas_absence_autorisation(self):
        proof = ["Les sources de cette fiche ne prévoient pas d'autorisation générale de la mairie."]
        assert unsupported_certainty("Il n'existe pas d'autorisation générale de la mairie.", proof)
        assert not unsupported_certainty("Vérifiez les règles d'usage auprès du gestionnaire du parc.", proof)
    
    def test_prescription_explicite_reste_utilisable(self):
        assert not unsupported_certainty("Les familles doivent signer.", ["Les familles doivent signer."])


class ForeignSchoolScopeTests(unittest.TestCase):
    def test_local_procedures_are_marked_outside_aix(self):
        from source_scope import scoped_segments, select_academy
        path = 'data/ipack/courriels_aix_2026_10_14/etablissement_etranger_compte_professeur_sans_eleves.txt'
        from pathlib import Path
        spans = scoped_segments(path, Path(path).read_text())
        selected, _ = select_academy([{'id':'D1', 'passages':[dict(s, id=str(i)) for i,s in enumerate(spans)]}], 'Créteil')
        for fragment in ("seul un accès", "à 100 %", "Cyclades soit fermé"):
            passage = next(p for p in selected[0]['passages'] if fragment in p['text'])
            self.assertEqual(passage['scope']['nature'], ['consigne_academique'])
            self.assertEqual(passage['scope']['not_confirmed_for'], 'Créteil')
        selected, _ = select_academy([{'id':'D1', 'passages':[dict(s,id=str(i)) for i,s in enumerate(spans)]}], 'Aix-Marseille')
        self.assertFalse(any(p['scope'].get('not_confirmed_for') for p in selected[0]['passages']))


class PersonalComputerFocusTests(unittest.TestCase):
    def test_personal_computer_focus_does_not_assume_a_symptom(self):
        from documentary_review import catalogue_focus_match
        path = 'data/ipack/acces_ipackeps_problemes.txt'
        packet = {'origin':'document', 'selection':'catalogue', 'path':path}
        self.assertTrue(catalogue_focus_match("Connexion à iPackEPS sur ordinateur perso", packet))
        self.assertFalse(catalogue_focus_match("Je ne peux pas importer les élèves.", packet))
        body = __import__('pathlib').Path(path).read_text()
        self.assertIn("Si le lien iPackEPS est absent", body)
        self.assertIn("Si l'application s'ouvre", body)
