import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from moyenne import (
    App,
    Base,
    TRI_PERSONNALISE,
    donnees_pwa,
    exporter_pdf,
    lire_csv,
    moyenne,
    tableau_export,
)


class DonneesTests(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.chemin = Path(self.dossier.name) / "moyenne.db"
        self.base = Base(self.chemin)

    def tearDown(self):
        self.base.cnx.close()
        self.dossier.cleanup()

    def test_nouvelle_base_commence_avec_deux_sessions(self):
        self.assertEqual(
            [periode["nom"] for periode in self.base.periodes()],
            ["1ère session", "2ème session"],
        )
        self.assertEqual(self.base.periode_active()["nom"], "1ère session")

    def test_moyenne_simple_ne_pondere_pas_avec_les_coefficients(self):
        self.assertEqual(moyenne([
            {"note": 50, "coef": 1},
            {"note": 100, "coef": 100},
            {"note": None, "coef": 100},
        ]), 75)

    def test_csv_combine_exporte_les_sessions_et_se_reimporte(self):
        periodes = [
            {"nom": "1ère session", "matieres": [
                {"nom": "Maths", "note": 80, "coef": 100},
                {"nom": "Français", "note": 60, "coef": 100},
            ]},
            {"nom": "2ème session", "matieres": [
                {"nom": "Histoire", "note": 90, "coef": 100},
            ]},
        ]
        lignes = tableau_export(periodes, 70)
        chemin = Path(self.dossier.name) / "sessions.csv"
        from moyenne import exporter_csv
        exporter_csv(lignes, chemin)

        self.assertEqual(lignes[0], ["Session", "Matière", "Note", "Statut"])
        self.assertIn(["1ère session", "Moyenne", "70,00", ""], lignes)
        self.assertIn(["2ème session", "Moyenne", "90,00", ""], lignes)
        self.assertIn(["Générale", "Moyenne générale", "76,67", ""], lignes)
        self.assertEqual(lire_csv(chemin), [
            ("1ère session", "Maths", 80),
            ("1ère session", "Français", 60),
            ("2ème session", "Histoire", 90),
        ])

    def test_pdf_consolide_les_sessions(self):
        chemin = Path(self.dossier.name) / "bulletin.pdf"
        exporter_pdf([
            {"nom": "1ère session", "matieres": [{"nom": "Maths", "note": 80, "coef": 100}]},
            {"nom": "2ème session", "matieres": [{"nom": "Histoire", "note": 60, "coef": 100}]},
        ], "Test", "L1", 70, chemin)

        contenu = chemin.read_bytes()
        self.assertTrue(contenu.startswith(b"%PDF-"))
        self.assertTrue(contenu.rstrip().endswith(b"%%EOF"))

    def test_sauvegarde_a_la_fermeture_si_modifie_et_retenue_de_trois(self):
        self.assertIsNone(self.base.sauvegarder_fermeture())
        self.assertEqual(self.base.liste_sauvegardes(), [])

        self.base.enregistrer_profil("L1", "Test")
        sauvegarde = self.base.sauvegarder_fermeture()
        self.assertTrue(sauvegarde.exists())
        self.assertIsNone(self.base.sauvegarder_fermeture())

        copie = sqlite3.connect(sauvegarde)
        try:
            self.assertEqual(copie.execute("SELECT niveau, nom FROM profil WHERE id = 1").fetchone(),
                             ("L1", "Test"))
        finally:
            copie.close()

        for i in range(5):
            self.base.enregistrer_profil("L1", f"Test {i}")
            self.base.sauvegarder_fermeture()
        self.assertEqual(len(self.base.liste_sauvegardes()), 3)

    def test_fermeture_affiche_confirmation_apres_creation_de_sauvegarde(self):
        self.base.enregistrer_profil("L1", "Test")
        base = self.base

        class FausseApp:
            def __init__(self):
                self.base = base
                self.parametres = base.parametres()
                self.en_attente = {}
                self.messages = []
                self.detruite = False

            def informer(self, *args, **kwargs):
                self.messages.append(args)

            def destroy(self):
                self.detruite = True

        app = FausseApp()
        App.quitter(app)

        self.assertEqual(app.messages[0][0], "Sauvegarde effectuée")
        self.assertTrue(app.detruite)
        self.assertFalse(self.base._modifie_depuis_sauvegarde)

    def test_demarrage_limite_les_anciennes_sauvegardes_a_trois(self):
        for i in range(5):
            self.base._creer_sauvegarde(f"moyenne_ancienne_{i}.db", nettoyer=False)
        self.base.cnx.close()

        self.base = Base(self.chemin)

        self.assertEqual(len(self.base.liste_sauvegardes()), 3)

    def test_parametres_persistent_et_refusent_les_valeurs_invalides(self):
        self.base.enregistrer_parametres({
            "langue": "en",
            "theme": "sombre",
            "nb_sauvegardes": "1",
        })
        self.assertEqual(self.base.parametres()["langue"], "en")
        self.assertTrue(self.base._modifie_depuis_sauvegarde)

        with self.assertRaises(ValueError):
            self.base.enregistrer_parametres({"theme": "bleu"})

        self.base.cnx.close()
        self.base = Base(self.chemin)
        self.assertEqual(self.base.parametres()["theme"], "sombre")
        self.assertEqual(self.base.parametres()["nb_sauvegardes"], "1")

    def test_sauvegarde_mobile_contient_le_profil_et_toutes_les_periodes(self):
        premiere = self.base.periode_active()["id"]
        self.base.enregistrer_profil("L2", "Test")
        self.base.ajouter_matiere("Maths", 100)
        self.base.changer_note("Maths", 84)
        seconde = self.base.periodes()[1]["id"]
        self.base.activer_periode(seconde)
        self.base.ajouter_matiere("Histoire", 100)
        self.base.enregistrer_tri(TRI_PERSONNALISE)
        self.base.enregistrer_parametres({"langue": "en", "theme": "sombre", "taille_texte": "grande"})

        sauvegarde = donnees_pwa(self.base)

        self.assertEqual(sauvegarde["profile"], {"level": "L2", "name": "Test"})
        self.assertEqual(sauvegarde["activePeriodId"], str(seconde))
        self.assertEqual(sauvegarde["sortMode"], "custom")
        self.assertEqual(sauvegarde["settings"], {
            "language": "en", "theme": "dark", "textSize": "large"})
        self.assertEqual(sauvegarde["periods"][0]["id"], str(premiere))
        self.assertEqual(sauvegarde["periods"][0]["subjects"][0]["grade"], 84)
        self.assertEqual(sauvegarde["periods"][1]["id"], str(seconde))
        self.assertEqual(sauvegarde["periods"][1]["subjects"][0]["name"], "Histoire")

    def test_nombre_de_sauvegardes_regle_la_retenue(self):
        for i in range(4):
            self.base._creer_sauvegarde(f"moyenne_test_{i}.db", nettoyer=False)
        self.base.enregistrer_parametres({"nb_sauvegardes": "1"})

        self.base._nettoyer_sauvegardes()

        self.assertEqual(len(self.base.liste_sauvegardes()), 1)

    def test_traduction_anglaise_des_libelles_de_parametres(self):
        app = SimpleNamespace(langue="en")

        self.assertEqual(App.tr(app, "Paramètres"), "Settings")
        self.assertEqual(App.tr(app, "Période actuelle"), "Current period")
        self.assertEqual(App.tr(app, "Matière sous 70"), "Subject below 70")

    def test_echec_de_sauvegarde_empeche_la_fermeture_et_affiche_une_erreur(self):
        self.base.enregistrer_profil("L1", "Test")
        base = self.base

        class FausseApp:
            def __init__(self):
                self.base = base
                self.en_attente = {}
                self.messages = []
                self.detruite = False

            def informer(self, *args, **kwargs):
                self.messages.append(args)

            def destroy(self):
                self.detruite = True

        app = FausseApp()
        with patch.object(self.base, "sauvegarder_fermeture", side_effect=OSError("dossier indisponible")):
            App.quitter(app)

        self.assertEqual(app.messages[0][0], "Sauvegarde impossible")
        self.assertFalse(app.detruite)

    def test_restauration_remet_les_donnees_et_cree_des_copies_de_securite(self):
        self.base.enregistrer_profil("L1", "Test")
        self.base.ajouter_matiere("Maths", 100)
        self.base.changer_note("Maths", 84)
        sauvegarde = self.base._creer_sauvegarde("moyenne_test_snapshot.db")

        self.base.supprimer_matiere("Maths")
        self.base.restaurer_sauvegarde(sauvegarde)

        self.assertEqual([(m["nom"], m["note"]) for m in self.base.matieres()], [("Maths", 84)])
        self.assertTrue(any("avant-restauration" in f.name for f in self.base.liste_sauvegardes()))
        self.assertTrue(any("apres-restauration" in f.name for f in self.base.liste_sauvegardes()))

    def test_periodes_isolent_les_matieres_et_autorisent_les_memes_noms(self):
        initiale = self.base.periode_active()["id"]
        self.base.ajouter_matiere("Maths", 100)
        self.base.changer_note("Maths", 91)

        seconde = self.base.ajouter_periode("Semestre 2")
        self.base.ajouter_matiere("Maths", 100)
        self.base.changer_note("Maths", 62)

        self.assertEqual(self.base.periode_active()["id"], seconde)
        self.assertEqual(self.base.matieres()[0]["note"], 62)
        self.assertEqual(self.base.matieres(initiale)[0]["note"], 91)

    def test_supprimer_periode_active_bascule_sur_une_autre_et_supprime_ses_matieres(self):
        initiale = self.base.periode_active()["id"]
        seconde = self.base.periodes()[1]["id"]
        self.base.activer_periode(seconde)
        self.base.ajouter_matiere("Physique", 100)

        self.base.supprimer_periode(seconde)

        self.assertEqual(self.base.periode_active()["id"], initiale)
        self.assertEqual(self.base.matieres(seconde), [])
        with self.assertRaises(ValueError):
            self.base.supprimer_periode(initiale)

    def test_annulation_de_suppression_restaure_une_matiere_meme_si_id_reutilise(self):
        self.base.ajouter_matiere("Français", 100)
        self.base.ajouter_matiere("Maths", 100)
        identifiant = self.base.ajouter_matiere("Histoire", 100)
        self.base.changer_note("Histoire", 77)
        matiere = self.base.matieres()[-1]

        self.base.supprimer_matiere("Histoire")
        self.base.ajouter_matiere("Géographie", 100)
        self.base.restaurer_matiere(matiere, 2)

        resultat = self.base.matieres()
        self.assertEqual([m["nom"] for m in resultat],
                         ["Français", "Maths", "Histoire", "Géographie"])
        histoire = next(m for m in resultat if m["nom"] == "Histoire")
        geographie = next(m for m in resultat if m["nom"] == "Géographie")
        self.assertEqual(histoire["id"], identifiant)
        self.assertEqual(histoire["note"], 77)
        self.assertNotEqual(geographie["id"], identifiant)

    def test_import_csv_ecrit_dans_la_periode_active(self):
        initiale = self.base.periode_active()["id"]
        self.base.ajouter_matiere("Déjà", 100)
        self.base.changer_note("Déjà", 30)
        self.base.ajouter_periode("Semestre 2")
        self.base.ajouter_matiere("Déjà", 100)
        self.base.changer_note("Déjà", 40)

        chemin_csv = Path(self.dossier.name) / "bulletin.csv"
        chemin_csv.write_text("Matière;Note\nDéjà;90\nNouvelle;80\n", encoding="utf-8")

        base = self.base

        class FausseApp:
            def __init__(self):
                self.base = base
                self.matieres = self.base.matieres()
                self.en_attente = {}
                self.parametres = self.base.parametres()

            def confirmer(self, *args, **kwargs):
                return True

            def informer(self, *args, **kwargs):
                raise AssertionError("L'import ne devrait pas afficher d'erreur.")

            def tr(self, texte):
                return texte

            def enregistrer(self, **kwargs):
                return True

            def dessiner(self):
                pass

        with patch("moyenne.filedialog.askopenfilename", return_value=str(chemin_csv)):
            App.importer(FausseApp())

        active = self.base.matieres()
        self.assertEqual([(m["nom"], m["note"]) for m in active], [("Déjà", 90), ("Nouvelle", 80)])
        self.assertEqual(self.base.matieres(initiale)[0]["note"], 30)

    def test_import_csv_combine_repartit_les_notes_par_session(self):
        premiere, seconde = self.base.periodes()
        chemin_csv = Path(self.dossier.name) / "sessions.csv"
        chemin_csv.write_text(
            "Session;Matière;Note;Statut\n"
            "1ère session;Maths;84;Validé\n"
            "2ème session;Maths;62;Reprise\n"
            "1ère session;Moyenne;84,00;\n"
            "2ème session;Moyenne;62,00;\n"
            "Générale;Moyenne générale;73,00;\n",
            encoding="utf-8-sig",
        )
        base = self.base

        class FausseApp:
            def __init__(self):
                self.base = base
                self.matieres = base.matieres()
                self.en_attente = {}
                self.parametres = base.parametres()

            def confirmer(self, *args, **kwargs):
                return True

            def informer(self, *args, **kwargs):
                raise AssertionError("L'import ne devrait pas afficher d'erreur.")

            def tr(self, texte):
                return texte

            def enregistrer(self, **kwargs):
                return True

            def dessiner(self):
                pass

        with patch("moyenne.filedialog.askopenfilename", return_value=str(chemin_csv)):
            App.importer(FausseApp())

        self.assertEqual(self.base.periode_active()["id"], premiere["id"])
        self.assertEqual(self.base.matieres(premiere["id"])[0]["note"], 84)
        self.assertEqual(self.base.matieres(seconde["id"])[0]["note"], 62)


if __name__ == "__main__":
    unittest.main()
