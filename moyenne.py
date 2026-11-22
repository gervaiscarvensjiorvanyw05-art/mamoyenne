#!/usr/bin/env python3
"""MaMoyenne : choisissez votre niveau, ajoutez vos matières, la moyenne se met à jour."""
import csv
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, ttk
import unicodedata

NOM_APP = "MaMoyenne"
ANCIEN_NOM_APP = "CalculMoyenne"  # dossier de données avant le changement de nom
NIVEAUX = {"L1": 70, "L2": 70, "L3": 75, "L4": 80}  # niveau -> note de passage
COEF_DEFAUT = 100
NOTE_MAX = 100
VERT, ROUGE, GRIS = "#1a7f37", "#c62828", "#888888"
BLEU, BORDURE, FOND_ENTETE, FOND_ALTERNE = "#3a5fc0", "#b8c2d8", "#e9edf6", "#f5f7fb"  # PDF
# Couleurs de l'interface
FOND, CARTE, TEXTE, DISCRET, LIGNE = "#f3f5fb", "#ffffff", "#1f2937", "#596273", "#e3e8f2"
BLEU_FONCE, BLEU_NUIT, BLEU_CLAIR, BLEU_PALE = "#2f4fa6", "#263f86", "#e8eefc", "#dbe4ff"
VERT_CLAIR, ROUGE_CLAIR, GRIS_CLAIR = "#e3f4e8", "#fde8e8", "#eef0f4"
ORANGE, ROUGE_FONCE = "#c2700a", "#a51f1f"
NULL = "NULL"  # note pas encore connue : ignorée dans la moyenne
TRI_ORDRE_AJOUT = "Ordre d'ajout"
TRI_NOTEES = "Notées d'abord"
TRI_MEILLEURES = "Meilleures notes d'abord"
TRI_PIRES = "Pires notes d'abord"
TRI_PERSONNALISE = "Ordre personnalisé"
OPTIONS_TRI = (TRI_ORDRE_AJOUT, TRI_NOTEES, TRI_MEILLEURES, TRI_PIRES, TRI_PERSONNALISE)
PERIODE_PREMIERE_SESSION = "1ère session"
PERIODE_DEUXIEME_SESSION = "2ème session"
PERIODE_INITIALE = PERIODE_PREMIERE_SESSION
PARAMETRES_DEFAUT = {
    "theme": "clair",
    "taille_texte": "normale",
    "langue": "fr",
    "nb_sauvegardes": "3",
    "message_sauvegarde": "oui",
    "confirmer_suppression": "oui",
    "confirmer_import": "oui",
}
PARAMETRES_CHOIX = {
    "theme": {"clair", "sombre"},
    "taille_texte": {"normale", "grande"},
    "langue": {"fr", "en"},
    "nb_sauvegardes": {"1", "3", "5"},
    "message_sauvegarde": {"oui", "non"},
    "confirmer_suppression": {"oui", "non"},
    "confirmer_import": {"oui", "non"},
}
TRADUCTIONS_EN = {
    "Pour commencer": "Getting started",
    "Calculez votre moyenne et suivez vos reprises.": "Calculate your average and keep track of retakes.",
    "Au premier lancement, choisissez votre niveau (L1 à L4), puis entrez votre nom.": "On first launch, choose your level (L1 to L4), then enter your name.",
    "Cliquez sur le bouton + pour ajouter une matière.": "Click the + button to add a subject.",
    "Saisir ses notes": "Entering grades",
    f"Cliquez dans la case Note d'une matière et tapez votre note, entre 0 et {NOTE_MAX} (15,5 ou 15.5 sont acceptés).": f"Click a subject's Grade field and enter a grade from 0 to {NOTE_MAX} (15.5 is accepted).",
    f"Si vous n'avez pas encore la note, laissez {NULL} (ou videz la case) : la matière ne compte pas dans la moyenne.": f"If you do not have the grade yet, leave {NULL} (or clear the field): the subject is not included in the average.",
    "La moyenne et les reprises se mettent à jour pendant que vous tapez.": "The average and retakes update as you type.",
    "Appuyez sur Entrée pour enregistrer la note : le curseur passe à la matière suivante.": "Press Enter to save the grade; the cursor moves to the next subject.",
    "Une note modifiée mais pas encore enregistrée est entourée en orange. Le bouton Enregistrer (en bas à droite) enregistre toutes les notes modifiées d'un coup.": "An edited but unsaved grade is outlined in orange. The Save button (bottom right) saves all edited grades at once.",
    "Si vous fermez l'application avec des notes non enregistrées, elle vous le demande.": "If you close the app with unsaved grades, you will be asked what to do.",
    "Notes de passage et reprises": "Pass marks and retakes",
    "L1 : 70    L2 : 70    L3 : 75    L4 : 80": "L1: 70    L2: 70    L3: 75    L4: 80",
    "Une matière notée en dessous de la note de passage de votre niveau est une reprise (en rouge).": "A subject grade below your level's pass mark is a retake (shown in red).",
    "Toutes les matières ont le même poids dans la moyenne.": "All subjects have equal weight in the average.",
    "Matières": "Subjects",
    "Choisissez la période active au-dessus du résumé. Dans Gérer les périodes, créez, renommez ou supprimez une période ; sa suppression efface ses matières et demande confirmation.": "Choose the active period above the summary. In Manage periods, create, rename, or delete a period; deleting one removes its subjects and asks for confirmation.",
    "Les notes existantes sont conservées dans « 1ère session » ; la « 2ème session » est ajoutée.": "Existing grades are kept in “1st session”; “2nd session” is added.",
    "Au-dessus de la liste, choisissez l'ordre d'ajout, les matières notées d'abord, les meilleures ou les pires notes d'abord, ou un ordre personnalisé. Les matières sans note restent en bas des tris par note.": "Above the list, choose added order, graded first, highest or lowest grades first, or a custom order. Ungraded subjects stay at the bottom of grade-based sorts.",
    "Le champ Rechercher filtre la liste par nom sans changer le résumé.": "The Search field filters the list by name without changing the summary.",
    "Le classement est actualisé lorsque vous enregistrez une note.": "The ranking updates when you save a grade.",
    "Glissez la poignée à deux traits ≡ devant une matière pour la déplacer ; cet ordre est conservé.": "Drag the two-line ≡ handle beside a subject to move it; the order is saved.",
    "Le bouton + (sous la liste) ajoute une matière ; sa note commence à NULL.": "The + button (below the list) adds a subject; its grade starts as NULL.",
    "✕ à droite d'une matière : la supprime avec sa note. Le bouton Annuler permet de la restaurer pendant 10 secondes.": "✕ beside a subject deletes it and its grade. Undo restores it for 10 seconds.",
    "Sauvegardes": "Backups",
    "Après des modifications enregistrées, une sauvegarde est créée à la fermeture de l'application. Les 3 plus récentes sont conservées sur cet ordinateur.": "After saved changes, a backup is created when the app closes. The 3 most recent backups are kept on this computer.",
    "Sauvegardes : choisissez une copie pour restaurer les données. Des copies de sécurité sont créées avant et après le remplacement.": "Backups: choose a copy to restore your data. Safety copies are created before and after restoring.",
    "Exporter et importer": "Export and import",
    "Exporter… : enregistre votre bulletin en PDF (à imprimer) ou en CSV (LibreOffice / Excel).": "Export… saves your report as a PDF (for printing) or CSV (LibreOffice / Excel).",
    "Importer… : reprend un bulletin CSV, par exemple pour retrouver vos notes sur un autre ordinateur. Les matières absentes sont ajoutées, celles déjà présentes prennent la note du fichier.": "Import… loads a CSV report, for example to transfer grades from another computer. Missing subjects are added; existing subjects take the grades from the file.",
    "Un fichier CSV fait à la main fonctionne aussi : une ligne par matière, sous la forme Matière;Note.": "You can also create a CSV file manually: one subject per line, in the format Subject;Grade.",
    "Profil": "Profile",
    "Périodes": "Periods",
    "Niveau": "Level",
    "Nom": "Name",
    "Exporter": "Export",
    "Mode d'emploi": "Help",
    "Matière": "Subject",
    "Profil… : changer de nom ou de niveau.": "Profile… changes your name or level.",
    "Tout effacer : supprime votre profil et toutes vos matières pour recommencer à zéro.": "Clear all: deletes your profile and all subjects so you can start over.",
    "Importer": "Import",
    "Paramètres": "Settings",
    "Période :": "Period:",
    "Période actuelle": "Current period",
    "1ère session": "1st session",
    "2ème session": "2nd session",
    "Note de passage": "Pass mark",
    "NULL = note pas encore connue, non comptée dans la moyenne": "NULL = grade not yet known; not included in the average",
    "Gérer les périodes…": "Manage periods…",
    "Ajoutez votre première matière": "Add your first subject",
    "Cliquez sur le bouton + pour commencer": "Click the + button to get started",
    "ou importer un bulletin (CSV)…": "or import a report (CSV)…",
    "MOYENNE": "AVERAGE",
    "REPRISES": "RETAKES",
    "MATIÈRES NOTÉES": "GRADED SUBJECTS",
    "Trier :": "Sort:",
    "Rechercher :": "Search:",
    "≡ déplacer": "≡ drag to move",
    "MATIÈRE": "SUBJECT",
    "COEF": "COEF",
    "NOTE": "GRADE",
    "STATUT": "STATUS",
    "Aucune matière ne correspond à cette recherche.": "No subjects match this search.",
    "Effacer la recherche": "Clear search",
    "Enregistrer": "Save",
    "Annuler": "Cancel",
    "Annuler la suppression": "Undo deletion",
    "Tout est enregistré": "All changes saved",
    "Aucune reprise": "No retakes",
    "Toutes notées": "All graded",
    "Nouvelle matière": "New subject",
    "Nom de la matière": "Subject name",
    "Ajouter": "Add",
    "Supprimer la matière ?": "Delete subject?",
    "Supprimer": "Delete",
    "Gérer les périodes": "Manage periods",
    "Créez une période ou choisissez-en une pour la renommer ou la supprimer.": "Create a period or select one to rename or delete.",
    "Nom de la période": "Period name",
    "Sélectionnez une période.": "Select a period.",
    "Créer et activer": "Create and activate",
    "Renommer": "Rename",
    "Fermer": "Close",
    "Supprimer cette période ?": "Delete this period?",
    "Tout effacer ?": "Clear all?",
    "Votre profil": "Your profile",
    "Tout effacer": "Clear all",
    "Valider": "Save",
    "Choisissez une sauvegarde à restaurer :": "Choose a backup to restore:",
    "Aucune sauvegarde n'est disponible.": "No backups are available.",
    "Restaurer": "Restore",
    "Restaurer cette sauvegarde ?": "Restore this backup?",
    "Les données actuelles seront remplacées. Une copie de la base actuelle sera créée avant la restauration.": "Current data will be replaced. A safety copy of the current database will be created before restoring.",
    "Restauration terminée": "Restore complete",
    "Importer un bulletin": "Import report",
    "Exporter le bulletin": "Export report",
    "Tous les fichiers": "All files",
    "Importer ce bulletin ?": "Import this report?",
    "Exporter votre bulletin": "Export your report",
    "Choisissez le format du fichier :": "Choose a file format:",
    "PDF  ·  à imprimer ou envoyer": "PDF · print or share",
    "CSV  ·  LibreOffice / Excel": "CSV · LibreOffice / Excel",
    "JSON  ·  toutes les périodes (application mobile)": "JSON · all periods (mobile app)",
    "Exporter les données": "Export data",
    "Quel est votre niveau ?": "What is your level?",
    "Quel est votre nom ?": "What is your name?",
    "Suivant  →": "Next  →",
    "Commencer": "Get started",
    "←  Retour": "←  Back",
    "Choisissez votre langue": "Choose your language",
    "Apparence": "Appearance",
    "Thème": "Theme",
    "Clair": "Light",
    "Sombre": "Dark",
    "Taille du texte": "Text size",
    "Normale": "Normal",
    "Grande": "Large",
    "Nombre de sauvegardes": "Number of backups",
    "Afficher le message après une sauvegarde": "Show a message after a backup",
    "Demander confirmation avant de supprimer une matière": "Ask before deleting a subject",
    "Demander confirmation avant d'importer des notes": "Ask before importing grades",
    "Paramètres enregistrés": "Settings saved",
    "Langue": "Language",
    "Français": "French",
    "English": "English",
    "active": "active",
    "Supprimer la matière": "Delete subject",
    "Suppression impossible": "Could not delete",
    "Ajout impossible": "Could not add subject",
    "Enregistrement impossible": "Could not save",
    "Changement impossible": "Could not switch period",
    "Création impossible": "Could not create period",
    "Renommage impossible": "Could not rename period",
    "Restauration impossible": "Could not restore",
    "Import impossible": "Could not import",
    "Import interrompu": "Import interrupted",
    "Profil impossible": "Could not save profile",
    "Déplacement impossible": "Could not move subject",
    "Les paramètres n'ont pas pu être enregistrés :": "Settings could not be saved:",
    "Aucune matière trouvée dans ce fichier.": "No subjects were found in this file.",
    "Tout est déjà enregistré": "Everything is already saved",
    "Matière(s) trouvée(s)": "Subject(s) found",
    "Nouvelle(s)": "New",
    "Déjà présente(s)": "Already present",
    "Le fichier": "The file",
    "Matière;Note": "Subject;Grade",
    "Choisissez votre niveau dans la liste.": "Choose your level from the list.",
    "Entrez votre nom.": "Enter your name.",
    "Notes non enregistrées": "Unsaved grades",
    "Certaines notes ont été modifiées mais pas enregistrées.": "Some grades have been changed but not saved.",
    "Ne pas enregistrer": "Don't save",
    "Sauvegarde effectuée": "Backup complete",
    "Sauvegarde impossible": "Backup failed",
    "Sélectionnez une sauvegarde.": "Select a backup.",
    "Sauvegarde": "Backup",
    "Ordre d'ajout": "Added order",
    "Notées d'abord": "Graded first",
    "Meilleures notes d'abord": "Highest grades first",
    "Pires notes d'abord": "Lowest grades first",
    "Ordre personnalisé": "Custom order",
    "Validé": "Passed",
    "Reprise": "Retake",
    "En attente": "Pending",
}

