import sqlite3
import tempfile
import unittest
from pathlib import Path

from moyenne import (
    Base,
    TRI_MEILLEURES,
    TRI_NOTEES,
    TRI_ORDRE_AJOUT,
    TRI_PERSONNALISE,
    TRI_PIRES,
    deplacer_matiere,
    filtrer_matieres,
    trier_matieres,
)


class TrierMatieresTests(unittest.TestCase):
    def setUp(self):
        self.matieres = [
            {"id": 4, "nom": "Sans note", "note": None},
            {"id": 2, "nom": "Moyenne", "note": 70},
            {"id": 3, "nom": "Meilleure", "note": 95},
            {"id": 1, "nom": "Faible", "note": 40},
        ]

    def test_ordre_dajout_conserve_ordre_initial(self):
        resultat = trier_matieres(self.matieres, TRI_ORDRE_AJOUT)
        self.assertEqual([m["nom"] for m in resultat],
                         ["Faible", "Moyenne", "Meilleure", "Sans note"])

    def test_ordre_personnalise_conserve_lordre_recu(self):
        resultat = trier_matieres(self.matieres, TRI_PERSONNALISE)
        self.assertEqual([m["nom"] for m in resultat],
                         ["Sans note", "Moyenne", "Meilleure", "Faible"])

    def test_deplacement_change_la_position_sans_modifier_la_liste_source(self):
        resultat = deplacer_matiere(self.matieres, 4, 2)
        self.assertEqual([m["nom"] for m in resultat],
                         ["Moyenne", "Meilleure", "Sans note", "Faible"])
        self.assertEqual(self.matieres[0]["nom"], "Sans note")

    def test_recherche_partielle_ignore_la_casse(self):
        resultat = filtrer_matieres(self.matieres, "LE")
        self.assertEqual([m["nom"] for m in resultat], ["Meilleure", "Faible"])

    def test_recherche_vide_conserve_toutes_les_matieres(self):
        resultat = filtrer_matieres(self.matieres, "  ")
        self.assertEqual(resultat, self.matieres)
        self.assertIsNot(resultat, self.matieres)

    def test_notees_dabord_garde_les_sans_note_a_la_fin(self):
        resultat = trier_matieres(self.matieres, TRI_NOTEES)
        self.assertEqual([m["nom"] for m in resultat],
                         ["Moyenne", "Meilleure", "Faible", "Sans note"])

    def test_meilleures_notes_dabord_garde_les_sans_note_a_la_fin(self):
        resultat = trier_matieres(self.matieres, TRI_MEILLEURES)
        self.assertEqual([m["nom"] for m in resultat],
                         ["Meilleure", "Moyenne", "Faible", "Sans note"])

    def test_pires_notes_dabord_garde_les_sans_note_a_la_fin(self):
        resultat = trier_matieres(self.matieres, TRI_PIRES)
        self.assertEqual([m["nom"] for m in resultat],
                         ["Faible", "Moyenne", "Meilleure", "Sans note"])


class BaseOrdreTests(unittest.TestCase):
    def test_ordre_personnalise_et_tri_persistent_apres_reouverture(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "moyenne.db"
            base = Base(chemin)
            base.enregistrer_profil("L1", "Test")
            for nom in ("Français", "Maths", "Histoire"):
                base.ajouter_matiere(nom, 100)
            matieres = base.matieres()
            ordre = [matieres[2], matieres[0], matieres[1]]
            base.enregistrer_ordre(ordre)
            base.enregistrer_tri(TRI_PERSONNALISE)
            base.cnx.close()

            base = Base(chemin)
            try:
                self.assertEqual(base.tri_affichage(), TRI_PERSONNALISE)
                self.assertEqual([m["nom"] for m in base.matieres()],
                                 ["Histoire", "Français", "Maths"])
            finally:
                base.cnx.close()

    def test_migration_garde_profil_et_matieres_existants(self):
        with tempfile.TemporaryDirectory() as dossier:
            chemin = Path(dossier) / "ancien.db"
            cnx = sqlite3.connect(chemin)
            cnx.executescript("""
                CREATE TABLE profil (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    niveau TEXT NOT NULL,
                    nom TEXT NOT NULL);
                CREATE TABLE matieres (
                    id INTEGER PRIMARY KEY,
                    nom TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    coef REAL NOT NULL,
                    note REAL);
                INSERT INTO profil VALUES (1, 'L2', 'Test');
                INSERT INTO matieres VALUES (1, 'Français', 100, 82);
                INSERT INTO matieres VALUES (2, 'Maths', 100, NULL);
            """)
            cnx.close()

            base = Base(chemin)
            try:
                self.assertEqual(base.profil(), ("L2", "Test"))
                self.assertEqual(base.tri_affichage(), TRI_ORDRE_AJOUT)
                self.assertEqual([(m["nom"], m["note"]) for m in base.matieres()],
                                 [("Français", 82), ("Maths", None)])
            finally:
                base.cnx.close()


if __name__ == "__main__":
    unittest.main()
