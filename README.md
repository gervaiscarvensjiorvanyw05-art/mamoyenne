# MaMoyenne

Petite application pour calculer sa moyenne et suivre ses reprises.
**Aucune installation n'est nécessaire** (pas besoin de Python) : on télécharge un fichier et on l'ouvre.

- Chaque matière a un coefficient de 100, les notes vont de 0 à 100.
- En dessous de la note de passage de votre niveau, la matière est une **reprise** :

  | Niveau | L1 | L2 | L3 | L4 |
  |---|---|---|---|---|
  | Note de passage | 70 | 70 | 75 | 80 |

- Une matière sans note (`NULL`) n'est pas comptée dans la moyenne.

## Installation

Ouvrez la page **[Releases → dernière version](../../releases/latest)**, puis dans la section *Assets*
téléchargez le fichier qui correspond à votre ordinateur.

### Windows

1. Téléchargez **`MaMoyenne-Windows.exe`**.
   Si le navigateur affiche « fichier rarement téléchargé », cliquez sur **…** puis **Conserver**.
2. Double-cliquez dessus. La première fois, Windows peut afficher **« Windows a protégé votre ordinateur »** :
   cliquez sur **Informations complémentaires**, puis **Exécuter quand même**.
3. Dès ce premier lancement, MaMoyenne **s'installe** et crée un raccourci dans le **menu Démarrer**
   et sur le **Bureau** : tapez « MaMoyenne » dans la recherche Windows.
4. Vous pouvez ensuite **supprimer le fichier téléchargé** : l'application installée et vos notes restent.

### macOS (Mac à puce Apple : M1, M2, M3…)

1. Téléchargez **`MaMoyenne-macOS.zip`** et double-cliquez dessus pour le décompresser.
2. Ouvrez **MaMoyenne**. La première fois, macOS bloque l'application car elle ne vient pas de l'App Store :
   - **macOS 14 ou plus ancien** : clic droit sur MaMoyenne → **Ouvrir** → **Ouvrir**.
   - **macOS 15 ou plus récent** : ouvrez **Réglages Système → Confidentialité et sécurité**, descendez
     jusqu'au message sur MaMoyenne et cliquez sur **Ouvrir quand même**.
3. Dès ce premier lancement, MaMoyenne **s'installe** dans le dossier **Applications** de votre compte
   (`~/Applications`) : Spotlight (⌘ + Espace) et le Launchpad la trouvent.
   Vous pouvez aussi la glisser vous-même dans **Applications** : elle n'est alors pas copiée.
4. Vous pouvez ensuite **supprimer le fichier téléchargé** et le `.zip` : l'application installée et vos notes restent.

Les Mac Intel (avant fin 2020) ne sont pas pris en charge.

### Linux

1. Téléchargez **`MaMoyenne-Linux`**.
2. Rendez-le exécutable : clic droit → **Propriétés** → **Permissions** → cocher **Autoriser l'exécution**
   (ou dans un terminal : `chmod +x MaMoyenne-Linux`).
3. Double-cliquez dessus (ou `./MaMoyenne-Linux` dans un terminal).
4. Dès ce premier lancement, MaMoyenne **s'installe** dans `~/.local/share/MaMoyenne` et
   **apparaît dans le menu des applications**, avec son icône : tapez « MaMoyenne » dans la recherche.
5. Vous pouvez ensuite **supprimer le fichier téléchargé** : l'application installée et vos notes restent.

> **Pourquoi ces avertissements ?** L'application n'est pas signée numériquement (la signature est payante).
> Le code est entièrement visible dans ce dépôt.

## Utilisation

L'interface ajuste la taille du texte et réorganise l'en-tête ainsi que les commandes de tri et de recherche
lorsque la fenêtre est étroite.

1. Au premier lancement, choisissez votre niveau (L1 à L4), puis entrez votre nom.
   Le mode d'emploi s'affiche ; vous pouvez le rouvrir à tout moment avec le bouton **Mode d'emploi**.
2. Cliquez sur **+** pour ajouter une matière.
3. Tapez votre note puis appuyez sur **Entrée** pour l'enregistrer (le curseur passe à la matière suivante).
   Le bouton **Enregistrer** enregistre toutes les notes modifiées d'un coup.
   Laissez `NULL` si vous n'avez pas encore la note.
4. Choisissez la période active au-dessus du résumé. **Gérer les périodes…** permet d'en créer,
   renommer ou supprimer. Chaque période a sa propre liste ; vos données actuelles sont conservées dans
   **Période actuelle**. Un import CSV concerne la période active.
5. Au-dessus de la liste, choisissez l'ordre d'affichage : ordre d'ajout, matières notées d'abord,
   meilleures notes d'abord, pires notes d'abord ou ordre personnalisé. Les matières sans note restent
   en bas des tris par note. Glissez la poignée à deux traits **≡** pour créer un ordre personnalisé,
   conservé après fermeture. Le classement par note est actualisé lorsque vous enregistrez une note.