MODE_EMPLOI = [
    ("Pour commencer", [
        "Au premier lancement, choisissez votre niveau (L1 à L4), puis entrez votre nom.",
        "Cliquez sur le bouton + pour ajouter une matière.",
    ]),
    ("Saisir ses notes", [
        f"Cliquez dans la case Note d'une matière et tapez votre note, entre 0 et {NOTE_MAX} "
        "(15,5 ou 15.5 sont acceptés).",
        f"Si vous n'avez pas encore la note, laissez {NULL} (ou videz la case) : "
        "la matière ne compte pas dans la moyenne.",
        "La moyenne et les reprises se mettent à jour pendant que vous tapez.",
        "Appuyez sur Entrée pour enregistrer la note : le curseur passe à la matière suivante.",
        "Une note modifiée mais pas encore enregistrée est entourée en orange. "
        "Le bouton Enregistrer (en bas à droite) enregistre toutes les notes modifiées d'un coup.",
        "Si vous fermez l'application avec des notes non enregistrées, elle vous le demande.",
    ]),
    ("Notes de passage et reprises", [
        "L1 : 70    L2 : 70    L3 : 75    L4 : 80",
        "Une matière notée en dessous de la note de passage de votre niveau est une reprise (en rouge).",
        "Toutes les matières ont le même poids dans la moyenne.",
    ]),
    ("Matières", [
        "Choisissez la période active au-dessus du résumé. Dans Gérer les périodes, créez, renommez "
        "ou supprimez une période ; sa suppression efface ses matières et demande confirmation.",
        "Les nouvelles installations commencent avec « 1ère session » et « 2ème session ». Les notes "
        "déjà enregistrées dans une seule période sont conservées dans « 1ère session » ; la seconde "
        "session est ajoutée.",
        "Au-dessus de la liste, choisissez l'ordre d'ajout, les matières notées d'abord, "
        "les meilleures ou les pires notes d'abord, ou un ordre personnalisé. Les matières sans note "
        "restent en bas des tris par note.",
        "Le champ Rechercher filtre la liste par nom sans changer le résumé.",
        "Le classement est actualisé lorsque vous enregistrez une note.",
        "Glissez la poignée à deux traits ≡ devant une matière pour la déplacer ; cet ordre est conservé.",
        "Le bouton + (sous la liste) ajoute une matière ; sa note commence à NULL.",
        "✕ à droite d'une matière : la supprime avec sa note. Le bouton Annuler permet de la restaurer "
        "pendant 10 secondes.",
    ]),
    ("Sauvegardes", [
        "Après des modifications enregistrées, une sauvegarde est créée à la fermeture de l'application. "
        "Les 3 plus récentes sont conservées sur cet ordinateur.",
        "Sauvegardes : choisissez une copie pour restaurer les données. Des copies de sécurité sont "
        "créées avant et après le remplacement.",
    ]),
    ("Exporter et importer", [
        "Exporter… : enregistre votre bulletin en PDF (à imprimer) ou en CSV (LibreOffice / Excel).",
        "Importer… : reprend un bulletin CSV, par exemple pour retrouver vos notes sur un autre ordinateur. "
        "Les matières absentes sont ajoutées, celles déjà présentes prennent la note du fichier.",
        "Un fichier CSV fait à la main fonctionne aussi : une ligne par matière, sous la forme Matière;Note.",
    ]),
    ("Profil", [
        "Profil… : changer de nom ou de niveau.",
        "Tout effacer : supprime votre profil et toutes vos matières pour recommencer à zéro.",
    ]),
]
LIGNES_IGNOREES = {
    "matiere", "moyenne", "moyenne de la session", "moyenne generale", "reprises",
}

# Taille de police de référence pour une fenêtre de LARGEUR_REF x HAUTEUR_REF
TAILLE_REF, LARGEUR_REF, HAUTEUR_REF = 11, 900, 550
LARGEUR_COMPACTE = 780


# ---------- Base de données ----------

