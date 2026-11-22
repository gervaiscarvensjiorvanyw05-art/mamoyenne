import {
  DEFAULT_SETTINGS,
  DEFAULT_PERIOD_NAMES,
  PASS_MARKS,
  SORT_MODES,
  average,
  averageAcrossPeriods,
  countRetakes,
  createEmptyState,
  createInitialPeriods,
  exportPeriodsCsv,
  filterSubjects,
  newId,
  normalizeState,
  parseCsvImport,
  parseGrade,
  sortSubjects,
} from "./core.mjs";

const DATABASE_NAME = "mamoyenne-pwa";
const DATABASE_VERSION = 1;
const STORE_NAME = "application";
const STATE_KEY = "state";

const TEXT = {
  fr: {
    install: "Installer",
    settings: "Paramètres",
    welcome: "Bienvenue sur MaMoyenne",
    "setup-title": "Suivez vos notes simplement",
    "setup-description": "Votre profil et vos notes sont enregistrés sur cet appareil.",
    "your-name": "Votre nom",
    "your-level": "Votre niveau",
    start: "Commencer",
    period: "Période",
    "session-one": "1ère session",
    "session-two": "2ème session",
    "general-session": "Générale",
    "manage-periods": "Gérer les périodes",
    average: "Moyenne",
    "out-of-100": "sur 100",
    retakes: "Reprises",
    "graded-subjects": "Matières notées",
    sort: "Trier",
    "sort-added": "Ordre d'ajout",
    "sort-graded": "Notées d'abord",
    "sort-best": "Meilleures notes",
    "sort-worst": "Pires notes",
    "sort-custom": "Ordre personnalisé",
    search: "Rechercher",
    "search-placeholder": "Nom d'une matière",
    "add-subject": "Ajouter une matière",
    "custom-order-hint": "Utilisez les flèches pour ajuster l'ordre des matières.",
    "empty-title": "Aucune matière pour le moment",
    "empty-start": "Ajoutez votre première matière pour commencer.",
    "empty-search": "Aucune matière ne correspond à cette recherche.",
    "import-csv": "Importer un CSV",
    "export-csv": "Exporter toutes les sessions en CSV",
    "export-pdf": "Imprimer / Enregistrer en PDF",
    "local-data-note": "Vos données restent sur cet appareil. Exportez une sauvegarde pour les transférer.",
    "subject-name": "Nom de la matière",
    cancel: "Annuler",
    add: "Ajouter",
    "period-name": "Nom de la période",
    "create-period": "Créer et activer",
    "rename-period": "Renommer",
    "delete-period": "Supprimer",
    close: "Fermer",
    language: "Langue",
    theme: "Thème",
    light: "Clair",
    dark: "Sombre",
    "text-size": "Taille du texte",
    normal: "Normale",
    large: "Grande",
    "export-backup": "Télécharger une sauvegarde complète",
    "import-backup": "Restaurer une sauvegarde JSON",
    "clear-data": "Effacer le profil et toutes les notes",
    "print-average": "Moyenne générale / 100",
    "print-retakes": "Reprises",
    "print-subject-count": "Matières",
    "print-subject": "Matière",
    "print-grade-report": "Bulletin de notes",
    "print-period-average": (name, mean) => `Moyenne de ${name} : ${mean} / 100`,
    "print-generated": (date) => `Généré le ${date}`,
    "backup-note": "Les sauvegardes sont stockées ou téléchargées à votre initiative. Aucune donnée n'est envoyée sur Internet.",
    note: "Note",
    status: "Statut",
    validated: "Validé",
    retake: "Reprise",
    pending: "En attente",
    "subject-count": (count) => `${count} matière${count > 1 ? "s" : ""} au total`,
    "graded-count": (count) => `${count} sur ${count === 1 ? "1 matière notée" : "les matières notées"}`,
    "retake-count": (count) => count === 0 ? "Aucune reprise" : `${count} reprise${count > 1 ? "s" : ""}`,
    "move-up": (name) => `Déplacer ${name} vers le haut`,
    "move-down": (name) => `Déplacer ${name} vers le bas`,
    "delete-subject": (name) => `Supprimer ${name}`,
    "grade-placeholder": "NULL",
    "profile-button": "Profil",
    "edit-profile": "Modifier le profil",
    save: "Enregistrer",
    "profile-saved": "Profil enregistré.",
    "subject-added": "Matière ajoutée.",
    "subject-deleted": "Matière supprimée.",
    "subject-restored": "Matière restaurée.",
    "period-created": "Période créée et activée.",
    "period-renamed": "Période renommée.",
    "period-deleted": "Période supprimée.",
    "csv-imported": (count, periods) =>
      `${count} matière${count > 1 ? "s importées" : " importée"} dans ${periods} session(s).`,
    "csv-exported": "Le CSV des sessions a été téléchargé.",
    "backup-exported": "Sauvegarde téléchargée.",
    "backup-imported": "Sauvegarde restaurée.",
    "confirm-import": (newCount, updatedCount, periods) =>
      `Importer ${newCount} nouvelle(s) matière(s) et remplacer ${updatedCount} note(s) existante(s) dans ${periods} session(s) ?`,
    "confirm-delete-subject": (name) => `Supprimer « ${name} » ?`,
    "confirm-delete-period": (name) => `Supprimer « ${name} » et toutes ses matières ?`,
    "confirm-clear": "Effacer le profil, les périodes et toutes les matières de cet appareil ?",
    "confirm-restore": "Remplacer les données de cet appareil par cette sauvegarde ?",
    "duplicate-subject": "Une matière porte déjà ce nom dans cette période.",
    "duplicate-period": "Une période porte déjà ce nom.",
    "last-period": "Il faut conserver au moins une période.",
    "bad-file": "Ce fichier n'a pas pu être lu.",
    "invalid-grade": "Saisissez une note entre 0 et 100, ou laissez le champ vide.",
    "install-ios": "Sur iPhone, ouvrez cette page dans Safari, touchez Partager, puis « Sur l’écran d’accueil ».",
    "install-android": "Dans Chrome, ouvrez le menu puis choisissez « Installer l’application » ou « Ajouter à l’écran d’accueil ».",
    "install-desktop": "Utilisez l’option Installer de votre navigateur pour ajouter MaMoyenne à l’écran d’accueil.",
    "install-prompt": "Choisissez Installer dans la fenêtre du navigateur.",
    "offline-error": "Le mode hors ligne n'a pas pu être activé.",
  },
  en: {
    install: "Install",
    settings: "Settings",
    welcome: "Welcome to MaMoyenne",
    "setup-title": "Keep track of your grades",
    "setup-description": "Your profile and grades are stored on this device.",
    "your-name": "Your name",
    "your-level": "Your level",
    start: "Get started",
    period: "Period",
    "session-one": "1st session",
    "session-two": "2nd session",
    "general-session": "Overall",
    "manage-periods": "Manage periods",
    average: "Average",
    "out-of-100": "out of 100",
    retakes: "Retakes",
    "graded-subjects": "Graded subjects",
    sort: "Sort",
    "sort-added": "Added order",
    "sort-graded": "Graded first",
    "sort-best": "Highest grades",
    "sort-worst": "Lowest grades",
    "sort-custom": "Custom order",
    search: "Search",
    "search-placeholder": "Subject name",
    "add-subject": "Add a subject",
    "custom-order-hint": "Use the arrows to change the order of subjects.",
    "empty-title": "No subjects yet",
    "empty-start": "Add your first subject to get started.",
    "empty-search": "No subjects match this search.",
    "import-csv": "Import CSV",
    "export-csv": "Export all sessions as CSV",
    "export-pdf": "Print / Save as PDF",
    "local-data-note": "Your data stays on this device. Export a backup to transfer it.",
    "subject-name": "Subject name",
    cancel: "Cancel",
    add: "Add",
    "period-name": "Period name",
    "create-period": "Create and activate",
    "rename-period": "Rename",
    "delete-period": "Delete",
    close: "Close",
    language: "Language",
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    "text-size": "Text size",
    normal: "Normal",
    large: "Large",
    "export-backup": "Download full backup",
    "import-backup": "Restore JSON backup",
    "clear-data": "Delete profile and all grades",
    "print-average": "Overall average / 100",
    "print-retakes": "Retakes",
    "print-subject-count": "Subjects",
    "print-subject": "Subject",
    "print-grade-report": "Grade report",
    "print-period-average": (name, mean) => `${name} average: ${mean} / 100`,
    "print-generated": (date) => `Generated on ${date}`,
    "backup-note": "Backups are stored or downloaded at your request. No data is sent over the Internet.",
    note: "Grade",
    status: "Status",
    validated: "Passed",
    retake: "Retake",
    pending: "Pending",
    "subject-count": (count) => `${count} subject${count === 1 ? "" : "s"} total`,
    "graded-count": (count) => `${count} graded`,
    "retake-count": (count) => count === 0 ? "No retakes" : `${count} retake${count === 1 ? "" : "s"}`,
    "move-up": (name) => `Move ${name} up`,
    "move-down": (name) => `Move ${name} down`,
    "delete-subject": (name) => `Delete ${name}`,
    "grade-placeholder": "—",
    "profile-button": "Profile",
    "edit-profile": "Edit profile",
    save: "Save",
    "profile-saved": "Profile saved.",
    "subject-added": "Subject added.",
    "subject-deleted": "Subject deleted.",
    "subject-restored": "Subject restored.",
    "period-created": "Period created and activated.",
    "period-renamed": "Period renamed.",
    "period-deleted": "Period deleted.",
    "csv-imported": (count, periods) =>
      `${count} subject${count === 1 ? "" : "s"} imported into ${periods} session(s).`,
    "csv-exported": "Sessions CSV downloaded.",
    "backup-exported": "Backup downloaded.",
    "backup-imported": "Backup restored.",
    "confirm-import": (newCount, updatedCount, periods) =>
      `Import ${newCount} new subject(s) and replace ${updatedCount} existing grade(s) in ${periods} session(s)?`,
    "confirm-delete-subject": (name) => `Delete “${name}”?`,
    "confirm-delete-period": (name) => `Delete “${name}” and all its subjects?`,
    "confirm-clear": "Delete the profile, periods, and all subjects from this device?",
    "confirm-restore": "Replace the data on this device with this backup?",
    "duplicate-subject": "A subject with this name already exists in this period.",
    "duplicate-period": "A period with this name already exists.",
    "last-period": "At least one period must remain.",
    "bad-file": "This file could not be read.",
    "invalid-grade": "Enter a grade from 0 to 100, or leave the field empty.",
    "install-ios": "On iPhone, open this page in Safari, tap Share, then “Add to Home Screen”.",
    "install-android": "In Chrome, open the menu and choose “Install app” or “Add to Home screen”.",
    "install-desktop": "Use your browser’s Install option to add MaMoyenne to your home screen.",
    "install-prompt": "Choose Install in the browser prompt.",
    "offline-error": "Offline support could not be enabled.",
  },
};