6. Le champ **Rechercher** filtre la liste par nom, sans modifier les moyennes ni le nombre de reprises.

Autres boutons :

- **✕** à côté d'une matière : la supprimer. Le bouton **Annuler** permet de la restaurer pendant 10 secondes.
- **Profil** : changer de nom ou de niveau, ou tout effacer pour recommencer.
- **Paramètres** : choisir le thème clair/sombre, la taille du texte, la langue (français/anglais),
  le nombre de sauvegardes conservées et les confirmations pour supprimer une matière ou importer des notes.
  La suppression d'une période et l'effacement complet demandent toujours confirmation.
- **Exporter** : votre bulletin en PDF (à imprimer) ou en CSV (LibreOffice / Excel).
- **Importer** : reprendre un bulletin CSV, par exemple pour retrouver vos notes sur un autre ordinateur.
  Les matières absentes sont ajoutées, celles déjà présentes prennent la note du fichier.
- **Sauvegardes** : après des modifications enregistrées, une copie locale est créée à la fermeture de
  l'application, avec un message de confirmation. Les 3 plus récentes sont conservées. Vous pouvez restaurer
  une copie depuis l'application ; une copie de sécurité de l'état actuel est créée avant le remplacement.

## Vos données

Vos notes restent **sur votre ordinateur**, dans une petite base de données personnelle.
Elles ne sont envoyées nulle part.

| Système | Emplacement |
|---|---|
| Windows | `%APPDATA%\MaMoyenne\moyenne.db` |
| macOS | `~/Library/Application Support/MaMoyenne/moyenne.db` |
| Linux | `~/.local/share/MaMoyenne/moyenne.db` |

Les sauvegardes se trouvent dans le sous-dossier `sauvegardes`, à côté de cette base.

- **Mettre à jour** : téléchargez la nouvelle version et lancez-la une fois : elle remplace la version
  installée. Vos notes sont conservées. (Sous Windows, fermez d'abord MaMoyenne si elle est ouverte.)
- **Changer d'ordinateur** : **Exporter** en CSV sur l'ancien, puis **Importer** ce fichier sur le nouveau.
- **Désinstaller** :
  - Windows : supprimez `%LOCALAPPDATA%\Programs\MaMoyenne`, `%APPDATA%\MaMoyenne`, et les raccourcis
    MaMoyenne du Bureau et du menu Démarrer.
  - macOS : mettez **MaMoyenne** (dans `~/Applications`) à la corbeille, puis supprimez
    `~/Library/Application Support/MaMoyenne`.
  - Linux : supprimez `~/.local/share/MaMoyenne`, `~/.local/share/applications/mamoyenne.desktop` et
    `~/.local/share/icons/hicolor/512x512/apps/mamoyenne.png`.

## Pour les développeurs

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt     # Windows : .venv\Scripts\pip install -r requirements.txt
.venv/bin/python moyenne.py                   # Windows : .venv\Scripts\python moyenne.py
```

Les exécutables sont construits automatiquement par GitHub Actions (`.github/workflows/build.yml`).
Pour publier une nouvelle version : `git tag v1.1 && git push origin v1.1`.

### Version mobile installable (PWA)

La version web se trouve dans `web/` et fonctionne séparément de l'application Tkinter. Pour la tester
sur l'ordinateur :

```powershell
python -m http.server 8000 --directory web
```

Ouvrez ensuite `http://localhost:8000`. Ne lancez pas `index.html` directement : le fonctionnement hors
ligne et l'installation nécessitent un serveur local ou HTTPS. Pour l'installer sur un téléphone, il
faudra d'abord héberger cette version sur une adresse HTTPS.

Les données de la PWA restent dans le stockage local du navigateur et ne se synchronisent pas entre
appareils. Pour transférer toutes les périodes depuis l'application de bureau, choisissez **Exporter**,
puis **JSON · toutes les périodes (application mobile)** ; dans la PWA, ouvrez **Paramètres → Restaurer
une sauvegarde JSON**. L'import CSV d'une période est également disponible.

Les tests du cœur PWA se lancent avec `node --test tests\test_web_core.mjs`.

#### Publier sur GitHub Pages

Le workflow `.github/workflows/deploy-pwa.yml` publie le contenu de `web/` en HTTPS après un push sur
`main`. Pour l'activer, choisissez **Settings → Pages → Build and deployment → Source: GitHub Actions**
dans le dépôt. Après la publication, GitHub affiche l'adresse du site dans l'exécution **Publier la PWA**
de l'onglet **Actions**. Ouvrez cette adresse sur le téléphone, puis installez l'application depuis le
navigateur (Chrome sur Android ; **Partager → Sur l'écran d'accueil** dans Safari sur iPhone).

La publication n'est pas automatique depuis votre copie locale : il faut d'abord pousser les changements
et les intégrer à `main`. Aucun changement n'a été poussé pour cette préparation.