def dossier_donnees():
    """Dossier de données de l'utilisateur, selon le système (l'exécutable n'est pas modifiable)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    dossier = base / NOM_APP
    ancien = base / ANCIEN_NOM_APP
    if not dossier.exists() and ancien.exists():
        ancien.rename(dossier)  # on garde les notes saisies avant le changement de nom
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


class Base:
    """Profil et notes stockés dans une base SQLite ; chaque modification est enregistrée immédiatement."""

    def __init__(self, chemin=None):
        self.chemin = Path(chemin) if chemin else dossier_donnees() / "moyenne.db"
        self.dossier_sauvegardes = self.chemin.parent / "sauvegardes"
        existait = self.chemin.exists() and self.chemin.stat().st_size > 0
        self.cnx = sqlite3.connect(self.chemin)
        migration_requise = existait and self._migration_requise()
        if migration_requise:
            horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
            self._creer_sauvegarde(f"moyenne_{horodatage}_avant-migration.db", nettoyer=False)
        self._initialiser_schema()
        self._modifie_depuis_sauvegarde = migration_requise
        self._nettoyer_sauvegardes()

    def _migration_requise(self):
        tables = {ligne[0] for ligne in self.cnx.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        if "parametres" not in tables and tables & {"profil", "matieres"}:
            return True
        if "periodes" not in tables:
            return bool(tables & {"profil", "matieres"})
        if "profil" in tables:
            colonnes_profil = {ligne[1] for ligne in self.cnx.execute("PRAGMA table_info(profil)")}
            if "tri" not in colonnes_profil:
                return True
        if "matieres" in tables:
            colonnes_matieres = {ligne[1] for ligne in self.cnx.execute("PRAGMA table_info(matieres)")}
            if not {"periode_id", "position"} <= colonnes_matieres:
                return True
        if "periodes" in tables:
            nombre = self.cnx.execute("SELECT COUNT(*) FROM periodes").fetchone()[0]
            version_sessions = self.cnx.execute("PRAGMA user_version").fetchone()[0]
            if nombre < 2 and version_sessions < 1:
                return True
        return False

    def _marquer_modifie(self):
        self._modifie_depuis_sauvegarde = True

    def _initialiser_schema(self):
        self.cnx.execute("PRAGMA foreign_keys = ON")
        self.cnx.executescript("""
            CREATE TABLE IF NOT EXISTS profil (
                id     INTEGER PRIMARY KEY CHECK (id = 1),
                niveau TEXT NOT NULL,
                nom    TEXT NOT NULL,
                tri    TEXT NOT NULL DEFAULT 'Ordre d''ajout');
            CREATE TABLE IF NOT EXISTS periodes (
                id       INTEGER PRIMARY KEY,
                nom      TEXT NOT NULL UNIQUE COLLATE NOCASE,
                position INTEGER NOT NULL DEFAULT 0,
                actif    INTEGER NOT NULL DEFAULT 0 CHECK (actif IN (0, 1)));
            CREATE TABLE IF NOT EXISTS matieres (
                id         INTEGER PRIMARY KEY,
                periode_id INTEGER NOT NULL REFERENCES periodes(id) ON DELETE CASCADE,
                nom        TEXT NOT NULL COLLATE NOCASE,
                coef       REAL NOT NULL,
                note       REAL,  -- NULL : note pas encore connue
                position   INTEGER NOT NULL DEFAULT 0,
                UNIQUE (periode_id, nom));
            CREATE TABLE IF NOT EXISTS parametres (
                cle    TEXT PRIMARY KEY,
                valeur TEXT NOT NULL);
        """)
        with self.cnx:
            self.cnx.executemany(
                "INSERT OR IGNORE INTO parametres (cle, valeur) VALUES (?, ?)",
                PARAMETRES_DEFAUT.items())
            colonnes_profil = {ligne[1] for ligne in self.cnx.execute("PRAGMA table_info(profil)")}
            if "tri" not in colonnes_profil:
                self.cnx.execute("ALTER TABLE profil ADD COLUMN tri TEXT NOT NULL DEFAULT 'Ordre d''ajout'")

            colonnes_matieres = {ligne[1] for ligne in self.cnx.execute("PRAGMA table_info(matieres)")}
            if "position" not in colonnes_matieres:
                self.cnx.execute("ALTER TABLE matieres ADD COLUMN position INTEGER NOT NULL DEFAULT 0")
                self.cnx.execute("UPDATE matieres SET position = id")

            version_sessions = self.cnx.execute("PRAGMA user_version").fetchone()[0]
            periodes = self.cnx.execute(
                "SELECT id, nom FROM periodes ORDER BY position, id").fetchall()
            if not periodes:
                curseur = self.cnx.execute(
                    "INSERT INTO periodes (nom, position, actif) VALUES (?, 0, 1)",
                    (PERIODE_PREMIERE_SESSION,))
                periode_id = curseur.lastrowid
                self.cnx.execute(
                    "INSERT INTO periodes (nom, position, actif) VALUES (?, 1, 0)",
                    (PERIODE_DEUXIEME_SESSION,))
                periodes = [(periode_id, PERIODE_PREMIERE_SESSION)]
            elif len(periodes) == 1:
                periode_id, nom = periodes[0]
                if version_sessions < 1:
                    if nom.casefold() != PERIODE_PREMIERE_SESSION.casefold():
                        self.cnx.execute(
                            "UPDATE periodes SET nom = ?, position = 0 WHERE id = ?",
                            (PERIODE_PREMIERE_SESSION, periode_id))
                    self.cnx.execute(
                        "INSERT INTO periodes (nom, position, actif) VALUES (?, 1, 0)",
                        (PERIODE_DEUXIEME_SESSION,))
            else:
                periode_id = periodes[0][0]

            actives = [ligne[0] for ligne in self.cnx.execute(
                "SELECT id FROM periodes WHERE actif = 1 ORDER BY position, id")]
            if not actives:
                self.cnx.execute("UPDATE periodes SET actif = 1 WHERE id = ?", (periode_id,))
            elif len(actives) > 1:
                self.cnx.execute("UPDATE periodes SET actif = 0")
                self.cnx.execute("UPDATE periodes SET actif = 1 WHERE id = ?", (actives[0],))
            periode_id = self.cnx.execute(
                "SELECT id FROM periodes WHERE actif = 1").fetchone()[0]

            if "periode_id" not in colonnes_matieres:
                self.cnx.execute("ALTER TABLE matieres RENAME TO matieres_ancienne")
                self.cnx.execute("""
                    CREATE TABLE matieres (
                        id         INTEGER PRIMARY KEY,
                        periode_id INTEGER NOT NULL REFERENCES periodes(id) ON DELETE CASCADE,
                        nom        TEXT NOT NULL COLLATE NOCASE,
                        coef       REAL NOT NULL,
                        note       REAL,
                        position   INTEGER NOT NULL DEFAULT 0,
                        UNIQUE (periode_id, nom))
                """)
                self.cnx.execute(
                    "INSERT INTO matieres (id, periode_id, nom, coef, note, position) "
                    "SELECT id, ?, nom, coef, note, position FROM matieres_ancienne",
                    (periode_id,))
                self.cnx.execute("DROP TABLE matieres_ancienne")

            self.cnx.execute("UPDATE matieres SET periode_id = ? WHERE periode_id IS NULL", (periode_id,))
            self.cnx.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_periodes_une_active "
                "ON periodes(actif) WHERE actif = 1")
            self.cnx.execute("PRAGMA user_version = 1")

    def _creer_sauvegarde(self, nom, nettoyer=True):
        self.dossier_sauvegardes.mkdir(parents=True, exist_ok=True)
        cible = self.dossier_sauvegardes / nom
        temporaire = cible.with_name(f".{cible.name}.tmp")
        destination = sqlite3.connect(temporaire)
        try:
            try:
                self.cnx.backup(destination)
            finally:
                destination.close()
            os.replace(temporaire, cible)
        finally:
            if temporaire.exists():
                temporaire.unlink()
        if nettoyer:
            self._nettoyer_sauvegardes()
        return cible

    def _nettoyer_sauvegardes(self):
        if not self.dossier_sauvegardes.exists():
            return
        limite = int(self.parametres()["nb_sauvegardes"])
        sauvegardes = sorted(
            self.dossier_sauvegardes.glob("moyenne_*.db"),
            key=lambda chemin: chemin.stat().st_mtime,
            reverse=True)
        for ancienne in sauvegardes[limite:]:
            ancienne.unlink()

    def sauvegarder_fermeture(self):
        if not self._modifie_depuis_sauvegarde:
            return None
        horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        sauvegarde = self._creer_sauvegarde(f"moyenne_{horodatage}_fermeture.db")
        self._modifie_depuis_sauvegarde = False
        return sauvegarde

    def liste_sauvegardes(self):
        if not self.dossier_sauvegardes.exists():
            return []
        return sorted(
            self.dossier_sauvegardes.glob("moyenne_*.db"),
            key=lambda chemin: chemin.stat().st_mtime,
            reverse=True)

    def parametres(self):
        valeurs = PARAMETRES_DEFAUT.copy()
        valeurs.update(self.cnx.execute("SELECT cle, valeur FROM parametres"))
        for cle, choix in PARAMETRES_CHOIX.items():
            if valeurs[cle] not in choix:
                raise ValueError(f"Valeur enregistrée invalide pour le paramètre « {cle} ».")
        return valeurs

    def enregistrer_parametres(self, nouveaux):
        actuels = self.parametres()
        changements = {}
        for cle, valeur in nouveaux.items():
            if cle not in PARAMETRES_CHOIX or valeur not in PARAMETRES_CHOIX[cle]:
                raise ValueError(f"Valeur invalide pour le paramètre « {cle} ».")
            if actuels[cle] != valeur:
                changements[cle] = valeur
        if not changements:
            return
        with self.cnx:
            self.cnx.executemany(
                "INSERT INTO parametres (cle, valeur) VALUES (?, ?) "
                "ON CONFLICT (cle) DO UPDATE SET valeur = excluded.valeur",
                changements.items())
        self._marquer_modifie()

    def restaurer_sauvegarde(self, chemin):
        sauvegarde = Path(chemin).resolve()
        if sauvegarde.parent != self.dossier_sauvegardes.resolve():
            raise ValueError("La sauvegarde doit se trouver dans le dossier de sauvegardes.")
        if sauvegarde not in [f.resolve() for f in self.liste_sauvegardes()]:
            raise ValueError("Cette sauvegarde n'existe pas.")
        source = sqlite3.connect(sauvegarde)
        try:
            resultat = source.execute("PRAGMA quick_check").fetchone()
            if not resultat or resultat[0] != "ok":
                raise ValueError("La sauvegarde est endommagée.")
            horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
            self._creer_sauvegarde(f"moyenne_{horodatage}_avant-restauration.db", nettoyer=False)
            source.backup(self.cnx)
            self.cnx.commit()
        finally:
            source.close()
        self._initialiser_schema()
        self._marquer_modifie()
        horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        self._creer_sauvegarde(f"moyenne_{horodatage}_apres-restauration.db")
        self._modifie_depuis_sauvegarde = False

    def profil(self):
        """(niveau, nom), ou None au premier lancement."""
        return self.cnx.execute("SELECT niveau, nom FROM profil WHERE id = 1").fetchone()

    def tri_affichage(self):
        ligne = self.cnx.execute("SELECT tri FROM profil WHERE id = 1").fetchone()
        if ligne is None:
            return TRI_ORDRE_AJOUT
        if ligne[0] not in OPTIONS_TRI:
            raise ValueError(f"Critère de tri enregistré inconnu : {ligne[0]}")
        return ligne[0]

    def periodes(self):
        return [{"id": id_, "nom": nom} for id_, nom in self.cnx.execute(
            "SELECT id, nom FROM periodes ORDER BY position, id")]

    def periode_active(self):
        ligne = self.cnx.execute("SELECT id, nom FROM periodes WHERE actif = 1").fetchone()
        if ligne is None:
            raise RuntimeError("Aucune période active n'est définie.")
        return {"id": ligne[0], "nom": ligne[1]}

    def ajouter_periode(self, nom):
        nom = nom.strip()
        if not nom:
            raise ValueError("Le nom de la période ne peut pas être vide.")
        if self.cnx.execute("SELECT 1 FROM periodes WHERE nom = ?", (nom,)).fetchone():
            raise ValueError(f"La période « {nom} » existe déjà.")
        with self.cnx:
            position = self.cnx.execute(
                "SELECT COALESCE(MAX(position) + 1, 0) FROM periodes").fetchone()[0]
            self.cnx.execute("UPDATE periodes SET actif = 0")
            curseur = self.cnx.execute(
                "INSERT INTO periodes (nom, position, actif) VALUES (?, ?, 1)", (nom, position))
            periode_id = curseur.lastrowid
        self._marquer_modifie()
        return periode_id

    def activer_periode(self, periode_id):
        if not self.cnx.execute("SELECT 1 FROM periodes WHERE id = ?", (periode_id,)).fetchone():
            raise ValueError("Cette période n'existe pas.")
        with self.cnx:
            self.cnx.execute("UPDATE periodes SET actif = 0")
            self.cnx.execute("UPDATE periodes SET actif = 1 WHERE id = ?", (periode_id,))
        self._marquer_modifie()

    def renommer_periode(self, periode_id, nom):
        nom = nom.strip()
        if not nom:
            raise ValueError("Le nom de la période ne peut pas être vide.")
        if self.cnx.execute("SELECT 1 FROM periodes WHERE nom = ? AND id != ?",
                            (nom, periode_id)).fetchone():
            raise ValueError(f"La période « {nom} » existe déjà.")
        with self.cnx:
            curseur = self.cnx.execute("UPDATE periodes SET nom = ? WHERE id = ?", (nom, periode_id))
            if curseur.rowcount != 1:
                raise ValueError("Cette période n'existe pas.")
        self._marquer_modifie()

    def supprimer_periode(self, periode_id):
        periodes = self.periodes()
        if len(periodes) <= 1:
            raise ValueError("Il faut conserver au moins une période.")
        periode = next((p for p in periodes if p["id"] == periode_id), None)
        if periode is None:
            raise ValueError("Cette période n'existe pas.")
        remplacement = next(p for p in periodes if p["id"] != periode_id)
        with self.cnx:
            if self.periode_active()["id"] == periode_id:
                self.cnx.execute("UPDATE periodes SET actif = 0 WHERE id = ?", (periode_id,))
                self.cnx.execute("UPDATE periodes SET actif = 1 WHERE id = ?", (remplacement["id"],))
            self.cnx.execute("DELETE FROM periodes WHERE id = ?", (periode_id,))
        self._marquer_modifie()

    def enregistrer_tri(self, tri):
        if tri not in OPTIONS_TRI:
            raise ValueError(f"Critère de tri inconnu : {tri}")
        with self.cnx:
            curseur = self.cnx.execute("UPDATE profil SET tri = ? WHERE id = 1", (tri,))
            if curseur.rowcount != 1:
                raise RuntimeError("Impossible d'enregistrer le tri sans profil.")
        self._marquer_modifie()

    def enregistrer_profil(self, niveau, nom):
        with self.cnx:
            self.cnx.execute("INSERT INTO profil (id, niveau, nom) VALUES (1, ?, ?)"
                             " ON CONFLICT (id) DO UPDATE SET niveau = excluded.niveau, nom = excluded.nom",
                             (niveau, nom))
        self._marquer_modifie()

    def matieres(self, periode_id=None):
        periode_id = periode_id if periode_id is not None else self.periode_active()["id"]
        return [{"id": id_, "nom": nom, "coef": coef, "note": note}
                for id_, nom, coef, note in self.cnx.execute(
                    "SELECT id, nom, coef, note FROM matieres "
                    "WHERE periode_id = ? ORDER BY position, id", (periode_id,))]

    def ajouter_matiere(self, nom, coef, periode_id=None):
        with self.cnx:
            periode_id = periode_id if periode_id is not None else self.periode_active()["id"]
            position = self.cnx.execute(
                "SELECT COALESCE(MAX(position) + 1, 0) FROM matieres WHERE periode_id = ?",
                (periode_id,)).fetchone()[0]
            curseur = self.cnx.execute(
                "INSERT INTO matieres (periode_id, nom, coef, position) VALUES (?, ?, ?, ?)",
                (periode_id, nom, coef, position))
            matiere_id = curseur.lastrowid
        self._marquer_modifie()
        return matiere_id

    def enregistrer_ordre(self, matieres):
        with self.cnx:
            self.cnx.executemany(
                "UPDATE matieres SET position = ? WHERE id = ?",
                ((position, matiere["id"]) for position, matiere in enumerate(matieres)))
        self._marquer_modifie()

    def supprimer_matiere(self, nom):
        with self.cnx:
            self.cnx.execute("DELETE FROM matieres WHERE nom = ? AND periode_id = ?",
                             (nom, self.periode_active()["id"]))
        self._marquer_modifie()

    def restaurer_matiere(self, matiere, position):
        with self.cnx:
            periode_id = self.periode_active()["id"]
            if self.cnx.execute(
                    "SELECT 1 FROM matieres WHERE nom = ? AND periode_id = ?",
                    (matiere["nom"], periode_id)).fetchone():
                raise ValueError(f"Une matière nommée « {matiere['nom']} » existe déjà.")
            if self.cnx.execute("SELECT 1 FROM matieres WHERE id = ?", (matiere["id"],)).fetchone():
                id_nouveau = self.cnx.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM matieres").fetchone()[0]
                self.cnx.execute("UPDATE matieres SET id = ? WHERE id = ?", (id_nouveau, matiere["id"]))
            curseur = self.cnx.execute(
                "INSERT INTO matieres (id, periode_id, nom, coef, note, position) VALUES (?, ?, ?, ?, ?, ?)",
                (matiere["id"], periode_id, matiere["nom"], matiere["coef"], matiere["note"], position))
            id_restaure = curseur.lastrowid
            ids = [ligne[0] for ligne in self.cnx.execute(
                "SELECT id FROM matieres WHERE periode_id = ? AND id != ? ORDER BY position, id",
                (periode_id, id_restaure))]
            ids.insert(max(0, min(position, len(ids))), id_restaure)
            self.cnx.executemany(
                "UPDATE matieres SET position = ? WHERE id = ?",
                ((i, id_) for i, id_ in enumerate(ids)))
        self._marquer_modifie()
        return id_restaure

    def changer_note(self, matiere, note, periode_id=None):
        with self.cnx:
            periode_id = periode_id if periode_id is not None else self.periode_active()["id"]
            self.cnx.execute("UPDATE matieres SET note = ? WHERE nom = ? AND periode_id = ?",
                             (note, matiere, periode_id))
        self._marquer_modifie()

    def tout_effacer(self):
        with self.cnx:
            self.cnx.execute("DELETE FROM matieres")
            self.cnx.execute("DELETE FROM periodes")
            self.cnx.executemany(
                "INSERT INTO periodes (nom, position, actif) VALUES (?, ?, ?)",
                ((PERIODE_PREMIERE_SESSION, 0, 1), (PERIODE_DEUXIEME_SESSION, 1, 0)))
            self.cnx.execute("DELETE FROM profil")
        self._marquer_modifie()


# ---------- Calculs ----------

def moyenne(matieres):
    """Moyenne simple des notes connues."""
    notees = [m for m in matieres if m["note"] is not None]
    return sum(m["note"] for m in notees) / len(notees) if notees else None


def statut(note, passage):
    if note is None:
        return "En attente"
    return "Validé" if note >= passage else "Reprise"


def nb_reprises(matieres, passage):
    """Nombre de matières notées sous la note de passage (les NULL ne comptent pas)."""
    return sum(1 for m in matieres if m["note"] is not None and m["note"] < passage)


def trier_matieres(matieres, critere):
    if critere == TRI_ORDRE_AJOUT:
        return sorted(matieres, key=lambda m: m["id"])
    if critere == TRI_PERSONNALISE:
        return list(matieres)
    if critere == TRI_NOTEES:
        return sorted(matieres, key=lambda m: m["note"] is None)
    if critere == TRI_MEILLEURES:
        return sorted(matieres, key=lambda m: (
            m["note"] is None, -(m["note"] if m["note"] is not None else 0)))
    if critere == TRI_PIRES:
        return sorted(matieres, key=lambda m: (
            m["note"] is None, m["note"] if m["note"] is not None else 0))
    raise ValueError(f"Critère de tri inconnu : {critere}")


def deplacer_matiere(matieres, id_, index):
    if not 0 <= index < len(matieres):
        raise IndexError(f"Position de destination invalide : {index}")
    source = next((i for i, m in enumerate(matieres) if m["id"] == id_), None)
    if source is None:
        raise ValueError(f"Matière inconnue : {id_}")
    resultat = list(matieres)
    resultat.insert(index, resultat.pop(source))
    return resultat


def filtrer_matieres(matieres, recherche):
    recherche = recherche.strip().casefold()
    if not recherche:
        return list(matieres)
    return [matiere for matiere in matieres if recherche in matiere["nom"].casefold()]


def texte_reprises(n):
    return "Aucune reprise" if n == 0 else f"{n} reprise{'s' if n > 1 else ''}"


def lire_note(texte):
    """Convertit la saisie en note ; vide, NULL ou - signifient « pas encore de note »."""
    texte = texte.strip().replace(",", ".")
    if texte.upper() in ("", NULL, "-"):
        return None
    note = float(texte)  # ValueError si la saisie n'est pas un nombre
    if not 0 <= note <= NOTE_MAX:
        raise ValueError(f"la note doit être comprise entre 0 et {NOTE_MAX}")
    return note


def saisie_autorisee(texte):
    """Filtre la frappe dans une case Note : chiffres jusqu'à NOTE_MAX, ou NULL en cours d'écriture."""
    t = texte.strip()
    if NULL.startswith(t.upper()) or t == "-":
        return True
    if not re.fullmatch(r"\d{0,3}([.,]\d{0,2})?", t):
        return False
    return t in (".", ",") or float(t.replace(",", ".")) <= NOTE_MAX


def fmt(valeur, decimales=None, vide=""):
    """Nombre au format français (virgule décimale)."""
    if valeur is None:
        return vide
    texte = f"{valeur:.{decimales}f}" if decimales is not None else f"{valeur:g}"
    return texte.replace(".", ",")


# ---------- Export ----------

def tableau_export(periodes, passage):
    """Un CSV combiné, avec les notes et la moyenne de chaque session."""
    lignes = [["Session", "Matière", "Note", "Statut"]]
    toutes_matieres = []
    for periode in periodes:
        matieres = periode["matieres"]
        toutes_matieres.extend(matieres)
        for matiere in matieres:
            lignes.append([
                periode["nom"], matiere["nom"], fmt(matiere["note"], vide=NULL),
                statut(matiere["note"], passage)])
        lignes.append([periode["nom"], "Moyenne", fmt(moyenne(matieres), 2, "—"), ""])
    lignes.append(["Générale", "Moyenne générale", fmt(moyenne(toutes_matieres), 2, "—"), ""])
    return lignes


def couleur_texte(texte):
    if texte in ("Validé", "Aucune reprise"):
        return VERT
    if texte == "Reprise" or texte.endswith(("reprise", "reprises")):
        return ROUGE
    return GRIS if texte in ("En attente", NULL) else None


def exporter_csv(lignes, chemin):
    # ";" et BOM UTF-8 : s'ouvre correctement dans LibreOffice et Excel en français
    with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f, delimiter=";").writerows(lignes)


def donnees_pwa(base):
    """Convertit toutes les périodes et le profil vers le format de sauvegarde mobile."""
    modes_tri = {
        TRI_ORDRE_AJOUT: "added",
        TRI_NOTEES: "graded",
        TRI_MEILLEURES: "best",
        TRI_PIRES: "worst",
        TRI_PERSONNALISE: "custom",
    }
    profil = base.profil()
    parametres = base.parametres()
    periodes = []
    for periode in base.periodes():
        matieres = base.matieres(periode["id"])
        periodes.append({
            "id": str(periode["id"]),
            "name": periode["nom"],
            "subjects": [{
                "id": str(matiere["id"]),
                "name": matiere["nom"],
                "grade": matiere["note"],
                "addedOrder": matiere["id"],
            } for matiere in matieres],
        })
    periode_active = base.periode_active()["id"] if profil else None
    return {
        "version": 1,
        "profile": {"level": profil[0], "name": profil[1]} if profil else None,
        "periods": periodes if profil else [],
        "activePeriodId": str(periode_active) if periode_active is not None else None,
        "sortMode": modes_tri[base.tri_affichage()],
        "settings": {
            "language": parametres["langue"],
            "theme": "dark" if parametres["theme"] == "sombre" else "light",
            "textSize": "large" if parametres["taille_texte"] == "grande" else "normal",
        },
    }


def exporter_json_pwa(base, chemin):
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(donnees_pwa(base), fichier, ensure_ascii=False, indent=2)


def exporter_pdf(periodes, nom, niveau, passage, chemin):
    """Bulletin PDF combinant les sessions, leurs moyennes et la moyenne générale."""
    from fpdf import FPDF

    def latin1(texte):  # les polices intégrées de fpdf ne couvrent que le latin-1
        return str(texte).replace("—", "-").encode("latin-1", "replace").decode("latin-1")

    def rgb(couleur):
        return tuple(int(couleur[i:i + 2], 16) for i in (1, 3, 5))

    def ajuster(texte, largeur):  # coupe un texte trop long pour sa case
        texte = latin1(texte)
        while texte and pdf.get_string_width(texte) > largeur - 4:
            texte = texte[:-4] + "..."
        return texte

    def case(largeur, texte, gras=False, couleur="#000000", fond=None, align="C", h=8):
        pdf.set_font("Helvetica", "B" if gras else "", 10)
        pdf.set_text_color(*rgb(couleur))
        if fond:
            pdf.set_fill_color(*rgb(fond))
        pdf.cell(largeur, h, ajuster(texte, largeur), border=1, align=align, fill=bool(fond))

    pdf = FPDF(format="A4")
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_page()
    pdf.set_draw_color(*rgb(BORDURE))
    L = pdf.w - pdf.l_margin - pdf.r_margin

    # Bandeau de titre
    pdf.set_fill_color(*rgb(BLEU))
    pdf.rect(pdf.l_margin, pdf.t_margin, L, 22, style="F")
    pdf.set_xy(pdf.l_margin + 6, pdf.t_margin + 3)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(L - 12, 9, "Bulletin de notes", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin + 6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(L - 12, 6, NOM_APP, new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(pdf.t_margin + 30)

    # Informations de l'étudiant
    etiquette, valeur = L * 0.2, L * 0.3
    for gauche, droite in ((("Nom", nom), ("Niveau", niveau)),
                           (("Note de passage", passage), ("Date", f"{date.today():%d/%m/%Y}"))):
        for lib, val in (gauche, droite):
            case(etiquette, lib, gras=True, fond=FOND_ENTETE, align="L")
            case(valeur, val, align="L")
        pdf.ln()
    pdf.ln(8)

    colonnes = [("Matière", 0.58), ("Note", 0.20), ("Statut", 0.22)]

    def entete_tableau():
        for titre, part in colonnes:
            case(L * part, titre, gras=True, couleur="#ffffff", fond=BLEU)
        pdf.ln()

    toutes_matieres = []
    for periode in periodes:
        matieres = periode["matieres"]
        toutes_matieres.extend(matieres)
        if pdf.get_y() + 26 > pdf.h - pdf.b_margin:
            pdf.add_page()
        pdf.set_fill_color(*rgb(BLEU))
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(L, 10, latin1(periode["nom"]), fill=True)
        pdf.ln()
        entete_tableau()
        for i, matiere in enumerate(matieres, start=1):
            if pdf.get_y() + 8 > pdf.h - pdf.b_margin:
                pdf.add_page()
                entete_tableau()
            fond = FOND_ALTERNE if i % 2 == 0 else "#ffffff"
            etat = statut(matiere["note"], passage)
            valeurs = [
                (matiere["nom"], "#000000"),
                (fmt(matiere["note"], vide=NULL),
                 GRIS if matiere["note"] is None else "#000000"),
                (etat, couleur_texte(etat)),
            ]
            for (texte, couleur), (titre, part) in zip(valeurs, colonnes):
                case(L * part, texte, gras=titre == "Statut" and matiere["note"] is not None,
                     couleur=couleur, fond=fond, align="L" if titre == "Matière" else "C")
            pdf.ln()
        pdf.ln(2)
        moyenne_session = moyenne(matieres)
        couleur_moyenne = (GRIS if moyenne_session is None
                           else VERT if moyenne_session >= passage else ROUGE)
        case(L * 0.70, f"Moyenne de {periode['nom']}", gras=True, fond=FOND_ENTETE, align="L")
        case(L * 0.30, "—" if moyenne_session is None else fmt(moyenne_session, 2),
             gras=True, couleur=couleur_moyenne)
        pdf.ln(8)

    moyenne_generale = moyenne(toutes_matieres)
    if pdf.get_y() + 16 > pdf.h - pdf.b_margin:
        pdf.add_page()
    pdf.set_x(pdf.l_margin + L * 0.4)
    case(L * 0.6, "Résultats généraux", gras=True, couleur="#ffffff", fond=BLEU)
    pdf.ln()
    reprises_generales = nb_reprises(toutes_matieres, passage)
    resultats = [
        ("Moyenne générale", "—" if moyenne_generale is None else fmt(moyenne_generale, 2),
         GRIS if moyenne_generale is None else VERT if moyenne_generale >= passage else ROUGE),
        ("Reprises", texte_reprises(reprises_generales),
         VERT if reprises_generales == 0 else ROUGE),
        ("Matières en attente de note",
         str(sum(1 for matiere in toutes_matieres if matiere["note"] is None)), "#000000"),
    ]
    for libelle, valeur_resultat, couleur in resultats:
        pdf.set_x(pdf.l_margin + L * 0.4)
        case(L * 0.35, libelle, gras=True, fond=FOND_ENTETE, align="L")
        case(L * 0.25, valeur_resultat, gras=True, couleur=couleur)
        pdf.ln()

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*rgb(GRIS))
    pdf.multi_cell(L, 4.5, latin1(
        f"Note de passage en {niveau} : {passage}. Une note inférieure est une reprise.\n"
        f"{NULL} : note pas encore connue, non comptée dans les moyennes. Chaque matière a le même poids."))
    pdf.output(str(chemin))


# ---------- Import ----------

def lire_csv(chemin):
    """Lit les anciens CSV à une période et les CSV combinés avec une colonne Session."""
    with open(chemin, newline="", encoding="utf-8-sig") as f:
        contenu = f.read()
    # ";" en priorité : une virgule peut aussi être la décimale d'une note (15,5)
    premiere = contenu.splitlines()[0] if contenu.strip() else ""
    separateur = ";" if ";" in premiere else ("\t" if "\t" in premiere else ",")
    lignes = [l for l in csv.reader(contenu.splitlines(), delimiter=separateur) if l and l[0].strip()]

    def normaliser(valeur):
        return "".join(car for car in unicodedata.normalize("NFD", valeur.casefold())
                       if unicodedata.category(car) != "Mn").strip()

    entete = [normaliser(cellule) for cellule in lignes[0]]
    col_nom = next((i for i, valeur in enumerate(entete) if valeur in ("matiere", "subject")), None)
    col_note = next((i for i, valeur in enumerate(entete) if valeur in ("note", "grade")), None)
    col_session = next((i for i, valeur in enumerate(entete)
                        if valeur in ("session", "periode", "period")), None)
    if col_nom is None or col_note is None:
        col_nom, col_note, col_session = 0, 1, None
        debut = 0
    else:
        debut = 1

    resultat = []
    for ligne in lignes[debut:]:
        nom = ligne[col_nom].strip() if col_nom < len(ligne) else ""
        if normaliser(nom) in LIGNES_IGNOREES:
            continue
        texte = ligne[col_note] if col_note < len(ligne) else ""
        session = ligne[col_session].strip() if col_session is not None and col_session < len(ligne) else ""
        try:
            note = lire_note(texte)
        except ValueError:
            raise ValueError(f"Note illisible pour « {nom} » : {texte!r}") from None
        resultat.append((session or None, nom, note))
    if not resultat:
        raise ValueError("Aucune matière trouvée dans ce fichier.")
    return resultat


def chemin_ressource(nom):
    """Chemin d'un fichier fourni avec l'application (dans l'exécutable ou à côté du script)."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / nom


def installer_copie(exe, cible):
    """Copie l'exécutable dans `cible` s'il n'y est pas déjà, à l'identique.

    Écriture dans un fichier temporaire puis remplacement : fonctionne même si l'ancienne copie
    est en cours d'exécution, et une nouvelle version téléchargée remplace l'ancienne.
    """
    if exe == cible:
        return
    if cible.exists() and cible.stat().st_size == exe.stat().st_size \
            and cible.read_bytes() == exe.read_bytes():
        return
    cible.parent.mkdir(parents=True, exist_ok=True)
    temporaire = cible.with_suffix(".tmp")
    shutil.copyfile(exe, temporaire)
    temporaire.chmod(0o755)
    os.replace(temporaire, cible)


def integrer_menu_linux():
    """Linux : installe MaMoyenne et l'ajoute au menu des applications (lanceur .desktop + icône).

    L'exécutable se copie dans ~/.local/share/MaMoyenne/MaMoyenne et le menu pointe vers cette copie :
    le fichier téléchargé (ou le dossier du projet) peut ensuite être supprimé sans rien casser.
    """
    try:
        donnees = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
        icone = donnees / "icons" / "hicolor" / "512x512" / "apps" / "mamoyenne.png"
        icone.parent.mkdir(parents=True, exist_ok=True)
        source = chemin_ressource("assets/icone.png")
        if source.exists() and (not icone.exists() or icone.stat().st_size != source.stat().st_size):
            shutil.copyfile(source, icone)

        installe = dossier_donnees() / NOM_APP
        try:
            installer_copie(Path(sys.executable).resolve(), installe)
        except OSError:
            installe = Path(sys.executable).resolve()  # copie impossible : on garde le fichier lancé
        exe = str(installe)
        for car in ("\\", '"', "`", "$"):  # échappement imposé par la norme des fichiers .desktop
            exe = exe.replace(car, "\\" + car)
        contenu = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={NOM_APP}\n"
            "Comment=Calculer sa moyenne et suivre ses reprises\n"
            f'Exec="{exe}"\n'
            f"Icon={icone}\n"
            "Terminal=false\n"
            "Categories=Education;\n"
            "Keywords=moyenne;notes;reprise;bulletin;\n"
            f"StartupWMClass={NOM_APP}\n"
        )
        lanceur = donnees / "applications" / "mamoyenne.desktop"
        lanceur.parent.mkdir(parents=True, exist_ok=True)
        if not lanceur.exists() or lanceur.read_text(encoding="utf-8") != contenu:
            lanceur.write_text(contenu, encoding="utf-8")
            lanceur.chmod(0o755)
    except OSError:
        pass  # pas grave : l'application fonctionne sans entrée dans le menu