const byId = (id) => document.getElementById(id);
let database;
let state;
let undoItem = null;
let undoTimer;
let toastTimer;
let installPrompt = null;

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function t(key, ...args) {
  const value = TEXT[state?.settings?.language || DEFAULT_SETTINGS.language][key];
  return typeof value === "function" ? value(...args) : value ?? key;
}

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      request.result.createObjectStore(STORE_NAME);
    };
    request.onsuccess = () => {
      database = request.result;
      database.onversionchange = () => database.close();
      resolve(database);
    };
    request.onerror = () => reject(request.error || new Error("Impossible d'ouvrir la base locale."));
  });
}

function readStoredState() {
  return new Promise((resolve, reject) => {
    const request = database.transaction(STORE_NAME, "readonly").objectStore(STORE_NAME).get(STATE_KEY);
    request.onsuccess = () => resolve(request.result ?? null);
    request.onerror = () => reject(request.error || new Error("Impossible de lire les données locales."));
  });
}

function writeStoredState() {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(STORE_NAME, "readwrite");
    transaction.objectStore(STORE_NAME).put(state, STATE_KEY);
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error || new Error("Impossible d'enregistrer les données."));
    transaction.onabort = () => reject(transaction.error || new Error("L'enregistrement a été annulé."));
  });
}

