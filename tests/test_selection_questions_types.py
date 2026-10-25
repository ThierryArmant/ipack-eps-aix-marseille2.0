"""Questions types publiques (aucune question privée du journal) : fiche principale attendue et fiches interdites.

Règles communes Claude / GPT (journal du 18 octobre 2026) : dans l'onglet iPackEPS, une question d'opération
logicielle reçoit une fiche de procédure, pas une synthèse de règles d'examen ; un motif ne se déclenche pas
sur un mot seul ; pas de fiche d'un autre diplôme."""
import unittest

import knowledge_catalog as kc

COL, GT, PRO = 'Collège (DNB)', 'Lycée Général & Techno', 'Lycée Pro / CAP'

# (question, public, onglet, début du titre attendu, débuts de titres interdits)
CAS = [
    ('Après la commission d\'harmonisation, qui peut encore corriger une note dans Santorin ?', GT, 'examens', 'Santorin : verrouillage, correction', []),
    ('Les profs d\'EPS sont-ils payés pour les CCF qu\'ils font passer dans leur lycée ?', PRO, 'examens', "CCF d'EPS : pas d'indemnité spécifique", []),
    ('Quand iPackEPS envoie-t-il automatiquement les protocoles vers Cyclades, à quelle heure ?', GT, 'ipack', 'iPackEPS et Cyclades : pas de synchronisation', ['[SITUATION: REFRESH ET SYNCHRONISATION ESTEREL']),
    ('Dans quelle ville ou sur quel site un candidat libre passe-t-il son examen ponctuel d\'EPS ?', GT, 'examens', "Examen ponctuel d'EPS : lieu des épreuves", []),
    ('Pas de réseau au stade pour recevoir le code de connexion à Santorin : comment noter ?', GT, 'examens', "Pas de réseau ou pas de code de connexion", []),
    ('Peut-on inverser l\'ordre des séquences de demi-fond et de badminton dans l\'année ?', GT, 'textes', 'Ordre des séquences et calendrier', []),
    ('Comment ajouter un deuxième évaluateur sur mon lot Santorin ?', GT, 'examens', '[SITUATION: CORRECTION PARTAGÉE SANTORIN]', ['Santorin : Co-évaluation']),
    ('Faut-il un deuxième évaluateur pour le bac ?', GT, 'examens', "Santorin : Co-évaluation — obligatoire ou non selon l'examen", ['[SITUATION: CORRECTION PARTAGÉE']),
    ('Comment réaffecter un lot à un autre examinateur ?', GT, 'examens', 'Cyclades : faire réaffecter les protocoles au bon évaluateur', []),
    ("Un élève est dans le lot de mon collègue, comment le changer de lot ?", GT, 'examens', 'FAQ EPS — Santorin : élève dans le mauvais lot', ['Cyclades : faire réaffecter']),
    ('comment importer mes élèves', COL, 'ipack', 'iPackEPS : classes', []),
    ('comment créer un groupe', COL, 'ipack', 'iPackEPS : créer un groupe', []),
    ('je ne vois pas mes élèves pour faire mon groupe', COL, 'ipack', 'iPackEPS : créer un groupe', []),
    ("comment faire l'emploi du temps", COL, 'ipack', 'iPackEPS : équipements sportifs et créneaux', []),
    ('comment associer ma classe au gymnase', COL, 'ipack', 'iPackEPS : équipements sportifs et créneaux', []),
    ('comment valider les protocoles', COL, 'ipack', None, ['DNB : LSU, Cyclades', 'DNB EPS : compétences']),
    ("où saisir les protocoles d'évaluation CAP et bac", PRO, 'ipack', 'iPackEPS lycée : Dossier Certificatif',
     ['cap session 2026', 'bac pro session 2026']),
    ('j\'ai un message moins de 3 APSA certificatives', PRO, 'ipack', 'iPackEPS lycée : réponses du référent', []),
    ("où saisir les protocoles d'évaluation", GT, 'ipack', 'iPackEPS lycée : Dossier Certificatif', []),
    ('le co-évaluateur est-il obligatoire ?', PRO, 'ipack', None, []),
    ('comment ajouter un collègue TZR', COL, 'ipack', 'iPackEPS : équipe EPS', []),
    # Fiche d'accès découpée (18 octobre) : une question ne reçoit que sa situation.
    ("je n'ai pas accès au dossier certificatif", GT, 'ipack', 'iPackEPS : Ma Fiche Professeur', ['Accès iPackEPS et portail ESTEREL']),
    ("iPackEPS n'apparaît pas dans mon portail", COL, 'ipack', 'Accès iPackEPS et portail ESTEREL', []),
    ("erreur 403 quand j'ouvre ipack", COL, 'ipack', 'Accès iPackEPS et portail ESTEREL', ['DNB : calcul']),
    ("j'ai un message instance en rouge", COL, 'ipack', "iPackEPS : message d'erreur « Instance »", ['Accès iPackEPS et portail ESTEREL']),
    ('cité scolaire : il manque des collègues au collège', COL, 'ipack', 'iPackEPS : cité scolaire', ['Accès iPackEPS et portail ESTEREL']),
    # Fiches officielles devenues prioritaires (questions sans fiche du journal, 18 octobre).
    ("une seconde prépa n'existe pas dans la liste des types de classes", GT, 'ipack', '[SITUATION: SECONDE PRÉPA', []),
    ("je suis sur deux établissements, comment passer de l'un à l'autre", COL, 'ipack', '[SITUATION: ENSEIGNANTS TZR OU PARTAGÉS', []),
    ('registre du matériel escalade, que signifient les alertes rouges', COL, 'ipack', '[ARTICLE 26]', []),
    ('où renseigner les installations sportives', COL, 'ipack', '[ARTICLE 19]', ['Accès iPackEPS et portail ESTEREL']),
    ("message : le groupe n'autorise pas le cycle scolaire", COL, 'ipack', '[ARTICLE 18]', []),
    ("à qui m'adresser pour un bug iPackEPS", GT, 'ipack', 'iPackEPS : qui contacter pour quoi', []),
    ('on a transmis nos protocoles, je veux changer une APSA', GT, 'ipack', "Remplacer une activité d'un protocole", []),
    ('où déposer les fiches certificatives d’activité (FCA) ?', GT, 'ipack', 'iPackEPS lycée : Dossier Certificatif', []),
    # Onglet Examens : fiches Santorin / Cyclades découpées ou rendues prioritaires (18 octobre).
    ('Santorin refuse ma note 4,5', GT, 'examens', 'Santorin : Saisie des notes', []),
    ("l'appréciation est-elle obligatoire dans Santorin ?", GT, 'examens', 'Santorin : Quand remplir le champ', []),
    ('faut-il verrouiller le lot avant la fin des rattrapages ?', GT, 'examens', 'Santorin : Faut-il verrouiller', []),
    ('comment partager un lot Santorin avec un collègue ?', GT, 'examens', '[SITUATION: CORRECTION PARTAGÉE SANTORIN]', []),
    ('mon remplaçant doit saisir les notes dans Santorin', GT, 'examens', '[SITUATION: ACCÈS REMPLAÇANT SANTORIN', ['Santorin : Vocabulaire']),
    ('je ne trouve pas le lot de ma classe dans Santorin', GT, 'examens', '[ERREUR : AUCUN LOT À CORRIGER]', []),
    ("compte-rendu d'import Cyclades : candidats ignorés et INE non inscrits", GT, 'examens', "Cyclades et Santorin : messages d'erreur", []),
    ('une copie est illisible dans Santorin', GT, 'examens', '[SITUATION: SANTORIN POUR LES CORRECTEURS', []),
    # Raccordements signalés par l'audit GPT du 18 octobre (avec contre-exemples).
    ("comment configurer les périodes des séquences d'apprentissage ?", COL, 'ipack', "iPackEPS : APSA, périodes et séquences", []),
    ('où déclarer le nouveau gymnase utilisé avec mes classes ?', COL, 'ipack', '[ARTICLE 19]', ['Accès iPackEPS et portail ESTEREL']),
    ('une APSA a changé après validation du protocole : comment corriger ?', GT, 'ipack', "Remplacer une activité d'un protocole",
     ["[SITUATION: ENSEIGNANT QUI CHANGE D'ÉTABLISSEMENT"]),
    ("je change d'établissement, mes protocoles me suivent-ils ?", GT, 'ipack', "[SITUATION: ENSEIGNANT QUI CHANGE D'ÉTABLISSEMENT", []),
    ('un élève a changé de classe, comment importer sa nouvelle affectation ?', COL, 'ipack', "iPackEPS : élève qui change de classe",
     ['Aix : élève parti encore affiché']),
    ('un élève est parti, il apparaît sans groupe', GT, 'ipack', 'Aix : élève parti encore affiché', ["iPackEPS : élève qui change de classe"]),
    ('je veux ajouter une section sportive mais elle ne figure pas dans les menus', GT, 'ipack', 'iPackEPS : Dossier SSS', []),
    ("comment imprimer une feuille d'appel pour mon groupe ?", COL, 'ipack', "iPackEPS : imprimer une feuille d'appel", []),
    ('comment donner les droits administrateur à un autre collègue ?', COL, 'ipack', "iPackEPS : droits de coordonnateur", []),
    # Raccordements signalés par l'audit Examens de GPT (19 octobre, 0 h).
    ("nos protocoles sont validés : dans quel ordre faire Cyclades et Santorin jusqu'à la saisie des notes ?", GT, 'examens', 'Santorin : De la validation des protocoles', []),
    ('mes notes ont disparu après le bouton Réinitialiser', GT, 'examens', 'Santorin : Saisie des notes', ['Santorin : De la validation des protocoles']),
    ("la même activité n'a pas pu être évaluée pour tout mon groupe de bac pro : comment saisir ?", PRO, 'examens', "Santorin : Une activité n'a pas pu être évaluée", []),
    ('je remplace un collègue absent : comment accéder à ses lots dans Santorin ?', GT, 'examens', '[SITUATION: ACCÈS REMPLAÇANT SANTORIN]',
     ['[ERREUR : AUCUN LOT À CORRIGER]', '[SITUATION: CORRECTION PARTAGÉE SANTORIN]']),
    ('une panne de piscine le jour du CCF oblige-t-elle à certifier sur deux notes ?', GT, 'examens', 'Installation fermée pour une classe', []),
    # Cas iPackEPS notés partiels ou faux (formulations génériques), 19 octobre.
    ("je rentre les protocoles dans iPackEPS, on me répond que cette fiche n'est pas certificative", GT, 'ipack',
     'iPackEPS lycée : APSA certificative', ['Accès iPackEPS et portail ESTEREL', 'iPackEPS : rentrée']),
    ('que faut-il refaire à la rentrée dans iPackEPS ?', COL, 'ipack', 'iPackEPS : rentrée', []),
    ('comment savoir si nos protocoles ont été validés par la commission ?', COL, 'ipack', "iPackEPS collège : pas de protocole d'examen", []),
    ('comment valider le protocole de sécurité APPN ?', COL, 'ipack', 'iPackEPS : Dossier APPN', ["iPackEPS collège : pas de protocole d'examen"]),
    ("combien d'élèves sont déclarés inaptes dans l'établissement ?", COL, 'ipack', None, ['DNB EPS : inaptitude']),
    # Calcul national GT : source dédiée, sans l'appliquer à la saisie ou aux autres diplômes.
    ("Quel est le coefficient de l'EPS au bac général ?", GT, 'examens', 'Bac GT : calcul, arrondi', []),
    ("Comment arrondir la note finale EPS au bac ?", GT, 'examens', 'Bac GT : calcul, arrondi', []),
    ("Les notes EPS de première comptent-elles au bac ?", GT, 'examens', 'Bac GT : calcul, arrondi', []),
    ("Comment saisir la moyenne finale dans Santorin ?", GT, 'examens', None, ['Bac GT : calcul, arrondi']),
    ("Quel coefficient EPS au CAP ?", PRO, 'examens', None, ['Bac GT : calcul, arrondi']),
    ("Nos protocoles sont validés : dans quel ordre faire Cyclades et Santorin jusqu'à la saisie des notes ?", GT, 'examens', 'Santorin : De la validation', ['Santorin : verrouillage']),
    # Chantier « fragilités » (19 octobre, Claude) : inscription tardive et « note de service ».
    ("Un élève s'est inscrit très en retard aux épreuves ponctuelles du bac, son nom n'apparaît pas sur les listes d'émargement Cyclades : peut-on l'accepter le jour J ?",
     GT, 'examens', 'Cyclades : candidats absents de la liste', ['Questions sans consigne écrite trouvée']),
    ("Un élève arrive en retard le jour du CCF, peut-il passer l'épreuve ?", GT, 'examens', 'Questions sans consigne écrite trouvée', []),
    ("Les repères d'évaluation sous forme de curseurs académiques ne sont pas actualisés dans iPackEPS alors que la note de service est sortie",
     GT, 'ipack', None, ['iPackEPS : notes, moyennes', "[SITUATION: PÉRIMÈTRE"]),
    ("Pour le CCF en bac pro, faut-il saisir une note globale sur 20 ou les notes par AFLP dans Santorin ?", PRO, 'examens', 'Santorin : Saisie des notes', []),
    ("Je suis TZR sur un collège et un lycée : qui fixe mon emploi du temps, comment sont calculées mes ORS et mon ISSR ?", COL, 'examens', 'TZR : zone, rattachement', []),
    ("cité scolaire : je dois remplir deux dossiers EPS ?", GT, 'ipack', 'Cité scolaire (collège + lycée)', []),
    ("En cité scolaire j'ai des heures au collège et au lycée, ai-je droit à une heure de réduction ?", GT, 'textes', 'Cité scolaire (collège + lycée)', []),
    ("Dans notre cité scolaire, qui organise le DNB et le bac EPS ?", COL, 'examens', 'Cité scolaire (collège + lycée)', []),
    ("Où trouver la liste des nouveautés de la dernière version d'iPackEPS ?", GT, 'ipack', 'Nouveautés iPackEPS 2025-2026', []),
    ("Comment indiquer dans Santorin qu'un élève a passé une épreuve de rattrapage ?", GT, 'examens', 'Santorin : Saisie des notes', ['iPackEPS lycée : Dossier Certificatif']),
    ("où saisir les dates de rattrapage du protocole ?", GT, 'ipack', 'iPackEPS lycée : Dossier Certificatif', []),
    ("La note d'EPS de mon élève sur son relevé n'est pas celle que j'ai saisie. Pourquoi ?", GT, 'examens', 'Après la saisie : harmonisation', []),
    ("L'AESH de la classe peut-elle compter comme accompagnatrice de la sortie ?", GT, 'textes', 'Sorties et voyages scolaires : guide Éduscol', []),
    ("j'ai pas de bus, pour mes 8 élèves, puis je louer un minibus pour faire ma sortie escalade ?", COL, 'textes', 'Minibus (de l', []),
    ("mon chef refuse de signer mon ordre de mission pour conduire le minibus de l'AS", COL, 'textes', 'Texte transport des élèves', []),
    ("Je ne peux plus saisir mes notes.", GT, 'ipack', 'iPackEPS : notes, moyennes', []),
    ("Combien de temps iPackEPS conserve-t-il les données de mes élèves, et à qui poser la question ?", GT, 'ipack', 'Passage d’année : conservation des données', []),
]


class QuestionsTypes(unittest.TestCase):
    def test_fiche_principale_et_fiches_interdites(self):
        for q, public, mode, attendu, interdits in CAS:
            with self.subTest(q=q, public=public):
                titres = kc.priority_titles(q, public, mode)
                if attendu:
                    self.assertTrue(any(t.startswith(attendu) for t in titres), (attendu, titres))
                for i in interdits:
                    self.assertFalse(any(t.startswith(i) for t in titres), (i, titres))


if __name__ == '__main__':
    unittest.main()