def integrer_windows():
    """Windows : installe MaMoyenne dans %LOCALAPPDATA%\\Programs\\MaMoyenne et crée ses raccourcis.

    Raccourci dans le menu Démarrer (recréé s'il manque) et sur le Bureau (seulement à la première
    installation, pour ne pas le remettre si l'utilisateur l'a supprimé). Le fichier téléchargé peut
    ensuite être supprimé.
    """
    exe = Path(sys.executable).resolve()
    installe = Path(os.environ["LOCALAPPDATA"]) / "Programs" / NOM_APP / f"{NOM_APP}.exe"
    premiere_fois = not installe.exists()
    try:
        installer_copie(exe, installe)
    except OSError:
        # ancienne version ouverte (fichier verrouillé) ou copie impossible : on réessaiera plus tard
        if premiere_fois:
            return
    menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{NOM_APP}.lnk"
    raccourcis = [] if menu.exists() else [f"'{ps(menu)}'"]
    if premiere_fois:
        raccourcis.append(f"(Join-Path ([Environment]::GetFolderPath('Desktop')) '{NOM_APP}.lnk')")
    if not raccourcis:
        return
    script = "$w = New-Object -ComObject WScript.Shell; " + "".join(
        f"$s = $w.CreateShortcut({chemin}); $s.TargetPath = '{ps(installe)}'; "
        f"$s.WorkingDirectory = '{ps(installe.parent)}'; $s.IconLocation = '{ps(installe)},0'; "
        "$s.Description = 'Calculer sa moyenne et suivre ses reprises'; $s.Save(); "
        for chemin in raccourcis)
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                    "-Command", script], capture_output=True, timeout=30,
                   creationflags=subprocess.CREATE_NO_WINDOW)


def ps(chemin):
    """Chemin placé entre apostrophes dans une commande PowerShell (apostrophe doublée)."""
    return str(chemin).replace("'", "''")


def integrer_macos():
    """macOS : copie MaMoyenne.app dans ~/Applications si elle a été lancée depuis ailleurs.

    Spotlight et le Launchpad la trouvent alors, et le fichier téléchargé peut être supprimé.
    """
    exe = Path(sys.executable).resolve()  # .../MaMoyenne.app/Contents/MacOS/MaMoyenne
    appli = exe.parents[2]
    if appli.suffix != ".app":
        return
    if appli.parent in (Path("/Applications"), Path.home() / "Applications"):
        return  # déjà rangée dans un dossier d'applications
    cible = Path.home() / "Applications" / appli.name
    exe_cible = cible / exe.relative_to(appli)
    if exe_cible.exists() and exe_cible.read_bytes() == exe.read_bytes():
        return  # cette version est déjà installée
    cible.parent.mkdir(parents=True, exist_ok=True)
    temporaire = cible.with_name(cible.name + ".tmp")
    shutil.rmtree(temporaire, ignore_errors=True)
    subprocess.run(["ditto", str(appli), str(temporaire)], check=True, capture_output=True, timeout=120)
    # l'utilisateur a déjà accepté d'ouvrir l'application : la copie ne doit pas redemander
    subprocess.run(["xattr", "-dr", "com.apple.quarantine", str(temporaire)], capture_output=True, timeout=30)
    shutil.rmtree(cible, ignore_errors=True)
    temporaire.rename(cible)


def integrer_au_systeme():
    """Installe l'exécutable à un endroit permanent et l'ajoute au menu du système.

    Seulement pour l'exécutable (pas en lançant moyenne.py). Facultatif : en cas d'échec,
    l'application fonctionne quand même depuis le fichier lancé.
    """
    if not getattr(sys, "frozen", False):
        return
    try:
        if sys.platform.startswith("linux"):
            integrer_menu_linux()
        elif sys.platform == "win32":
            integrer_windows()
        elif sys.platform == "darwin":
            integrer_macos()
    except (OSError, subprocess.SubprocessError, KeyError, IndexError):
        pass


# ---------- Widgets ----------

class Bouton(tk.Label):
    """Bouton plat coloré (un Label cliquable : les couleurs de tk.Button sont ignorées sur macOS)."""
    STYLES = {  # fond, texte, fond au survol, texte au survol
        "primaire": (BLEU, "#ffffff", BLEU_FONCE, "#ffffff"),
        "secondaire": (CARTE, TEXTE, BLEU_CLAIR, BLEU),
        "barre": (BLEU_FONCE, "#ffffff", BLEU_NUIT, "#ffffff"),
        "lien": (None, BLEU, None, BLEU_FONCE),
        "discret": (CARTE, DISCRET, ROUGE_CLAIR, ROUGE),
        "danger": (CARTE, ROUGE, ROUGE_CLAIR, ROUGE),
        "alerte": (ROUGE, "#ffffff", ROUGE_FONCE, "#ffffff"),
    }

    def __init__(self, parent, texte, commande, style="primaire", font=None, padx=14, pady=6):
        fond, couleur, fond2, couleur2 = self.STYLES[style]
        fond = fond or parent.cget("bg")
        fond2 = fond2 or fond
        racine = parent._root()
        traduire = getattr(racine, "tr", None)
        if traduire:
            texte = traduire(texte)
        super().__init__(parent, text=texte, bg=fond, fg=couleur, font=font, padx=padx, pady=pady,
                         cursor="hand2", highlightthickness=1 if style in ("secondaire", "danger") else 0,
                         highlightbackground=LIGNE)
        self.bind("<Enter>", lambda e: self.config(bg=fond2, fg=couleur2))
        self.bind("<Leave>", lambda e: self.config(bg=fond, fg=couleur))
        self.bind("<ButtonRelease-1>", lambda e: commande())


class BoutonRond(tk.Canvas):
    """Bouton + rond, dont la taille suit la police (pour la mise à l'échelle)."""

    def __init__(self, parent, commande, police, echelle=1.9):
        super().__init__(parent, bg=parent.cget("bg"), highlightthickness=0, bd=0, cursor="hand2")
        self.police, self.echelle, self.couleur = police, echelle, BLEU
        self.bind("<Enter>", lambda e: self.colorer(BLEU_FONCE))
        self.bind("<Leave>", lambda e: self.colorer(BLEU))
        self.bind("<ButtonRelease-1>", lambda e: commande())
        self.redessiner()

    def colorer(self, couleur):
        self.couleur = couleur
        self.redessiner()

    def redessiner(self):
        d = int(self.police.metrics("linespace") * self.echelle)
        self.config(width=d + 2, height=d + 2)
        self.delete("all")
        self.create_oval(1, 1, d, d, fill=self.couleur, outline="")
        c, l, w = d / 2 + 1, d * 0.22, max(2, round(d * 0.08))
        self.create_line(c - l, c, c + l, c, fill="#ffffff", width=w, capstyle="round")
        self.create_line(c, c - l, c, c + l, fill="#ffffff", width=w, capstyle="round")