function activePeriod() {
  const period = state.periods.find((item) => item.id === state.activePeriodId);
  if (!period) throw new Error("La période active est introuvable.");
  return period;
}

function periodLabel(name) {
  const index = DEFAULT_PERIOD_NAMES.findIndex((periodName) => periodName === name);
  return index < 0 ? name : t(index === 0 ? "session-one" : "session-two");
}

function updateStaticText() {
  document.documentElement.lang = state.settings.language;
  document.title = "MaMoyenne";
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  byId("search-input").placeholder = t("search-placeholder");
  byId("install-button").setAttribute("aria-label", t("install"));
  byId("profile-button").setAttribute("aria-label", t("profile-button"));
  byId("settings-button").setAttribute("aria-label", t("settings"));
  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    if (button.classList.contains("close-button")) button.setAttribute("aria-label", t("close"));
  });
  document.querySelector(".summary-grid").setAttribute("aria-label", t("average"));
  document.querySelector(".subject-tools").setAttribute("aria-label", t("sort"));
  document.querySelector(".data-actions").setAttribute("aria-label", t("export-csv"));
  document.body.dataset.theme = state.settings.theme;
  document.body.dataset.textSize = state.settings.textSize;
  document.querySelector('meta[name="theme-color"]').content =
    state.settings.theme === "dark" ? "#171b24" : "#3158c5";
}

