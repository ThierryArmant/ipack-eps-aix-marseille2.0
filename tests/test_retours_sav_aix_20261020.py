import json
import unittest
from pathlib import Path
from documentary_review import mark_excerpt, source_packets
from source_scope import select_academy

CASE='data/examens/cas_concrets_lots_inaptes_coevaluation_etranger.txt'
J4='data/examens/audit_faq_2026_10_12/j4_procedure_verifiee.txt'
CONTROL='data/ipack/fiches/ipack_224_situation_role_de_controle_du_chef_d_etablissement_sur_les_protocoles.txt'
ABS='data/examens/audit_lot2_2026_10_12/absence_injustifiee_gt.txt'

class RetoursSavAixTests(unittest.TestCase):
    def test_confirmed_departure_and_unconfirmed_message_are_distinct(self):
        text=Path(J4).read_text()
        self.assertIn('départ de l’élève est avéré',text)
        self.assertIn('faire sortir le candidat du lot',text)
        self.assertIn('ne suffit pas à établir',text)
        self.assertNotIn('Seule solution',text)
        self.assertNotIn("Ce message signifie qu'un élève",text)
        self.assertIn('ni saisir « Absent » ou zéro',text)

    def test_absence_from_my_lot_is_not_absence_from_exam(self):
        text=Path(CASE).read_text()
        self.assertIn('ne pas répondre qu’il faut d’abord l’inscrire',text)
        self.assertIn('la relance d’une distribution ne garantit pas',text)
        self.assertIn('donner au correcteur l’accès au lot',text)
        self.assertIn('ne signifie pas déverrouiller',text)

    def test_certificatif_is_not_an_appn_signature(self):
        text=Path(CONTROL).read_text()
        self.assertIn('n’attend pas à proprement parler une signature',text)
        self.assertIn('déposés et validés',text)
        self.assertIn('contrôle de suivi recommandé',text)
        self.assertNotIn('Avant de signer et valider',text)
        self.assertIn('distincte des signatures prévues pour d’autres dossiers',text)

    def test_current_aix_limits_do_not_override_national_handicap(self):
        text=Path(CASE).read_text()
        self.assertNotIn('un protocole adapté comporte au moins 2 APSA',text)
        self.assertIn('extraction d’iPack IA-IPR',text)
        self.assertIn('ne modifie pas les possibilités de contrôle adapté',text)
        national=Path('data/examens/mesure3_corrections/gt_controle_adapte_inaptitude_permanente.txt').read_text()
        self.assertIn('autant que possible',national)
        self.assertIn('une seule épreuve adaptée',national)

    def test_zero_and_absence_code_are_local_without_reclassifying_national_rule(self):
        ps=source_packets(mark_excerpt(Path(ABS).read_text(),path=ABS))
        selected,_=select_academy(ps,'Nantes')
        code=next(s for s in selected[0]['passages'] if 'le statut d’absence' in s['text'])
        self.assertEqual(code['scope']['academy'],'Aix-Marseille')
        self.assertEqual(code['scope']['not_confirmed_for'],'Nantes')
        self.assertEqual(code['scope']['nature'],['consigne_academique'])
        national=next(s for s in selected[0]['passages'] if 'absence effectivement non justifiée' in s['text'])
        self.assertNotIn('not_confirmed_for',national['scope'])

    def test_exact_annotations_are_unique_and_dated(self):
        n=json.loads(Path('config/nature_passages.json').read_text())['fichiers']
        count=0
        for path,entry in n.items():
            for ann in entry['passages']:
                if 'responsable SAV' not in ann.get('reference',''):continue
                count+=1
                self.assertEqual(Path(path).read_text().count(ann['texte']),1,path)
                self.assertEqual(ann['academie'],'Aix-Marseille')
                self.assertIn('20 octobre 2026',ann['reference'])
        self.assertGreaterEqual(count,10)