class ZoneDefilante(tk.Frame):
    """Cadre avec barre de défilement verticale, affichée seulement si le contenu dépasse."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.barre = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interieur = tk.Frame(self.canvas, bg=bg)
        self._fenetre = self.canvas.create_window(0, 0, window=self.interieur, anchor="nw")
        self.canvas.configure(yscrollcommand=self.barre.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.interieur.bind("<Configure>", self.ajuster)
        self.canvas.bind("<Configure>", self.ajuster)

    def deborde(self):
        return self.interieur.winfo_reqheight() > self.canvas.winfo_height()

    def ajuster(self, _=None):
        self.canvas.itemconfigure(self._fenetre, width=self.canvas.winfo_width())
        self.canvas.configure(scrollregion=(0, 0, 0, self.interieur.winfo_reqheight()))
        if self.deborde() and not self.barre.winfo_ismapped():
            self.barre.pack(side="right", fill="y", before=self.canvas)
        elif not self.deborde() and self.barre.winfo_ismapped():
            self.barre.pack_forget()
            self.canvas.yview_moveto(0)

    def defiler(self, event):
        if not self.deborde():
            return
        if event.num in (4, 5):  # Linux
            sens = -1 if event.num == 4 else 1
        else:  # Windows et macOS
            sens = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(sens * 2, "units")


# ---------- Interface ----------

class App(tk.Tk):
    def __init__(self, base=None):
        super().__init__(className=NOM_APP)  # nom de fenêtre : relie la fenêtre à son icône dans le dock
        self.title(NOM_APP)
        self.configure(bg=FOND)
        try:
            self.icone = tk.PhotoImage(file=chemin_ressource("assets/icone.png"))
            self.iconphoto(True, self.icone)
        except tk.TclError:
            self.icone = None  # icône absente : on garde celle par défaut
        self.geometry(f"{LARGEUR_REF}x{HAUTEUR_REF}")
        self.minsize(680, 460)
        self.base = base or Base()
        self.parametres = self.base.parametres()
        self.langue = self.parametres["langue"]
        self.facteur_texte = 1.15 if self.parametres["taille_texte"] == "grande" else 1.0
        self.appliquer_theme(self.parametres["theme"])

        # Polices partagées : les modifier redimensionne tous les widgets d'un coup
        self.polices = [tkfont.nametofont(n) for n in ("TkDefaultFont", "TkTextFont", "TkHeadingFont")]
        self.gras = tkfont.Font(weight="bold")
        self.petite = tkfont.Font()
        self.petite_gras = tkfont.Font(weight="bold")
        self.titre = tkfont.Font(weight="bold")
        self.titre_barre = tkfont.Font(weight="bold")
        self.grand = tkfont.Font(weight="bold")
        self.ronds = []
        self._taille = None
        self._disposition_compacte = None
        self.styliser()
        self.bind("<Configure>", self.redimensionner)
        self.bind_all("<MouseWheel>", self.molette)
        self.bind_all("<Button-4>", self.molette)
        self.bind_all("<Button-5>", self.molette)
        self.protocol("WM_DELETE_WINDOW", self.quitter)
        self.en_attente = {}  # notes modifiées pas encore enregistrées : {matière: note}
        self.tri = self.base.tri_affichage()
        self.recherche = tk.StringVar(self)
        self.recherche.trace_add("write", self.rechercher_matieres)
        self._drag_id = None
        self._drag_cible_id = None
        self.suppression_annulable = None
        self._annulation_after = None
        self._onboarding_action = None
        self.appliquer_taille(round(TAILLE_REF * self.facteur_texte))

        self.ecran = self.zone = None
        profil = self.base.profil()
        if profil:
            self.ouvrir(*profil)
        else:
            self.ecran_niveau()

    def styliser(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=CARTE, background=CARTE, foreground=TEXTE,
                        arrowcolor=BLEU, bordercolor=LIGNE, lightcolor=CARTE, darkcolor=CARTE, padding=5)
        style.map("TCombobox", fieldbackground=[("readonly", CARTE)], selectbackground=[("readonly", CARTE)],
                  selectforeground=[("readonly", TEXTE)], bordercolor=[("focus", BLEU)])
        style.configure("Vertical.TScrollbar", background=LIGNE, troughcolor=CARTE, bordercolor=CARTE,
                        arrowcolor=DISCRET, lightcolor=LIGNE, darkcolor=LIGNE, gripcount=0)
        self.option_add("*TCombobox*Listbox.background", CARTE)
        self.option_add("*TCombobox*Listbox.selectBackground", BLEU)
        self.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")

    def appliquer_theme(self, theme):
        global FOND, CARTE, TEXTE, DISCRET, LIGNE
        global BLEU_CLAIR, BLEU_PALE, VERT_CLAIR, ROUGE_CLAIR, GRIS_CLAIR, ORANGE, ROUGE_FONCE
        if theme == "sombre":
            FOND, CARTE, TEXTE, DISCRET, LIGNE = (
                "#171b24", "#242a36", "#edf1f7", "#a7b1c0", "#3a4352")
            BLEU_CLAIR, BLEU_PALE = "#293d5d", "#d0dcf3"
            VERT_CLAIR, ROUGE_CLAIR, GRIS_CLAIR = "#1f3b2b", "#482a2e", "#343b47"
            ORANGE, ROUGE_FONCE = "#e6a84d", "#81232a"
        else:
            FOND, CARTE, TEXTE, DISCRET, LIGNE = (
                "#f3f5fb", "#ffffff", "#1f2937", "#596273", "#e3e8f2")
            BLEU_CLAIR, BLEU_PALE = "#e8eefc", "#dbe4ff"
            VERT_CLAIR, ROUGE_CLAIR, GRIS_CLAIR = "#e3f4e8", "#fde8e8", "#eef0f4"
            ORANGE, ROUGE_FONCE = "#c2700a", "#a51f1f"
        self.configure(bg=FOND)
        Bouton.STYLES = {
            "primaire": (BLEU, "#ffffff", BLEU_FONCE, "#ffffff"),
            "secondaire": (CARTE, TEXTE, BLEU_CLAIR, BLEU),
            "barre": (BLEU_FONCE, "#ffffff", BLEU_NUIT, "#ffffff"),
            "lien": (None, BLEU, None, BLEU_FONCE),
            "discret": (CARTE, DISCRET, ROUGE_CLAIR, ROUGE),
            "danger": (CARTE, ROUGE, ROUGE_CLAIR, ROUGE),
            "alerte": (ROUGE, "#ffffff", ROUGE_FONCE, "#ffffff"),
        }

    def tr(self, texte):
        if self.langue != "en":
            return texte
        traduit = TRADUCTIONS_EN.get(texte)
        if traduit is not None:
            return traduit
        correspondance = re.fullmatch(r"Étape (\d+) sur 2", texte)
        if correspondance:
            return f"Step {correspondance.group(1)} of 2"
        correspondance = re.fullmatch(r"Niveau (L[1-4])  ·  note de passage (\d+)", texte)
        if correspondance:
            return f"Level {correspondance.group(1)}  ·  pass mark {correspondance.group(2)}"
        correspondance = re.fullmatch(r"Note de passage : (.+)", texte)
        if correspondance:
            return f"Pass mark: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"Bienvenue sur (.+)", texte)
        if correspondance:
            return f"Welcome to {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La matière « (.+) » existe déjà\.", texte)
        if correspondance:
            return f"The subject “{correspondance.group(1)}” already exists."
        correspondance = re.fullmatch(r"La matière « (.+) » et sa note seront supprimées\.", texte)
        if correspondance:
            return f"The subject “{correspondance.group(1)}” and its grade will be deleted."
        correspondance = re.fullmatch(
            r"(\d+) matière\(s\) trouvée\(s\) :\n•  (\d+) nouvelle\(s\)\n•  (\d+) déjà présente\(s\)( : leur note sera remplacée)?",
            texte)
        if correspondance:
            resultat = (f"{correspondance.group(1)} subject(s) found:\n"
                        f"•  {correspondance.group(2)} new\n"
                        f"•  {correspondance.group(3)} already present")
            return resultat + ("; their grades will be replaced" if correspondance.group(4) else "")
        correspondance = re.fullmatch(r"Vos données ont été sauvegardées dans :\n(.+)", texte)
        if correspondance:
            return f"Your data was backed up to:\n{correspondance.group(1)}"
        correspondance = re.fullmatch(r"Le tri n'a pas pu être enregistré : (.+)", texte)
        if correspondance:
            return f"The sort order could not be saved: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La période n'a pas pu être activée : (.+)", texte)
        if correspondance:
            return f"The period could not be activated: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"L'ordre n'a pas pu être enregistré : (.+)", texte)
        if correspondance:
            return f"The order could not be saved: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La matière n'a pas pu être ajoutée : (.+)", texte)
        if correspondance:
            return f"The subject could not be added: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La matière n'a pas pu être supprimée : (.+)", texte)
        if correspondance:
            return f"The subject could not be deleted: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La matière n'a pas pu être restaurée : (.+)", texte)
        if correspondance:
            return f"The subject could not be restored: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"Le profil n'a pas pu être enregistré : (.+)", texte)
        if correspondance:
            return f"The profile could not be saved: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"Les données n'ont pas pu être effacées : (.+)", texte)
        if correspondance:
            return f"The data could not be cleared: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La sauvegarde n'a pas pu être créée\. L'application reste ouverte : (.+)",
                                      texte)
        if correspondance:
            return f"The backup could not be created. The app will stay open: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"La sauvegarde n'a pas pu être restaurée : (.+)", texte)
        if correspondance:
            return f"The backup could not be restored: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"Ce fichier n'a pas pu être lu : (.+)", texte)
        if correspondance:
            return f"This file could not be read: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"L'export a échoué : (.+)", texte)
        if correspondance:
            return f"Export failed: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"Fichier créé :\n(.+)", texte)
        if correspondance:
            return f"File created:\n{correspondance.group(1)}"
        correspondance = re.fullmatch(r"Les paramètres n'ont pas pu être enregistrés : (.+)", texte)
        if correspondance:
            return f"Settings could not be saved: {correspondance.group(1)}"
        if texte.startswith("L'export PDF nécessite le module fpdf2"):
            return "PDF export requires the fpdf2 module (pip install fpdf2)."
        correspondance = re.fullmatch(r"La note de « (.+) » n'a pas pu être enregistrée : (.+)", texte)
        if correspondance:
            return f"The grade for “{correspondance.group(1)}” could not be saved: {correspondance.group(2)}"
        correspondance = re.fullmatch(r"Le bulletin n'a pas pu être importé en entier : (.+)", texte)
        if correspondance:
            return f"The report could not be imported completely: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"Matières? sous (\d+)", texte)
        if correspondance:
            singulier = texte.startswith("Matière sous")
            return f"Subject{'s' if not singulier else ''} below {correspondance.group(1)}"
        correspondance = re.fullmatch(r"En attente : (\d+)", texte)
        if correspondance:
            return f"Pending: {correspondance.group(1)}"
        correspondance = re.fullmatch(r"● (\d+) notes? non enregistrées?  ·  Entrée pour valider", texte)
        if correspondance:
            nombre = correspondance.group(1)
            return f"● {nombre} unsaved grade{'s' if nombre != '1' else ''}  ·  Enter to save"
        correspondance = re.fullmatch(r"✓ Note de (.+) enregistrée", texte)
        if correspondance:
            return f"✓ Grade for {correspondance.group(1)} saved"
        correspondance = re.fullmatch(r"✓ (\d+) notes enregistrées", texte)
        if correspondance:
            return f"✓ {correspondance.group(1)} grades saved"
        correspondance = re.fullmatch(r"✓ (.+) supprimée", texte)
        if correspondance:
            return f"✓ {correspondance.group(1)} deleted"
        correspondance = re.fullmatch(r"✓ (.+) restaurée", texte)
        if correspondance:
            return f"✓ {correspondance.group(1)} restored"
        return texte

    def tr_periode(self, nom):
        return self.tr(nom) if nom in (
            PERIODE_PREMIERE_SESSION, PERIODE_DEUXIEME_SESSION, "Période actuelle") else nom

    # --- Mise à l'échelle ---

    def redimensionner(self, event):
        if event.widget is not self:
            return
        echelle = min(event.width / LARGEUR_REF, event.height / HAUTEUR_REF)
        self.appliquer_taille(max(9, min(26, round(TAILLE_REF * echelle * self.facteur_texte))))
        self._adapter_disposition(event.width)

    def appliquer_taille(self, taille):
        if taille == self._taille:
            return
        self._taille = taille
        for p in self.polices + [self.gras]:
            p.configure(size=taille)
        self.petite.configure(size=max(9, taille - 2))
        self.petite_gras.configure(size=max(9, taille - 2))
        self.titre.configure(size=round(taille * 1.7))
        self.titre_barre.configure(size=round(taille * 1.3))
        self.grand.configure(size=round(taille * 2))
        self.ronds = [r for r in self.ronds if r.winfo_exists()]
        for r in self.ronds:
            r.redessiner()

    def _adapter_disposition(self, largeur):
        if not hasattr(self, "entete_actions"):
            return
        compacte = largeur < LARGEUR_COMPACTE
        if compacte == self._disposition_compacte:
            return
        self._disposition_compacte = compacte
        if compacte:
            self.entete_actions.grid_configure(row=1, column=0, columnspan=2, sticky="e", pady=(8, 0))
            if hasattr(self, "ligne_recherche") and self.ligne_recherche.winfo_exists():
                self.ligne_recherche.grid_configure(row=1, column=0, columnspan=2, sticky="w",
                                                    padx=0, pady=(8, 0))
            self.corps.configure(padx=12)
            self.entete.configure(padx=14)
        else:
            self.entete_actions.grid_configure(row=0, column=1, columnspan=1, sticky="e", pady=0)
            if hasattr(self, "ligne_recherche") and self.ligne_recherche.winfo_exists():
                self.ligne_recherche.grid_configure(row=0, column=1, columnspan=1, sticky="e",
                                                    padx=(14, 0), pady=0)
            self.corps.configure(padx=24)
            self.entete.configure(padx=20)

    def molette(self, event):
        if self.zone and self.zone.winfo_exists():
            sous = self.winfo_containing(event.x_root, event.y_root)
            if sous is not None and str(sous).startswith(str(self.zone)):
                self.zone.defiler(event)

    # --- Petits outils ---

    def nouvel_ecran(self):
        if self.ecran:
            self.ecran.destroy()
        self.zone = None
        self.ecran = tk.Frame(self, bg=FOND)
        self.ecran.pack(fill="both", expand=True)
        return self.ecran

    def carte(self, parent, **pack):
        cadre = tk.Frame(parent, bg=CARTE, highlightthickness=1, highlightbackground=LIGNE, highlightcolor=LIGNE)
        if pack:
            cadre.pack(**pack)
        return cadre

    def texte(self, parent, texte, font=None, fg=None, traduire=True, **options):
        if traduire:
            texte = self.tr(texte)
        if fg is None:
            fg = TEXTE
        return tk.Label(parent, text=texte, font=font, fg=fg, bg=parent.cget("bg"), **options)

    def champ(self, parent, width=24, justify="left", **options):
        return tk.Entry(parent, width=width, justify=justify, relief="flat", bd=0, bg=CARTE, fg=TEXTE,
                        insertbackground=TEXTE, highlightthickness=1, highlightbackground=LIGNE,
                        highlightcolor=BLEU, selectbackground=BLEU_CLAIR, selectforeground=TEXTE, **options)

    def rond(self, parent, commande, echelle=1.9):
        bouton = BoutonRond(parent, commande, self.polices[0], echelle)
        self.ronds.append(bouton)
        return bouton

    def dialogue(self, titre, parent=None):
        fen = tk.Toplevel(self, bg=CARTE)
        fen.title(self.tr(titre))
        fen.transient(parent or self)
        fen.resizable(False, False)
        cadre = tk.Frame(fen, bg=CARTE, padx=24, pady=20)
        cadre.pack(fill="both", expand=True)
        fen.bind("<Escape>", lambda e: fen.destroy())
        return fen, cadre

    def afficher_dialogue(self, fen):
        fen.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - fen.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height() - fen.winfo_reqheight()) // 3
        fen.geometry(f"+{max(0, x)}+{max(0, y)}")
        fen.grab_set()

    def message(self, titre, texte, boutons, genre="question", parent=None):
        """Boîte de dialogue assortie à l'application ; renvoie la valeur du bouton cliqué (None si fermée)."""
        fen, cadre = self.dialogue(titre, parent)
        couleur, symbole = {"question": (BLEU, "?"), "attention": (ORANGE, "!"), "danger": (ROUGE, "!"),
                            "erreur": (ROUGE, "✕"), "info": (BLEU, "i"), "succes": (VERT, "✓")}[genre]
        haut = tk.Frame(cadre, bg=CARTE)
        haut.pack(fill="x")
        d = int(self.polices[0].metrics("linespace") * 2.4)
        pastille = tk.Canvas(haut, width=d, height=d, bg=CARTE, highlightthickness=0)
        pastille.create_oval(1, 1, d - 1, d - 1, fill=couleur, outline="")
        pastille.create_text(d / 2, d / 2, text=symbole, fill="#ffffff", font=self.titre_barre)
        pastille.pack(side="left", anchor="n", padx=(0, 16))
        textes = tk.Frame(haut, bg=CARTE)
        textes.pack(side="left", fill="x")
        self.texte(textes, titre, font=self.titre_barre).pack(anchor="w")
        self.texte(textes, texte, fg=DISCRET, justify="left", wraplength=self._taille * 34).pack(anchor="w", pady=(4, 0))

        resultat = []

        def choisir(valeur):
            resultat.append(valeur)
            fen.destroy()

        bas = tk.Frame(cadre, bg=CARTE)
        bas.pack(fill="x", pady=(22, 0))
        for libelle, valeur, style in reversed(boutons):
            Bouton(bas, libelle, lambda v=valeur: choisir(v), style).pack(side="right", padx=(8, 0))
        fen.bind("<Return>", lambda e: choisir(boutons[-1][1]))
        self.afficher_dialogue(fen)
        self.wait_window(fen)
        if parent is not None and parent.winfo_exists():
            parent.grab_set()
        return resultat[0] if resultat else None

    def confirmer(self, titre, texte, oui="Oui", danger=False, parent=None):
        return self.message(titre, texte, [("Annuler", False, "secondaire"),
                                           (oui, True, "alerte" if danger else "primaire")],
                            "danger" if danger else "question", parent) is True

    def informer(self, titre, texte, genre="info", parent=None):
        self.message(titre, texte, [("OK", True, "primaire")], genre, parent)

    def demander_texte(self, titre, question, valider="Valider"):
        fen, cadre = self.dialogue(titre)
        self.texte(cadre, question, font=self.gras).pack(anchor="w")
        saisie = self.champ(cadre, width=30)
        saisie.pack(fill="x", pady=(8, 16), ipady=5)
        saisie.focus_set()
        resultat = []

        def ok():
            resultat.append(saisie.get().strip())
            fen.destroy()

        saisie.bind("<Return>", lambda e: ok())
        boutons = tk.Frame(cadre, bg=CARTE)
        boutons.pack(fill="x")
        Bouton(boutons, valider, ok).pack(side="right")
        Bouton(boutons, "Annuler", fen.destroy, "secondaire").pack(side="right", padx=8)
        self.afficher_dialogue(fen)
        self.wait_window(fen)
        return resultat[0] if resultat else ""

    # --- Premier lancement : niveau puis nom ---

    def carte_accueil(self, etape):
        carte = self.carte(self.nouvel_ecran())
        carte.place(relx=0.5, rely=0.47, anchor="center")
        cadre = tk.Frame(carte, bg=CARTE, padx=48, pady=32)
        cadre.pack()
        if self.icone:
            self.icone_accueil = self.icone.subsample(8)
            tk.Label(cadre, image=self.icone_accueil, bg=CARTE).pack()
        self.texte(cadre, f"Bienvenue sur {NOM_APP}", font=self.titre).pack(pady=(10, 2))
        self.texte(cadre, "Calculez votre moyenne et suivez vos reprises.", fg=DISCRET).pack()
        Bouton(cadre, "Paramètres", self.fenetre_parametres, "lien", font=self.petite).pack(
            anchor="e", pady=(4, 0))
        self.texte(cadre, f"Étape {etape} sur 2", font=self.petite_gras, fg=BLEU).pack(pady=(22, 4))
        return cadre

    def ecran_niveau(self, nom=""):
        self._onboarding_action = lambda: self.ecran_niveau(nom)
        cadre = self.carte_accueil(1)
        self.texte(cadre, "Quel est votre niveau ?", font=self.gras).pack()
        niveau = ttk.Combobox(cadre, state="readonly", values=list(NIVEAUX), width=10, justify="center",
                              font=self.polices[0])
        niveau.pack(pady=10)
        info = self.texte(cadre, " ", font=self.petite, fg=DISCRET)
        info.pack()
        niveau.bind("<<ComboboxSelected>>",
                    lambda e: info.config(text=self.tr(f"Note de passage : {NIVEAUX[niveau.get()]}")))

        def suivant():
            if not niveau.get():
                self.informer("Niveau", "Choisissez votre niveau dans la liste.", "attention")
                return
            self.ecran_nom(niveau.get(), nom)

        Bouton(cadre, "Suivant  →", suivant, padx=22, pady=8).pack(pady=(18, 0))

    def ecran_nom(self, niveau, nom=""):
        cadre = self.carte_accueil(2)
        self.texte(cadre, "Quel est votre nom ?", font=self.gras).pack()
        saisie = self.champ(cadre, width=26, justify="center")
        saisie.insert(0, nom)
        saisie.pack(pady=12, ipady=6)
        self._onboarding_action = lambda: self.ecran_nom(niveau, saisie.get())
        saisie.focus_set()
        self.texte(cadre, f"Niveau {niveau}  ·  note de passage {NIVEAUX[niveau]}",
                   font=self.petite, fg=DISCRET).pack()

        def commencer():
            saisi = saisie.get().strip()
            if not saisi:
                self.informer("Nom", "Entrez votre nom.", "attention")
                return
            try:
                self.base.enregistrer_profil(niveau, saisi)
            except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
                self.informer("Profil impossible", f"Le profil n'a pas pu être enregistré : {err}", "erreur")
                return
            self.ouvrir(niveau, saisi)
            self.after(300, self.fenetre_aide)  # premier lancement : on montre le mode d'emploi

        saisie.bind("<Return>", lambda e: commencer())
        boutons = tk.Frame(cadre, bg=CARTE)
        boutons.pack(pady=(18, 0))
        Bouton(boutons, "←  Retour", lambda: self.ecran_niveau(saisie.get()), "secondaire",
               padx=18, pady=8).pack(side="left", padx=5)
        Bouton(boutons, "Commencer", commencer, padx=22, pady=8).pack(side="left", padx=5)

    # --- Écran principal ---

    def ouvrir(self, niveau, nom):
        self.niveau, self.nom = niveau, nom
        self.passage = NIVEAUX[niveau]
        self.tri = self.base.tri_affichage()
        self.periode = self.base.periode_active()
        self.matieres = self.base.matieres(self.periode["id"])
        ecran = self.nouvel_ecran()

        entete = tk.Frame(ecran, bg=BLEU, padx=20, pady=12)
        entete.pack(fill="x")
        entete.columnconfigure(0, weight=1)
        titres = tk.Frame(entete, bg=BLEU)
        titres.grid(row=0, column=0, sticky="w")
        if self.icone:
            self.icone_barre = self.icone.subsample(14)
            tk.Label(titres, image=self.icone_barre, bg=BLEU).pack(side="left", padx=(0, 12))
        textes_entete = tk.Frame(titres, bg=BLEU)
        textes_entete.pack(side="left")
        self.texte(textes_entete, NOM_APP, font=self.titre_barre, fg="#ffffff").pack(anchor="w")
        resume_entete = (f"{nom}  ·  {niveau}  ·  {self.tr_periode(self.periode['nom'])}  ·  "
                         f"{self.tr('Note de passage')}: {self.passage}")
        self.texte(textes_entete, resume_entete, font=self.petite, fg=BLEU_PALE, traduire=False).pack(anchor="w")
        self.entete = entete
        self.entete_actions = tk.Frame(entete, bg=BLEU)
        self.entete_actions.grid(row=0, column=1, sticky="e")
        for texte, commande in (("Mode d'emploi", self.fenetre_aide), ("Profil", self.fenetre_profil),
                                ("Exporter", self.fenetre_export), ("Importer", self.importer),
                                ("Sauvegardes", self.fenetre_sauvegardes)):
            Bouton(self.entete_actions, texte, commande, "barre", padx=8).pack(side="right", padx=2)

        self.corps = tk.Frame(ecran, bg=FOND, padx=24, pady=18)
        self.corps.pack(fill="both", expand=True)
        self._disposition_compacte = None
        self.dessiner()
        self._adapter_disposition(self.winfo_width())

    def dessiner(self, focus=None):
        self._disposition_compacte = None
        for w in self.corps.winfo_children():
            w.destroy()
        self.zone = None

        barre_periode = tk.Frame(self.corps, bg=FOND)
        barre_periode.pack(fill="x", pady=(0, 10))
        self.texte(barre_periode, "Période :", font=self.petite_gras,
                   fg=DISCRET).pack(side="left", padx=(0, 8))
        self.choix_periode = ttk.Combobox(
            barre_periode, state="readonly", values=[self.tr_periode(p["nom"]) for p in self.base.periodes()],
            width=22, font=self.petite)
        self.choix_periode.set(self.tr_periode(self.periode["nom"]))
        self.choix_periode.pack(side="left")
        self.choix_periode.bind("<<ComboboxSelected>>", self.changer_periode)
        Bouton(barre_periode, "Gérer les périodes…", self.fenetre_periodes,
               "lien", font=self.petite).pack(side="left", padx=(8, 0))
        Bouton(barre_periode, "Paramètres", self.fenetre_parametres,
               "lien", font=self.petite).pack(side="right")

        if not self.matieres:  # interface vierge : un grand bouton + au milieu
            vide = tk.Frame(self.corps, bg=FOND)
            vide.place(relx=0.5, rely=0.42, anchor="center")
            self.rond(vide, self.ajouter_matiere, echelle=3.4).pack()
            self.texte(vide, "Ajoutez votre première matière", font=self.gras).pack(pady=(14, 2))
            self.texte(vide, "Cliquez sur le bouton + pour commencer", font=self.petite, fg=DISCRET).pack()
            Bouton(vide, "ou importer un bulletin (CSV)…", self.importer, "lien", font=self.petite).pack(pady=(10, 0))
            self.bouton_annuler = None
            if self.suppression_annulable:
                self.bouton_annuler = Bouton(vide, "Annuler la suppression", self.annuler_suppression,
                                             "secondaire", font=self.petite)
                self.bouton_annuler.pack(pady=(8, 0))
            self._adapter_disposition(self.winfo_width())
            return

        # Résumé : trois cartes
        resume = tk.Frame(self.corps, bg=FOND)
        resume.pack(fill="x", pady=(0, 14))
        self.cartes = {}
        for i, cle in enumerate(("moyenne", "reprises", "notees")):
            carte = self.carte(resume)
            carte.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 2 else 7))
            resume.columnconfigure(i, weight=1, uniform="cartes")
            interieur = tk.Frame(carte, bg=CARTE, padx=16, pady=10)
            interieur.pack(fill="both")
            titre = {"moyenne": "MOYENNE", "reprises": "REPRISES", "notees": "MATIÈRES NOTÉES"}[cle]
            self.texte(interieur, titre, font=self.petite_gras, fg=DISCRET).pack(anchor="w")
            valeur = self.texte(interieur, "", font=self.grand)
            valeur.pack(anchor="w")
            detail = self.texte(interieur, "", font=self.petite, fg=DISCRET)
            detail.pack(anchor="w")
            self.cartes[cle] = (valeur, detail)

        commande_tri = tk.Frame(self.corps, bg=FOND)
        commande_tri.pack(fill="x", pady=(0, 8))
        commande_tri.columnconfigure(1, weight=1)
        ligne_tri = tk.Frame(commande_tri, bg=FOND)
        ligne_recherche = tk.Frame(commande_tri, bg=FOND)
        self.ligne_tri = ligne_tri
        self.ligne_recherche = ligne_recherche
        self.texte(ligne_tri, "Trier :", font=self.petite_gras,
                   fg=DISCRET).pack(side="left", padx=(0, 8))
        self.choix_tri = ttk.Combobox(ligne_tri, state="readonly",
                                      values=[self.tr(option) for option in OPTIONS_TRI],
                                      width=25, font=self.petite)
        self.choix_tri.set(self.tr(self.tri))
        self.choix_tri.pack(side="left")
        self.choix_tri.bind("<<ComboboxSelected>>", self.changer_tri)
        self.texte(ligne_tri, "≡ déplacer", font=self.petite, fg=DISCRET).pack(side="left", padx=(8, 0))
        self.texte(ligne_recherche, "Rechercher :", font=self.petite_gras,
                   fg=DISCRET).pack(side="left", padx=(0, 6))
        self.champ(ligne_recherche, width=17, textvariable=self.recherche).pack(side="left", ipady=3)
        ligne_tri.grid(row=0, column=0, sticky="w")
        ligne_recherche.grid(row=0, column=1, sticky="e", padx=(14, 0))

        # Tableau des matières (défile s'il y en a beaucoup)
        carte = self.carte(self.corps, fill="both", expand=True)
        self.zone = ZoneDefilante(carte, CARTE)
        self.zone.pack(fill="both", expand=True, padx=1, pady=1)
        self.dessiner_liste()

        pied = tk.Frame(self.corps, bg=FOND)
        pied.pack(fill="x", pady=(10, 0))
        self.texte(pied, f"{NULL} = note pas encore connue, non comptée dans la moyenne",
                   font=self.petite, fg=DISCRET).pack(side="left")
        Bouton(pied, "Enregistrer", self.enregistrer, padx=18).pack(side="right")
        self.bouton_annuler = Bouton(pied, "Annuler", self.annuler_suppression, "secondaire", padx=12)
        if self.suppression_annulable:
            self.bouton_annuler.pack(side="right", padx=(0, 8))
        self.lbl_etat = self.texte(pied, "", font=self.petite_gras)
        self.lbl_etat.pack(side="right", padx=12)
        self.maj()

        if focus in self.lignes:  # nouvelle matière : on descend et on place le curseur dans sa note
            self.update_idletasks()
            self.zone.ajuster()
            self.zone.canvas.yview_moveto(1)
            self.lignes[focus][0].focus_set()
        self._adapter_disposition(self.winfo_width())

    def matieres_affichees(self):
        return filtrer_matieres(trier_matieres(self.matieres, self.tri), self.recherche.get())

    def dessiner_liste(self):
        t = self.zone.interieur
        for widget in t.winfo_children():
            widget.destroy()
        t.columnconfigure(1, weight=1)
        pad = dict(padx=14)
        for j, texte in enumerate(("", "MATIÈRE", "COEF", "NOTE", "STATUT", "")):
            if texte:
                self.texte(t, texte, font=self.petite_gras, fg=DISCRET).grid(
                    row=0, column=j, sticky="w" if j == 1 else "", pady=(12, 8), **pad)

        self.lignes = {}
        self.poignees = {}
        self.libelles_matieres = {}
        matieres = self.matieres_affichees()
        for i, m in enumerate(matieres):
            r = 2 * i + 1
            tk.Frame(t, bg=LIGNE, height=1).grid(row=r, column=0, columnspan=6, sticky="ew")
            poignee = tk.Canvas(t, width=20, height=20, bg=CARTE, highlightthickness=0, cursor="hand2")
            poignee.create_line(5, 7, 15, 7, fill=DISCRET, width=2)
            poignee.create_line(5, 13, 15, 13, fill=DISCRET, width=2)
            poignee.grid(row=r + 1, column=0, padx=(8, 0))
            poignee.bind("<ButtonPress-1>", lambda e, m=m: self.commencer_deplacement(m))
            poignee.bind("<B1-Motion>", self.suivre_deplacement)
            poignee.bind("<ButtonRelease-1>", self.terminer_deplacement)
            self.poignees[m["id"]] = poignee

            libelle = self.texte(t, m["nom"], anchor="w", traduire=False)
            libelle.grid(row=r + 1, column=1, sticky="ew", pady=7, **pad)
            self.libelles_matieres[m["id"]] = libelle
            self.texte(t, f"{m['coef']:g}", fg=DISCRET).grid(row=r + 1, column=2, **pad)
            var = tk.StringVar(value=NULL if m["note"] is None else f"{m['note']:g}")
            saisie = self.champ(t, width=7, justify="center", textvariable=var, validate="key",
                                validatecommand=(self.register(saisie_autorisee), "%P"))
            saisie.grid(row=r + 1, column=3, ipady=4, **pad)
            saisie.bind("<FocusIn>", lambda e, c=saisie: c.select_range(0, "end"))
            saisie.bind("<FocusOut>", lambda e, v=var: v.set(NULL) if v.get().strip() == "" else None)
            var.trace_add("write", lambda *_, m=m, v=var: self.changer_note(m, v))
            saisie.bind("<Return>", lambda e, m=m: self.valider_note(m))
            saisie.bind("<KP_Enter>", lambda e, m=m: self.valider_note(m))
            pastille = tk.Label(t, font=self.petite_gras, padx=10, pady=2, width=10)
            pastille.grid(row=r + 1, column=4, **pad)
            Bouton(t, "✕", lambda m=m: self.supprimer_matiere(m), "discret", padx=8, pady=2).grid(
                row=r + 1, column=5, padx=(0, 10))
            self.lignes[m["nom"]] = (saisie, pastille)

        if not matieres:
            self.texte(t, "Aucune matière ne correspond à cette recherche.",
                       font=self.petite, fg=DISCRET).grid(
                row=1, column=0, columnspan=6, pady=(18, 4))
            Bouton(t, "Effacer la recherche", lambda: self.recherche.set(""),
                   "lien", font=self.petite).grid(row=2, column=0, columnspan=6)
            fin = 3
        else:
            fin = 2 * len(matieres) + 1
        tk.Frame(t, bg=LIGNE, height=1).grid(row=fin, column=0, columnspan=6, sticky="ew")
        self.rond(t, self.ajouter_matiere).grid(row=fin + 1, column=0, columnspan=6, pady=12)

    def rechercher_matieres(self, *_):
        if not self.zone or not self.zone.winfo_exists():
            return
        self.dessiner_liste()
        self.zone.canvas.yview_moveto(0)
        self.maj()

    def changer_tri(self, _event=None):
        tri_precedent = self.tri
        nouveau_tri = next((option for option in OPTIONS_TRI
                            if self.tr(option) == self.choix_tri.get()), None)
        if nouveau_tri is None:
            self.choix_tri.set(self.tr(tri_precedent))
            return
        try:
            self.base.enregistrer_tri(nouveau_tri)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.choix_tri.set(self.tr(tri_precedent))
            self.informer("Tri impossible", f"Le tri n'a pas pu être enregistré : {err}", "erreur")
            return
        self.tri = nouveau_tri
        self.dessiner()

    def changer_periode(self, _event=None):
        periode = next((p for p in self.base.periodes()
                        if self.tr_periode(p["nom"]) == self.choix_periode.get()), None)
        if periode is None:
            raise ValueError(f"Période inconnue : {self.choix_periode.get()}")
        if periode["id"] == self.periode["id"]:
            return
        try:
            if not self.enregistrer(silencieux=True):
                self.choix_periode.set(self.tr_periode(self.periode["nom"]))
                return
            self.base.activer_periode(periode["id"])
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.informer("Changement impossible", f"La période n'a pas pu être activée : {err}", "erreur")
            self.choix_periode.set(self.tr_periode(self.periode["nom"]))
            return
        self._effacer_annulation()
        self.en_attente.clear()
        self.recherche.set("")
        self.ouvrir(*self.base.profil())

    def fenetre_periodes(self):
        fen, cadre = self.dialogue("Gérer les périodes")
        self.texte(cadre, "Créez une période ou choisissez-en une pour la renommer ou la supprimer.",
                   fg=DISCRET, justify="left", wraplength=420).pack(anchor="w")
        liste_cadre = tk.Frame(cadre, bg=CARTE)
        liste_cadre.pack(fill="x", pady=(10, 12))
        liste = tk.Listbox(liste_cadre, height=6, width=42, exportselection=False,
                           relief="flat", bg=CARTE, fg=TEXTE, selectbackground=BLEU,
                           selectforeground="#ffffff", highlightthickness=1,
                           highlightbackground=LIGNE, font=self.polices[0])
        defilement = ttk.Scrollbar(liste_cadre, orient="vertical", command=liste.yview)
        liste.configure(yscrollcommand=defilement.set)
        liste.pack(side="left", fill="x", expand=True)
        defilement.pack(side="right", fill="y")
        self.texte(cadre, "Nom de la période", font=self.petite_gras).pack(anchor="w")
        nom = self.champ(cadre, width=34)
        nom.pack(fill="x", pady=(4, 12), ipady=4)
        etat = {"periodes": []}

        def rafraichir(selection_id=None):
            etat["periodes"] = self.base.periodes()
            active_id = self.base.periode_active()["id"]
            liste.delete(0, "end")
            selection = 0
            for i, periode in enumerate(etat["periodes"]):
                suffixe = f"  ({self.tr('active')})" if periode["id"] == active_id else ""
                liste.insert("end", self.tr_periode(periode["nom"]) + suffixe)
                if periode["id"] == (selection_id or active_id):
                    selection = i
            if etat["periodes"]:
                liste.selection_set(selection)
                liste.see(selection)
                nom.delete(0, "end")
                nom.insert(0, etat["periodes"][selection]["nom"])

        def periode_selectionnee():
            selection = liste.curselection()
            return etat["periodes"][selection[0]] if selection else None

        def mettre_nom_selection():
            periode = periode_selectionnee()
            if periode:
                nom.delete(0, "end")
                nom.insert(0, periode["nom"])

        def creer():
            try:
                if not self.enregistrer(silencieux=True):
                    return
                self.base.ajouter_periode(nom.get())
            except (OSError, sqlite3.Error, ValueError) as err:
                self.informer("Création impossible", str(err), "erreur", parent=fen)
                return
            self._effacer_annulation()
            self.en_attente.clear()
            self.recherche.set("")
            self.ouvrir(*self.base.profil())
            rafraichir(self.periode["id"])

        def renommer():
            periode = periode_selectionnee()
            if not periode:
                self.informer("Périodes", "Sélectionnez une période.", "attention", parent=fen)
                return
            try:
                if periode["id"] == self.periode["id"]:
                    if not self.enregistrer(silencieux=True):
                        return
                self.base.renommer_periode(periode["id"], nom.get())
            except (OSError, sqlite3.Error, ValueError) as err:
                self.informer("Renommage impossible", str(err), "erreur", parent=fen)
                return
            if periode["id"] == self.periode["id"]:
                self.ouvrir(*self.base.profil())
            rafraichir(periode["id"])

        def supprimer():
            periode = periode_selectionnee()
            if not periode:
                self.informer("Périodes", "Sélectionnez une période.", "attention", parent=fen)
                return
            nombre = len(self.base.matieres(periode["id"]))
            detail = (f" ainsi que ses {nombre} matière(s) et leurs notes" if nombre
                      else " (elle est vide)")
            if not self.confirmer("Supprimer cette période ?",
                                  f"La période « {periode['nom']} »{detail} sera supprimée définitivement.",
                                  "Supprimer", danger=True, parent=fen):
                return
            try:
                if periode["id"] == self.periode["id"]:
                    if not self.enregistrer(silencieux=True):
                        return
                self.base.supprimer_periode(periode["id"])
            except (OSError, sqlite3.Error, ValueError) as err:
                self.informer("Suppression impossible", str(err), "erreur", parent=fen)
                return
            if periode["id"] == self.periode["id"]:
                self._effacer_annulation()
                self.en_attente.clear()
                self.recherche.set("")
                self.ouvrir(*self.base.profil())
            rafraichir(self.base.periode_active()["id"])

        liste.bind("<<ListboxSelect>>", lambda e: mettre_nom_selection())
        boutons = tk.Frame(cadre, bg=CARTE)
        boutons.pack(fill="x")
        Bouton(boutons, "Créer et activer", creer, padx=10).pack(side="left")
        Bouton(boutons, "Renommer", renommer, "secondaire", padx=10).pack(side="left", padx=6)
        Bouton(boutons, "Supprimer", supprimer, "danger", padx=10).pack(side="left")
        Bouton(cadre, "Fermer", fen.destroy, "lien").pack(pady=(12, 0))
        rafraichir()
        self.afficher_dialogue(fen)

    def commencer_deplacement(self, matiere):
        self._drag_id = matiere["id"]
        self._drag_cible_id = matiere["id"]
        self.poignees[matiere["id"]].configure(bg=BLEU_CLAIR)
        return "break"

    def cible_deplacement(self, event):
        visibles = self.matieres_affichees()
        haut = self.zone.canvas.winfo_rooty()
        bas = haut + self.zone.canvas.winfo_height()
        candidats = []
        for index, matiere in enumerate(visibles):
            libelle = self.libelles_matieres[matiere["id"]]
            centre = libelle.winfo_rooty() + libelle.winfo_height() / 2
            if haut <= centre <= bas:
                candidats.append((index, centre, matiere))
        if not candidats:
            return None
        index, _, matiere = min(candidats, key=lambda item: abs(item[1] - event.y_root))
        return index, matiere

    def suivre_deplacement(self, event):
        if self._drag_id is None:
            return
        cible = self.cible_deplacement(event)
        if cible is None:
            return "break"
        id_cible = cible[1]["id"]
        if id_cible != self._drag_cible_id:
            if self._drag_cible_id in self.libelles_matieres:
                self.libelles_matieres[self._drag_cible_id].configure(bg=CARTE)
            self._drag_cible_id = id_cible
            self.libelles_matieres[id_cible].configure(bg=BLEU_CLAIR)
        return "break"

    def terminer_deplacement(self, event):
        drag_id = self._drag_id
        self._drag_id = None
        self._drag_cible_id = None
        if drag_id is None:
            return

        cible = self.cible_deplacement(event)
        for libelle in self.libelles_matieres.values():
            libelle.configure(bg=CARTE)
        if drag_id in self.poignees:
            self.poignees[drag_id].configure(bg=CARTE)
        if cible is None:
            return "break"

        visibles = self.matieres_affichees()
        index_cible, matiere_cible = cible
        if matiere_cible["id"] == drag_id:
            return "break"

        ordre_visible = deplacer_matiere(visibles, drag_id, index_cible)
        ids_visibles = {m["id"] for m in visibles}
        ordre_personnalise = iter(ordre_visible)
        nouvelles_matieres = [
            next(ordre_personnalise) if m["id"] in ids_visibles else m for m in self.matieres]
        try:
            self.base.enregistrer_ordre(nouvelles_matieres)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.matieres = self.base.matieres()
            self.dessiner()
            self.informer("Déplacement impossible", f"L'ordre n'a pas pu être enregistré : {err}", "erreur")
            return "break"
        self.matieres = nouvelles_matieres
        self.tri = TRI_PERSONNALISE
        try:
            self.base.enregistrer_tri(self.tri)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.matieres = self.base.matieres()
            self.tri = self.base.tri_affichage()
            self.dessiner()
            self.informer("Déplacement impossible", f"L'ordre n'a pas pu être enregistré : {err}", "erreur")
            return "break"
        self.dessiner()
        return "break"

    def maj(self):
        """Met à jour couleurs, statuts et cartes de résumé."""
        pastilles = {"Validé": (VERT, VERT_CLAIR), "Reprise": (ROUGE, ROUGE_CLAIR), "En attente": (DISCRET, GRIS_CLAIR)}
        for m in self.matieres:
            if m["nom"] not in self.lignes:
                continue
            saisie, pastille = self.lignes[m["nom"]]
            etat = statut(m["note"], self.passage)
            couleur, fond = pastilles[etat]
            saisie.config(fg=couleur if m["note"] is not None else DISCRET,
                          highlightbackground=ORANGE if m["nom"] in self.en_attente else LIGNE)
            pastille.config(text=self.tr(etat), fg=couleur, bg=fond)

        moy = moyenne(self.matieres)
        valeur, detail = self.cartes["moyenne"]
        valeur.config(text="—" if moy is None else fmt(moy, 2),
                      fg=DISCRET if moy is None else (VERT if moy >= self.passage else ROUGE))
        detail.config(text=self.tr(f"Note de passage : {self.passage}"))

        n = nb_reprises(self.matieres, self.passage)
        valeur, detail = self.cartes["reprises"]
        valeur.config(text=str(n), fg=VERT if n == 0 else ROUGE)
        detail.config(text=self.tr("Aucune reprise") if n == 0 else
                      self.tr(f"Matière{'s' if n > 1 else ''} sous {self.passage}"))

        notees = sum(1 for m in self.matieres if m["note"] is not None)
        valeur, detail = self.cartes["notees"]
        valeur.config(text=f"{notees} / {len(self.matieres)}", fg=TEXTE)
        attente = len(self.matieres) - notees
        detail.config(text=self.tr("Toutes notées") if attente == 0 else
                      self.tr(f"En attente : {attente}"))
        self.maj_etat()

    def maj_etat(self, message=None):
        if not getattr(self, "lbl_etat", None) or not self.lbl_etat.winfo_exists():
            return
        if self.en_attente:
            n = len(self.en_attente)
            texte = (f"● {n} note{'s' if n > 1 else ''} non enregistrée{'s' if n > 1 else ''}"
                     "  ·  Entrée pour valider")
            self.lbl_etat.config(text=self.tr(texte), fg=ORANGE)
        else:
            self.lbl_etat.config(text=self.tr(message or "✓ Tout est enregistré"), fg=VERT)

    def changer_note(self, matiere, var):
        try:
            note = lire_note(var.get())
        except ValueError:
            return  # saisie en cours ou invalide : on garde l'ancienne valeur
        if note == matiere["note"]:
            return
        matiere["note"] = note
        self.en_attente[matiere["nom"]] = note
        self.maj()

    def valider_note(self, matiere):
        """Entrée dans une case Note : enregistre la note et passe à la matière suivante."""
        if not self.enregistrer([matiere["nom"]]):
            return
        noms = list(self.lignes)
        index = noms.index(matiere["nom"])
        if index + 1 < len(noms):
            self.lignes[noms[index + 1]][0].focus_set()
        else:
            self.focus_set()

    def enregistrer(self, noms=None, silencieux=False):
        """Écrit dans la base les notes modifiées (toutes, ou seulement celles de `noms`)."""
        ordre_avant = list(getattr(self, "lignes", {}))
        for saisie, _ in getattr(self, "lignes", {}).values():  # case laissée vide : on affiche NULL
            if saisie.winfo_exists() and not saisie.get().strip():
                saisie.delete(0, "end")
                saisie.insert(0, NULL)
        noms = [n for n in (noms if noms is not None else list(self.en_attente)) if n in self.en_attente]
        for nom in noms:
            try:
                self.base.changer_note(nom, self.en_attente[nom])
            except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
                self.informer("Enregistrement impossible",
                              f"La note de « {nom} » n'a pas pu être enregistrée : {err}", "erreur")
                return False
            self.en_attente.pop(nom)
        if silencieux or not getattr(self, "lignes", None):
            return True
        ordre_apres = [m["nom"] for m in self.matieres_affichees()]
        if ordre_apres != ordre_avant:
            self.dessiner()
        else:
            self.maj()
        if len(noms) == 1:
            self.maj_etat(f"✓ Note de {noms[0]} enregistrée")
        elif noms:
            self.maj_etat(f"✓ {len(noms)} notes enregistrées")
        else:
            self.maj_etat("✓ Tout est déjà enregistré")
        return True

    def quitter(self):
        if self.en_attente:
            choix = self.message("Notes non enregistrées",
                                 "Certaines notes ont été modifiées mais pas enregistrées.",
                                 [("Annuler", None, "secondaire"), ("Ne pas enregistrer", False, "secondaire"),
                                  ("Enregistrer", True, "primaire")], "attention")
            if choix is None:
                return
            if choix:
                if not self.enregistrer(silencieux=True):
                    return
        try:
            sauvegarde = self.base.sauvegarder_fermeture()
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.informer("Sauvegarde impossible",
                          f"La sauvegarde n'a pas pu être créée. L'application reste ouverte : {err}",
                          "erreur")
            return
        if sauvegarde and self.parametres["message_sauvegarde"] == "oui":
            self.informer("Sauvegarde effectuée",
                          f"Vos données ont été sauvegardées dans :\n{sauvegarde.name}", "succes")
        self.destroy()

    def ajouter_matiere(self):
        nom = self.demander_texte("Nouvelle matière", "Nom de la matière", "Ajouter")
        if not nom:
            return
        if any(m["nom"].lower() == nom.lower() for m in self.matieres):
            self.informer("Matière", f"La matière « {nom} » existe déjà.", "attention")
            return
        try:
            id_ = self.base.ajouter_matiere(nom, COEF_DEFAUT)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.informer("Ajout impossible", f"La matière n'a pas pu être ajoutée : {err}", "erreur")
            return
        self.matieres.append({"id": id_, "nom": nom, "coef": COEF_DEFAUT, "note": None})
        if self.recherche.get():
            self.recherche.set("")
        self.dessiner(focus=nom)

    def supprimer_matiere(self, matiere):
        if self.parametres["confirmer_suppression"] == "oui" and not self.confirmer(
                "Supprimer la matière ?",
                f"La matière « {matiere['nom']} » et sa note seront supprimées.",
                "Supprimer", danger=True):
            return
        position = self.matieres.index(matiere)
        try:
            self.base.supprimer_matiere(matiere["nom"])
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            self.informer("Suppression impossible", f"La matière n'a pas pu être supprimée : {err}",
                          "erreur")
            return
        self._effacer_annulation()
        self.en_attente.pop(matiere["nom"], None)
        self.matieres.remove(matiere)
        self.suppression_annulable = (dict(matiere), position)
        self._annulation_after = self.after(10_000, self.expirer_annulation)
        self.dessiner()
        self.maj_etat(f"✓ {matiere['nom']} supprimée")

    def _effacer_annulation(self):
        if self._annulation_after is not None:
            self.after_cancel(self._annulation_after)
            self._annulation_after = None
        self.suppression_annulable = None
        if getattr(self, "bouton_annuler", None) and self.bouton_annuler.winfo_exists():
            self.bouton_annuler.pack_forget()

    def expirer_annulation(self):
        self._annulation_after = None
        self.suppression_annulable = None
        if getattr(self, "bouton_annuler", None) and self.bouton_annuler.winfo_exists():
            self.bouton_annuler.pack_forget()

    def annuler_suppression(self):
        if not self.suppression_annulable:
            return
        matiere, position = self.suppression_annulable
        try:
            self.base.restaurer_matiere(matiere, position)
        except (OSError, sqlite3.Error, ValueError) as err:
            self.informer("Restauration impossible", f"La matière n'a pas pu être restaurée : {err}", "erreur")
            return
        self._effacer_annulation()
        self.matieres = self.base.matieres()
        self.dessiner()
        self.maj_etat(f"✓ {matiere['nom']} restaurée")

    # --- Profil ---

    def fenetre_profil(self):
        fen, cadre = self.dialogue("Profil")
        self.texte(cadre, "Votre profil", font=self.titre_barre).grid(row=0, column=0, columnspan=2,
                                                                    sticky="w", pady=(0, 12))
        self.texte(cadre, "Nom", font=self.gras).grid(row=1, column=0, sticky="w", pady=6)
        nom = self.champ(cadre, width=24)
        nom.insert(0, self.nom)
        nom.grid(row=1, column=1, sticky="w", pady=6, padx=(14, 0), ipady=4)
        self.texte(cadre, "Niveau", font=self.gras).grid(row=2, column=0, sticky="w", pady=6)
        niveau = ttk.Combobox(cadre, state="readonly", values=list(NIVEAUX), width=8, font=self.polices[0])
        niveau.set(self.niveau)
        niveau.grid(row=2, column=1, sticky="w", pady=6, padx=(14, 0))

        def valider():
            if not nom.get().strip():
                self.informer("Profil", "Entrez votre nom.", "attention", parent=fen)
                return
            if not self.enregistrer(silencieux=True):  # on recharge depuis la base juste après
                return
            try:
                self.base.enregistrer_profil(niveau.get(), nom.get().strip())
            except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
                self.informer("Profil impossible", f"Le profil n'a pas pu être enregistré : {err}",
                              "erreur", parent=fen)
                return
            fen.destroy()
            self.ouvrir(niveau.get(), nom.get().strip())

        def effacer():
            if self.confirmer("Tout effacer ?", "Votre profil et toutes vos matières seront supprimés. "
                              "Cette action est définitive.", "Tout effacer", danger=True, parent=fen):
                try:
                    self.base.tout_effacer()
                except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
                    self.informer("Suppression impossible", f"Les données n'ont pas pu être effacées : {err}",
                                  "erreur", parent=fen)
                    return
                self._effacer_annulation()
                self.en_attente.clear()
                fen.destroy()
                self.ecran_niveau()

        boutons = tk.Frame(cadre, bg=CARTE)
        boutons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(20, 0))
        Bouton(boutons, "Tout effacer", effacer, "danger").pack(side="left")
        Bouton(boutons, "Valider", valider).pack(side="right")
        Bouton(boutons, "Annuler", fen.destroy, "secondaire").pack(side="right", padx=8)
        self.afficher_dialogue(fen)

    def fenetre_parametres(self):
        fen, cadre = self.dialogue("Paramètres")
        actuels = self.base.parametres()

        def ligne(texte, options, valeur):
            rang = tk.Frame(cadre, bg=CARTE)
            rang.pack(fill="x", pady=5)
            self.texte(rang, texte, font=self.petite_gras).pack(side="left", anchor="w")
            choix = ttk.Combobox(rang, state="readonly", values=options, width=18,
                                 font=self.polices[0])
            choix.current(options.index(valeur))
            choix.pack(side="right")
            return choix

        langue_options = [self.tr("Français"), self.tr("English")]
        langue = ligne("Langue", langue_options,
                       langue_options[0] if actuels["langue"] == "fr" else langue_options[1])
        theme_options = [self.tr("Clair"), self.tr("Sombre")]
        theme = ligne("Thème", theme_options,
                      theme_options[0] if actuels["theme"] == "clair" else theme_options[1])
        taille_options = [self.tr("Normale"), self.tr("Grande")]
        taille = ligne("Taille du texte", taille_options,
                       taille_options[0] if actuels["taille_texte"] == "normale" else taille_options[1])
        sauvegardes = ligne("Nombre de sauvegardes", ["1", "3", "5"], actuels["nb_sauvegardes"])

        variables = {}
        for cle, label in (
                ("message_sauvegarde", "Afficher le message après une sauvegarde"),
                ("confirmer_suppression", "Demander confirmation avant de supprimer une matière"),
                ("confirmer_import", "Demander confirmation avant d'importer des notes")):
            variable = tk.BooleanVar(self, value=actuels[cle] == "oui")
            tk.Checkbutton(cadre, text=self.tr(label), variable=variable, anchor="w",
                           bg=CARTE, fg=TEXTE, activebackground=CARTE, activeforeground=TEXTE,
                           selectcolor=FOND, font=self.petite, wraplength=420,
                           justify="left").pack(fill="x", pady=3)
            variables[cle] = variable

        def enregistrer():
            if not self.enregistrer(silencieux=True):
                return
            choix_langue = "fr" if langue.current() == 0 else "en"
            choix_theme = "clair" if theme.current() == 0 else "sombre"
            choix_taille = "normale" if taille.current() == 0 else "grande"
            nouveaux = {
                "langue": choix_langue,
                "theme": choix_theme,
                "taille_texte": choix_taille,
                "nb_sauvegardes": sauvegardes.get(),
                **{cle: "oui" if variable.get() else "non" for cle, variable in variables.items()},
            }
            try:
                self.base.enregistrer_parametres(nouveaux)
            except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
                self.informer("Paramètres", f"Les paramètres n'ont pas pu être enregistrés : {err}",
                              "erreur", parent=fen)
                return
            self.parametres = self.base.parametres()
            self.langue = self.parametres["langue"]
            self.facteur_texte = 1.15 if self.parametres["taille_texte"] == "grande" else 1.0
            self.appliquer_theme(self.parametres["theme"])
            self.styliser()
            self._taille = None
            echelle = min(self.winfo_width() / LARGEUR_REF, self.winfo_height() / HAUTEUR_REF)
            self.appliquer_taille(max(9, min(26, round(TAILLE_REF * echelle * self.facteur_texte))))
            fen.destroy()
            profil = self.base.profil()
            if profil:
                self.ouvrir(*profil)
            elif self._onboarding_action:
                self._onboarding_action()
            else:
                self.ecran_niveau()

        boutons = tk.Frame(cadre, bg=CARTE)
        boutons.pack(fill="x", pady=(16, 0))
        Bouton(boutons, "Enregistrer", enregistrer).pack(side="right")
        Bouton(boutons, "Annuler", fen.destroy, "secondaire").pack(side="right", padx=8)
        self.afficher_dialogue(fen)

    # --- Sauvegardes ---

    def fenetre_sauvegardes(self):
        sauvegardes = self.base.liste_sauvegardes()
        if not sauvegardes:
            self.informer("Sauvegardes", "Aucune sauvegarde n'est disponible.")
            return

        fen, cadre = self.dialogue("Sauvegardes")
        self.texte(cadre, "Choisissez une sauvegarde à restaurer :", font=self.gras).pack(anchor="w")
        liste = tk.Listbox(cadre, height=min(7, len(sauvegardes)), width=44, exportselection=False,
                           relief="flat", bg=CARTE, fg=TEXTE, selectbackground=BLEU,
                           selectforeground="#ffffff", highlightthickness=1,
                           highlightbackground=LIGNE, font=self.polices[0])
        for sauvegarde in sauvegardes:
            liste.insert("end", sauvegarde.stem[len("moyenne_"):])
        liste.selection_set(0)
        liste.pack(fill="x", pady=(10, 14))

        def restaurer():
            selection = liste.curselection()
            if not selection:
                self.informer("Sauvegardes", "Sélectionnez une sauvegarde.", "attention", parent=fen)
                return
            sauvegarde = sauvegardes[selection[0]]
            if not self.confirmer(
                    "Restaurer cette sauvegarde ?",
                    "Les données actuelles seront remplacées. Une copie de la base actuelle "
                    "sera créée avant la restauration.",
                    "Restaurer", danger=True, parent=fen):
                return
            try:
                if not self.enregistrer(silencieux=True):
                    return
                self.base.restaurer_sauvegarde(sauvegarde)
            except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
                self.informer("Restauration impossible", f"La sauvegarde n'a pas pu être restaurée : {err}",
                              "erreur", parent=fen)
                return

            self._effacer_annulation()
            self.en_attente.clear()
            profil = self.base.profil()
            fen.destroy()
            if profil:
                self.ouvrir(*profil)
            else:
                self.ecran_niveau()
            self.informer("Restauration terminée", "Les données de la sauvegarde ont été restaurées.",
                          "succes")

        boutons = tk.Frame(cadre, bg=CARTE)
        boutons.pack(fill="x")
        Bouton(boutons, "Restaurer", restaurer, "primaire").pack(side="right")
        Bouton(boutons, "Fermer", fen.destroy, "secondaire").pack(side="right", padx=8)
        self.afficher_dialogue(fen)

    # --- Import ---

    def importer(self):
        chemin = filedialog.askopenfilename(
            parent=self, title=self.tr("Importer un bulletin"), initialdir=Path.home(),
            filetypes=[("CSV", "*.csv"), (self.tr("Tous les fichiers"), "*")])
        if not chemin:
            return
        try:
            lues = lire_csv(chemin)
        except (OSError, UnicodeDecodeError, ValueError) as err:
            self.informer("Import impossible", f"Ce fichier n'a pas pu être lu : {err}", "erreur")
            return

        periode_active = self.base.periode_active()
        groupes = {}
        for session, nom, note in lues:
            nom_session = session or periode_active["nom"]
            groupes.setdefault(nom_session.casefold(), {"nom": nom_session, "matieres": []})
            groupes[nom_session.casefold()]["matieres"].append((nom, note))

        periodes = {periode["nom"].casefold(): periode for periode in self.base.periodes()}
        nouvelles = 0
        mises_a_jour = 0
        nouvelles_periodes = 0
        for cle, groupe in groupes.items():
            periode = periodes.get(cle)
            if periode is None:
                nouvelles_periodes += 1
                noms_existants = set()
            else:
                noms_existants = {
                    matiere["nom"].casefold()
                    for matiere in self.base.matieres(periode["id"])
                }
            for nom, _ in groupe["matieres"]:
                if nom.casefold() in noms_existants:
                    mises_a_jour += 1
                else:
                    nouvelles += 1
                    noms_existants.add(nom.casefold())

        resume = (f"{len(lues)} matière(s) trouvée(s) :\n•  {nouvelles} nouvelle(s)\n"
                  f"•  {mises_a_jour} déjà présente(s)")
        if nouvelles_periodes:
            resume += f"\n•  {nouvelles_periodes} nouvelle(s) session(s)"
        if mises_a_jour:
            resume += " : leur note sera remplacée"
        if (self.parametres["confirmer_import"] == "oui"
                and not self.confirmer("Importer ce bulletin ?", resume, "Importer")):
            return

        if not self.enregistrer(silencieux=True):
            return
        try:
            for cle, groupe in groupes.items():
                periode = periodes.get(cle)
                periode_id = (periode["id"] if periode is not None
                              else self.base.ajouter_periode(groupe["nom"]))
                existantes = {
                    matiere["nom"].casefold(): matiere
                    for matiere in self.base.matieres(periode_id)
                }
                for nom, note in groupe["matieres"]:
                    matiere = existantes.get(nom.casefold())
                    if matiere is None:
                        id_ = self.base.ajouter_matiere(nom, COEF_DEFAUT, periode_id)
                        matiere = {"id": id_, "nom": nom, "coef": COEF_DEFAUT, "note": None}
                        existantes[nom.casefold()] = matiere
                    matiere["note"] = note
                    self.en_attente.pop(matiere["nom"], None)
                    self.base.changer_note(nom, note, periode_id)
        except (OSError, sqlite3.Error, ValueError, RuntimeError) as err:
            if self.base.periode_active()["id"] != periode_active["id"]:
                self.base.activer_periode(periode_active["id"])
            self.matieres = self.base.matieres(periode_active["id"])
            self.informer("Import interrompu", f"Le bulletin n'a pas pu être importé en entier : {err}",
                          "erreur")
            self.dessiner()
            return
        if self.base.periode_active()["id"] != periode_active["id"]:
            self.base.activer_periode(periode_active["id"])
        self.matieres = self.base.matieres(periode_active["id"])
        self.dessiner()

    # --- Export ---

    def fenetre_export(self):
        fen, cadre = self.dialogue("Exporter")
        self.texte(cadre, "Exporter votre bulletin", font=self.titre_barre).pack(anchor="w")
        self.texte(cadre, "Choisissez le format du fichier :", fg=DISCRET).pack(anchor="w", pady=(2, 14))
        a_exporter = any(self.base.matieres(periode["id"]) for periode in self.base.periodes())
        formats = [("PDF  ·  à imprimer ou envoyer", "pdf"),
                   ("CSV  ·  LibreOffice / Excel", "csv")] if a_exporter else []
        formats.append(("JSON  ·  toutes les périodes (application mobile)", "json"))
        for texte, format_ in formats:
            Bouton(cadre, texte, lambda f=format_: (fen.destroy(), self.exporter(f)), "secondaire",
                   pady=10).pack(fill="x", pady=4)
        Bouton(cadre, "Annuler", fen.destroy, "lien").pack(pady=(12, 0))
        self.afficher_dialogue(fen)

    def exporter(self, format_):
        extensions = {
            "pdf": (".pdf", [("PDF", "*.pdf")]),
            "csv": (".csv", [("CSV", "*.csv")]),
            "json": (".json", [("Sauvegarde MaMoyenne mobile", "*.json")]),
        }
        extension, types_fichier = extensions[format_]
        if format_ == "json" and not self.enregistrer(silencieux=True):
            return
        nom_fichier = (f"mamoyenne_{self.nom}.json" if format_ == "json"
                       else f"bulletin_{self.nom}{extension}")
        chemin = filedialog.asksaveasfilename(
            parent=self, title=self.tr("Exporter les données" if format_ == "json" else "Exporter le bulletin"),
            initialdir=Path.home(), initialfile=nom_fichier, defaultextension=extension,
            filetypes=types_fichier)
        if not chemin:
            return
        try:
            periodes = [{
                "nom": periode["nom"],
                "matieres": self.base.matieres(periode["id"]),
            } for periode in self.base.periodes()]
            if format_ == "csv":
                exporter_csv(tableau_export(periodes, self.passage), chemin)
            elif format_ == "json":
                exporter_json_pwa(self.base, chemin)
            else:
                exporter_pdf(periodes, self.nom, self.niveau, self.passage, chemin)
        except ImportError:
            self.informer("Export impossible", "L'export PDF nécessite le module fpdf2 (pip install fpdf2).", "erreur")
            return
        except Exception as err:
            self.informer("Export impossible", f"L'export a échoué : {err}", "erreur")
            return
        self.informer("Bulletin exporté", f"Fichier créé :\n{chemin}", "succes")

    # --- Mode d'emploi ---

    def fenetre_aide(self):
        fen = tk.Toplevel(self, bg=CARTE)
        titre = self.tr("Mode d'emploi")
        fen.title(f"{titre} - {NOM_APP}")
        fen.transient(self)
        fen.geometry("640x540")
        texte = tk.Text(fen, wrap="word", padx=26, pady=20, relief="flat", bd=0, cursor="arrow",
                        background=CARTE, foreground=TEXTE, font=self.polices[0], highlightthickness=0)
        defil = ttk.Scrollbar(fen, command=texte.yview)
        texte.configure(yscrollcommand=defil.set)
        pied = tk.Frame(fen, bg=FOND, pady=10)
        pied.pack(side="bottom", fill="x")
        Bouton(pied, "Fermer", fen.destroy, padx=22).pack()
        defil.pack(side="right", fill="y")
        texte.pack(fill="both", expand=True)

        texte.tag_configure("titre", font=self.titre, foreground=BLEU, spacing3=10)
        texte.tag_configure("section", font=self.gras, foreground=BLEU_FONCE, spacing1=14, spacing3=4)
        texte.tag_configure("point", lmargin1=10, lmargin2=26, spacing1=3)
        texte.insert("end", self.tr(f"Bienvenue sur {NOM_APP}") + "\n", "titre")
        for section, points in MODE_EMPLOI:
            texte.insert("end", self.tr(section) + "\n", "section")
            for point in points:
                texte.insert("end", f"•  {self.tr(point)}\n", "point")
        texte.configure(state="disabled")


if __name__ == "__main__":
    integrer_au_systeme()
    App().mainloop()