function renderPeriods() {
  const selected = state.activePeriodId;
  const options = state.periods.map((period) => {
    const option = document.createElement("option");
    option.value = period.id;
    option.textContent = periodLabel(period.name);
    option.selected = period.id === selected;
    return option;
  });
  byId("period-select").replaceChildren(...options);

  const manageOptions = state.periods.map((period) => {
    const option = document.createElement("option");
    option.value = period.id;
    option.textContent = periodLabel(period.name);
    option.selected = period.id === selected;
    return option;
  });
  byId("period-manage-select").replaceChildren(...manageOptions);
  byId("period-name").value = activePeriod().name;
}

function renderSummary() {
  const period = activePeriod();
  const passMark = PASS_MARKS[state.profile.level];
  const mean = average(period.subjects);
  const graded = period.subjects.filter((subject) => subject.grade !== null).length;
  byId("average-value").textContent = mean === null
    ? "—"
    : new Intl.NumberFormat(state.settings.language, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(mean);
  byId("retake-value").textContent = String(countRetakes(period.subjects, passMark));
  byId("retake-detail").textContent = t("retake-count", countRetakes(period.subjects, passMark));
  byId("graded-value").textContent = String(graded);
  byId("subject-count-detail").textContent = t("subject-count", period.subjects.length);
  byId("profile-summary").textContent =
    `${state.profile.name} · ${state.profile.level} · ${state.settings.language === "fr" ? "Passage" : "Pass mark"} ${passMark}`;
}

function createButton(className, label, action, ariaLabel = label) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.setAttribute("aria-label", ariaLabel);
  button.addEventListener("click", action);
  return button;
}

function showToast(message, action = null) {
  const toast = byId("toast");
  clearTimeout(toastTimer);
  toast.replaceChildren();
  const text = document.createElement("span");
  text.textContent = message;
  toast.append(text);
  if (action) {
    const button = createButton("toast-action", action.label, action.run);
    toast.append(button);
  }
  toast.hidden = false;
  toastTimer = setTimeout(() => {
    toast.hidden = true;
  }, 6000);
}

async function updateState(mutator, message = null) {
  const previous = clone(state);
  try {
    mutator();
    await writeStoredState();
    render();
    if (message) showToast(message);
    return true;
  } catch (error) {
    state = previous;
    render();
    showToast(error.message || t("bad-file"));
    return false;
  }
}

function renderSubjects() {
  const period = activePeriod();
  const query = byId("search-input").value;
  const subjects = filterSubjects(sortSubjects(period.subjects, state.sortMode), query);
  const list = byId("subject-list");
  const fragment = document.createDocumentFragment();
  byId("sort-select").value = state.sortMode;
  byId("custom-order-hint").hidden = state.sortMode !== "custom";
  byId("custom-order-hint").textContent = t("custom-order-hint");

  for (const subject of subjects) {
    const card = document.createElement("article");
    card.className = "subject-card";
    card.dataset.subjectId = subject.id;

    const name = document.createElement("div");
    name.className = "subject-name";
    name.textContent = subject.name;
    const nameCell = document.createElement("div");
    nameCell.className = "subject-name-cell";
    if (state.sortMode === "custom" && !query.trim()) {
      const originalIndex = period.subjects.findIndex((item) => item.id === subject.id);
      nameCell.append(
        createButton("reorder-button", "↑", () => moveSubject(subject.id, -1),
          t("move-up", subject.name)),
      );
      const down = createButton("reorder-button", "↓", () => moveSubject(subject.id, 1),
        t("move-down", subject.name));
      down.disabled = originalIndex === period.subjects.length - 1;
      nameCell.append(down);
    }
    nameCell.append(name);

    const gradeCell = document.createElement("label");
    gradeCell.className = "grade-cell";
    const gradeLabel = document.createElement("span");
    gradeLabel.textContent = t("note");
    const input = document.createElement("input");
    input.type = "text";
    input.inputMode = "decimal";
    input.autocomplete = "off";
    input.className = "grade-input";
    input.value = subject.grade === null ? "" : String(subject.grade).replace(".", ",");
    input.placeholder = t("grade-placeholder");
    input.setAttribute("aria-label", `${t("note")} · ${subject.name}`);
    input.addEventListener("change", async () => {
      let grade;
      try {
        grade = parseGrade(input.value);
      } catch {
        input.setCustomValidity(t("invalid-grade"));
        input.reportValidity();
        input.setCustomValidity("");
        input.value = subject.grade === null ? "" : String(subject.grade).replace(".", ",");
        return;
      }
      await updateState(() => {
        const current = activePeriod().subjects.find((item) => item.id === subject.id);
        if (!current) throw new Error(t("bad-file"));
        current.grade = grade;
      });
    });
    gradeCell.append(gradeLabel, input);

    const status = document.createElement("span");
    const passMark = PASS_MARKS[state.profile.level];
    status.className = `status-pill ${subject.grade === null
      ? "status-pending"
      : subject.grade >= passMark ? "status-passed" : "status-retake"}`;
    status.textContent = subject.grade === null
      ? t("pending")
      : subject.grade >= passMark ? t("validated") : t("retake");

    const remove = createButton("delete-button", "×", () => deleteSubject(subject.id),
      t("delete-subject", subject.name));
    card.append(nameCell, gradeCell, status, remove);
    fragment.append(card);
  }
  list.replaceChildren(fragment);

  const empty = subjects.length === 0;
  byId("empty-message").hidden = !empty;
  byId("empty-description").textContent = period.subjects.length === 0
    ? t("empty-start")
    : t("empty-search");
}

function render() {
  updateStaticText();
  const hasProfile = Boolean(state.profile && state.periods.length > 0);
  byId("setup-view").hidden = hasProfile;
  byId("dashboard-view").hidden = !hasProfile;
  byId("profile-name").value = state.profile?.name || "";
  byId("profile-level").value = state.profile?.level || "L1";
  byId("profile-button").hidden = !hasProfile;
  byId("language-select").value = state.settings.language;
  byId("theme-select").value = state.settings.theme;
  byId("text-size-select").value = state.settings.textSize;
  if (!hasProfile) {
    byId("profile-summary").textContent = "";
    return;
  }
  renderPeriods();
  renderSummary();
  renderSubjects();
}

function openDialog(id) {
  const dialog = byId(id);
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

function closeDialog(dialog) {
  if (typeof dialog.close === "function") dialog.close();
  else dialog.removeAttribute("open");
}

async function moveSubject(id, direction) {
  const period = activePeriod();
  const index = period.subjects.findIndex((subject) => subject.id === id);
  const destination = index + direction;
  if (index < 0 || destination < 0 || destination >= period.subjects.length) return;
  await updateState(() => {
    const subjects = activePeriod().subjects;
    [subjects[index], subjects[destination]] = [subjects[destination], subjects[index]];
  });
}

async function deleteSubject(id) {
  const period = activePeriod();
  const index = period.subjects.findIndex((subject) => subject.id === id);
  if (index < 0) return;
  const removed = clone(period.subjects[index]);
  if (!window.confirm(t("confirm-delete-subject", removed.name))) return;
  const periodId = period.id;
  const saved = await updateState(() => {
    activePeriod().subjects.splice(index, 1);
  });
  if (!saved) return;
  undoItem = { periodId, index, subject: removed };
  clearTimeout(undoTimer);
  undoTimer = setTimeout(() => { undoItem = null; }, 10000);
  showToast(t("subject-deleted"), {
    label: state.settings.language === "fr" ? "Annuler" : "Undo",
    run: async () => {
      if (!undoItem) return;
      const item = undoItem;
      const target = state.periods.find((candidate) => candidate.id === item.periodId);
      if (!target) return;
      await updateState(() => target.subjects.splice(item.index, 0, item.subject), t("subject-restored"));
      undoItem = null;
      clearTimeout(undoTimer);
    },
  });
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.hidden = true;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function renderPrintReport() {
  const passMark = PASS_MARKS[state.profile.level];
  const locale = state.settings.language;
  const formatNumber = new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  const allSubjects = state.periods.flatMap((period) => period.subjects);
  const mean = averageAcrossPeriods(state.periods);

  byId("print-title").textContent = t("print-grade-report");
  byId("print-subtitle").textContent = `${state.profile.name} · ${state.profile.level}`;
  byId("print-average").textContent = mean === null ? "—" : formatNumber.format(mean);
  byId("print-retakes").textContent = String(countRetakes(allSubjects, passMark));
  byId("print-subject-count").textContent = String(allSubjects.length);

  const sections = state.periods.map((period) => {
    const section = document.createElement("section");
    section.className = "print-period";
    const heading = document.createElement("h2");
    const label = periodLabel(period.name);
    heading.textContent = label;
    const meanText = document.createElement("p");
    const periodMean = average(period.subjects);
    meanText.textContent = t(
      "print-period-average",
      label,
      periodMean === null ? "—" : formatNumber.format(periodMean),
    );
    const table = document.createElement("table");
    table.className = "print-table";
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    for (const key of ["print-subject", "note", "status"]) {
      const cell = document.createElement("th");
      cell.scope = "col";
      cell.textContent = t(key);
      headerRow.append(cell);
    }
    thead.append(headerRow);
    const tbody = document.createElement("tbody");
    const rows = sortSubjects(period.subjects, state.sortMode).map((subject) => {
      const row = document.createElement("tr");
      const name = document.createElement("th");
      name.scope = "row";
      name.textContent = subject.name;
      const grade = document.createElement("td");
      grade.textContent = subject.grade === null
        ? "—"
        : `${formatNumber.format(subject.grade)} / 100`;
      const status = document.createElement("td");
      status.textContent = subject.grade === null
        ? t("pending")
        : subject.grade >= passMark ? t("validated") : t("retake");
      row.append(name, grade, status);
      return row;
    });
    tbody.replaceChildren(...rows);
    table.append(thead, tbody);
    section.append(heading, meanText, table);
    return section;
  });
  byId("print-periods").replaceChildren(...sections);

  const date = new Intl.DateTimeFormat(locale, { dateStyle: "long" }).format(new Date());
  byId("print-footer").textContent = t("print-generated", date);
}

function safeFilename(value) {
  return value.normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9_-]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 40) || "periode";
}

function bindEvents() {
  byId("period-form").addEventListener("submit", (event) => event.preventDefault());
  byId("settings-form").addEventListener("submit", (event) => event.preventDefault());

  byId("setup-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = byId("profile-name").value.trim();
    const level = byId("profile-level").value;
    if (!name || !PASS_MARKS[level]) return;
    await updateState(() => {
      state.profile = { name, level };
      state.periods = createInitialPeriods();
      state.activePeriodId = state.periods[0].id;
    });
  });

  byId("add-subject").addEventListener("click", () => {
    byId("subject-form").reset();
    openDialog("subject-dialog");
    byId("subject-name").focus();
  });
  byId("subject-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = byId("subject-name").value.trim();
    if (!name) return;
    if (activePeriod().subjects.some((subject) => subject.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      showToast(t("duplicate-subject"));
      return;
    }
    const saved = await updateState(() => {
      const subjects = activePeriod().subjects;
      const addedOrder = subjects.reduce((largest, subject) => Math.max(largest, subject.addedOrder ?? -1), -1) + 1;
      subjects.push({ id: newId(), name, grade: null, addedOrder });
    }, t("subject-added"));
    if (saved) {
      closeDialog(byId("subject-dialog"));
      byId("subject-name").value = "";
    }
  });

  byId("period-select").addEventListener("change", async (event) => {
    await updateState(() => { state.activePeriodId = event.target.value; });
  });
  byId("manage-periods").addEventListener("click", () => {
    renderPeriods();
    openDialog("period-dialog");
  });
  byId("period-manage-select").addEventListener("change", (event) => {
    const selected = state.periods.find((period) => period.id === event.target.value);
    byId("period-name").value = selected?.name || "";
  });
  byId("create-period").addEventListener("click", async () => {
    const name = byId("period-name").value.trim();
    if (!name) {
      byId("period-name").focus();
      return;
    }
    if (state.periods.some((period) => period.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      showToast(t("duplicate-period"));
      return;
    }
    const saved = await updateState(() => {
      const period = { id: newId(), name, subjects: [] };
      state.periods.push(period);
      state.activePeriodId = period.id;
    }, t("period-created"));
    if (saved) closeDialog(byId("period-dialog"));
  });
  byId("rename-period").addEventListener("click", async () => {
    const id = byId("period-manage-select").value;
    const name = byId("period-name").value.trim();
    if (!name) return;
    if (state.periods.some((period) =>
      period.id !== id && period.name.toLocaleLowerCase() === name.toLocaleLowerCase())) {
      showToast(t("duplicate-period"));
      return;
    }
    await updateState(() => {
      const period = state.periods.find((item) => item.id === id);
      if (!period) throw new Error(t("bad-file"));
      period.name = name;
    }, t("period-renamed"));
    renderPeriods();
  });
  byId("delete-period").addEventListener("click", async () => {
    if (state.periods.length <= 1) {
      showToast(t("last-period"));
      return;
    }
    const id = byId("period-manage-select").value;
    const period = state.periods.find((item) => item.id === id);
    if (!period || !window.confirm(t("confirm-delete-period", period.name))) return;
    const saved = await updateState(() => {
      state.periods = state.periods.filter((item) => item.id !== id);
      if (state.activePeriodId === id) state.activePeriodId = state.periods[0].id;
    }, t("period-deleted"));
    if (saved) closeDialog(byId("period-dialog"));
  });

  byId("sort-select").addEventListener("change", async (event) => {
    if (!SORT_MODES.includes(event.target.value)) return;
    await updateState(() => { state.sortMode = event.target.value; });
  });
  byId("search-input").addEventListener("input", renderSubjects);

  byId("language-select").addEventListener("change", async (event) => {
    await updateState(() => { state.settings.language = event.target.value; });
  });
  byId("theme-select").addEventListener("change", async (event) => {
    await updateState(() => { state.settings.theme = event.target.value; });
  });
  byId("text-size-select").addEventListener("change", async (event) => {
    await updateState(() => { state.settings.textSize = event.target.value; });
  });
  byId("settings-button").addEventListener("click", () => openDialog("settings-dialog"));
  byId("profile-button")?.addEventListener("click", () => {
    byId("edit-profile-name").value = state.profile?.name || "";
    byId("edit-profile-level").value = state.profile?.level || "L1";
    openDialog("profile-dialog");
  });
  byId("profile-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const name = byId("edit-profile-name").value.trim();
    const level = byId("edit-profile-level").value;
    if (!name || !PASS_MARKS[level]) return;
    const saved = await updateState(() => {
      state.profile = { name, level };
    }, t("profile-saved"));
    if (saved) closeDialog(byId("profile-dialog"));
  });

  byId("export-csv").addEventListener("click", () => {
    downloadFile(
      `mamoyenne-${safeFilename(state.profile.name)}-sessions.csv`,
      exportPeriodsCsv(state.periods, PASS_MARKS[state.profile.level]),
      "text/csv;charset=utf-8",
    );
    showToast(t("csv-exported"));
  });
  byId("export-pdf").addEventListener("click", () => {
    renderPrintReport();
    const previousTitle = document.title;
    document.title = `${t("print-grade-report")} - ${safeFilename(state.profile.name)}`;
    try {
      window.print();
    } finally {
      document.title = previousTitle;
    }
  });
  byId("csv-input").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const imported = parseCsvImport(await file.text());
      const groups = new Map();
      for (const item of imported) {
        const name = item.session || activePeriod().name;
        const key = name.trim().toLocaleLowerCase();
        if (!groups.has(key)) groups.set(key, { name, subjects: [] });
        groups.get(key).subjects.push(item);
      }
      const periods = new Map(state.periods.map((period) =>
        [period.name.trim().toLocaleLowerCase(), period]));
      let added = 0;
      let updated = 0;
      for (const [key, group] of groups) {
        const existing = new Map((periods.get(key)?.subjects || []).map((subject) =>
          [subject.name.toLocaleLowerCase(), subject]));
        for (const item of group.subjects) {
          if (existing.has(item.name.toLocaleLowerCase())) updated += 1;
          else {
            added += 1;
            existing.set(item.name.toLocaleLowerCase(), item);
          }
        }
      }
      if (!window.confirm(t("confirm-import", added, updated, groups.size))) return;
      await updateState(() => {
        for (const [key, group] of groups) {
          let period = state.periods.find((item) =>
            item.name.trim().toLocaleLowerCase() === key);
          if (!period) {
            period = { id: newId(), name: group.name, subjects: [] };
            state.periods.push(period);
          }
          const byName = new Map(period.subjects.map((subject) =>
            [subject.name.toLocaleLowerCase(), subject]));
          for (const item of group.subjects) {
            const current = byName.get(item.name.toLocaleLowerCase());
            if (current) current.grade = item.grade;
            else {
              const addedOrder = period.subjects.reduce(
                (largest, subject) => Math.max(largest, subject.addedOrder ?? -1), -1) + 1;
              const subject = { id: newId(), name: item.name, grade: item.grade, addedOrder };
              period.subjects.push(subject);
              byName.set(item.name.toLocaleLowerCase(), subject);
            }
          }
        }
      }, t("csv-imported", imported.length, groups.size));
    } catch (error) {
      showToast(error.message || t("bad-file"));
    } finally {
      event.target.value = "";
    }
  });

  byId("export-backup").addEventListener("click", () => {
    const stamp = new Date().toISOString().slice(0, 10);
    downloadFile(`mamoyenne-${stamp}.json`, JSON.stringify(state, null, 2), "application/json");
    showToast(t("backup-exported"));
  });
  byId("backup-input").addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const imported = normalizeState(JSON.parse(await file.text()));
      if (!window.confirm(t("confirm-restore"))) return;
      const saved = await updateState(() => { state = imported; }, t("backup-imported"));
      if (saved) closeDialog(byId("settings-dialog"));
    } catch (error) {
      showToast(error.message || t("bad-file"));
    } finally {
      event.target.value = "";
    }
  });
  byId("clear-data").addEventListener("click", async () => {
    if (!window.confirm(t("confirm-clear"))) return;
    const settings = { ...state.settings };
    await updateState(() => {
      state = createEmptyState();
      state.settings = settings;
    });
    closeDialog(byId("settings-dialog"));
  });
  byId("install-button").addEventListener("click", async () => {
    if (installPrompt) {
      installPrompt.prompt();
      await installPrompt.userChoice;
      installPrompt = null;
      return;
    }
    const userAgent = navigator.userAgent;
    byId("install-instructions").textContent = /iPhone|iPad|iPod/.test(userAgent)
      ? t("install-ios")
      : /Android/.test(userAgent) ? t("install-android") : t("install-desktop");
    openDialog("install-dialog");
  });
  document.querySelectorAll("[data-close-dialog]").forEach((button) => {
    button.addEventListener("click", () => closeDialog(button.closest("dialog")));
  });
  for (const dialog of document.querySelectorAll("dialog")) {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) closeDialog(dialog);
    });
  }
}

async function start() {
  try {
    await openDatabase();
    const stored = await readStoredState();
    state = stored === null ? createEmptyState() : normalizeState(stored);
    if (stored !== null && JSON.stringify(state) !== JSON.stringify(stored)) {
      await writeStoredState();
    }
    bindEvents();
    render();
    if ("serviceWorker" in navigator) {
      try {
        await navigator.serviceWorker.register("./sw.js");
      } catch (error) {
        console.error("Service worker registration failed:", error);
        showToast(t("offline-error"));
      }
    }
  } catch (error) {
    document.body.innerHTML = "";
    const message = document.createElement("main");
    message.className = "startup-error";
    const heading = document.createElement("h1");
    heading.textContent = "MaMoyenne";
    const detail = document.createElement("p");
    detail.textContent = `Impossible de démarrer l'application : ${error.message}`;
    message.append(heading, detail);
    document.body.append(message);
  }
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  installPrompt = event;
});

start();
