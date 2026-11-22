export const PASS_MARKS = Object.freeze({ L1: 70, L2: 70, L3: 75, L4: 80 });

export const SORT_MODES = Object.freeze(["added", "graded", "best", "worst", "custom"]);
export const DEFAULT_PERIOD_NAMES = Object.freeze(["1ère session", "2ème session"]);

export const DEFAULT_SETTINGS = Object.freeze({
  language: "fr",
  theme: "light",
  textSize: "normal",
});

export function createEmptyState() {
  return {
    version: 1,
    profile: null,
    periods: [],
    sessionsInitialized: true,
    activePeriodId: null,
    sortMode: "added",
    settings: { ...DEFAULT_SETTINGS },
  };
}

export function newId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

export function createInitialPeriods() {
  return DEFAULT_PERIOD_NAMES.map((name) => ({ id: newId(), name, subjects: [] }));
}

export function parseGrade(value) {
  const text = String(value ?? "").trim();
  if (!text || text === "-" || text.toUpperCase() === "NULL") return null;
  if (!/^\d{1,3}([.,]\d{1,2})?$/.test(text)) {
    throw new Error("La note doit être un nombre entre 0 et 100.");
  }
  const grade = Number(text.replace(",", "."));
  if (!Number.isFinite(grade) || grade < 0 || grade > 100) {
    throw new Error("La note doit être comprise entre 0 et 100.");
  }
  return grade;
}

export function average(subjects) {
  const grades = subjects.filter((subject) => subject.grade !== null).map((subject) => subject.grade);
  if (grades.length === 0) return null;
  return grades.reduce((sum, grade) => sum + grade, 0) / grades.length;
}

export function averageAcrossPeriods(periods) {
  return average(periods.flatMap((period) => period.subjects));
}

export function countRetakes(subjects, passMark) {
  return subjects.filter((subject) => subject.grade !== null && subject.grade < passMark).length;
}

export function sortSubjects(subjects, mode) {
  if (!SORT_MODES.includes(mode)) throw new Error("Mode de tri inconnu.");
  const indexed = subjects.map((subject, index) => ({ subject, index }));
  if (mode === "custom") return indexed.map(({ subject }) => subject);
  if (mode === "added") {
    indexed.sort((left, right) =>
      (left.subject.addedOrder ?? left.index) - (right.subject.addedOrder ?? right.index));
    return indexed.map(({ subject }) => subject);
  }
  indexed.sort((left, right) => {
    const a = left.subject.grade;
    const b = right.subject.grade;
    if (a === null || b === null) {
      if (a === b) return left.index - right.index;
      return a === null ? 1 : -1;
    }
    if (a === b) return left.index - right.index;
    if (mode === "graded") return left.index - right.index;
    return mode === "best" ? b - a : a - b;
  });
  return indexed.map(({ subject }) => subject);
}

export function filterSubjects(subjects, query) {
  const normalized = String(query ?? "").trim().toLocaleLowerCase();
  if (!normalized) return [...subjects];
  return subjects.filter((subject) => subject.name.toLocaleLowerCase().includes(normalized));
}

export function normalizeState(value) {
  if (!value || typeof value !== "object" || Array.isArray(value) || value.version !== 1) {
    throw new Error("Ce fichier de sauvegarde n'est pas reconnu.");
  }
  const settings = { ...DEFAULT_SETTINGS, ...(value.settings || {}) };
  if (!["fr", "en"].includes(settings.language)
      || !["light", "dark"].includes(settings.theme)
      || !["normal", "large"].includes(settings.textSize)) {
    throw new Error("Les paramètres de la sauvegarde sont invalides.");
  }
  if (!SORT_MODES.includes(value.sortMode)) throw new Error("Le tri de la sauvegarde est invalide.");

  if (value.profile === null && Array.isArray(value.periods) && value.periods.length === 0) {
    return { ...createEmptyState(), settings, sortMode: value.sortMode };
  }
  const profile = value.profile;
  if (!profile || !Object.prototype.hasOwnProperty.call(PASS_MARKS, profile.level)
      || typeof profile.name !== "string" || !profile.name.trim()) {
    throw new Error("Le profil de la sauvegarde est invalide.");
  }
  if (!Array.isArray(value.periods) || value.periods.length === 0) {
    throw new Error("La sauvegarde doit contenir au moins une période.");
  }
  if (value.sessionsInitialized !== undefined
      && typeof value.sessionsInitialized !== "boolean") {
    throw new Error("Le marqueur des sessions de la sauvegarde est invalide.");
  }
  const ids = new Set();
  const periodNames = new Set();
  let periods = value.periods.map((period) => {
    if (!period || typeof period.id !== "string" || !period.id
        || ids.has(period.id) || typeof period.name !== "string" || !period.name.trim()
        || !Array.isArray(period.subjects)) {
      throw new Error("Une période de la sauvegarde est invalide.");
    }
    ids.add(period.id);
    const periodKey = period.name.trim().toLocaleLowerCase();
    if (periodNames.has(periodKey)) throw new Error("La sauvegarde contient des périodes en double.");
    periodNames.add(periodKey);
    const names = new Set();
    const subjectIds = new Set();
    const subjects = period.subjects.map((subject, index) => {
      if (!subject || typeof subject.id !== "string" || !subject.id
          || typeof subject.name !== "string" || !subject.name.trim()) {
        throw new Error("Une matière de la sauvegarde est invalide.");
      }
      if (subjectIds.has(subject.id)) throw new Error("La sauvegarde contient des matières en double.");
      subjectIds.add(subject.id);
      const key = subject.name.trim().toLocaleLowerCase();
      if (names.has(key)) throw new Error("La sauvegarde contient des matières en double.");
      names.add(key);
      if (subject.grade !== null
          && (typeof subject.grade !== "number" || !Number.isFinite(subject.grade)
            || subject.grade < 0 || subject.grade > 100)) {
        throw new Error("Une note de la sauvegarde est invalide.");
      }
      const addedOrder = Number.isSafeInteger(subject.addedOrder) && subject.addedOrder >= 0
        ? subject.addedOrder : index;
      return { id: subject.id, name: subject.name.trim(), grade: subject.grade, addedOrder };
    });
    return { id: period.id, name: period.name.trim(), subjects };
  });
  if (!periods.some((period) => period.id === value.activePeriodId)) {
    throw new Error("La période active de la sauvegarde est introuvable.");
  }
  if (periods.length === 1 && value.sessionsInitialized !== true) {
    periods = [
      { ...periods[0], name: DEFAULT_PERIOD_NAMES[0] },
      { id: newId(), name: DEFAULT_PERIOD_NAMES[1], subjects: [] },
    ];
  }
  return {
    version: 1,
    profile: { level: profile.level, name: profile.name.trim() },
    periods,
    sessionsInitialized: true,
    activePeriodId: value.activePeriodId,
    sortMode: value.sortMode,
    settings,
  };
}

function parseCsvRows(text, delimiter) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted) {
      if (character === '"' && text[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else if (character === '"') {
        quoted = false;
      } else {
        cell += character;
      }
    } else if (character === '"' && cell.length === 0) {
      quoted = true;
    } else if (character === delimiter) {
      row.push(cell);
      cell = "";
    } else if (character === "\n" || character === "\r") {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(cell);
      if (row.some((item) => item.trim())) rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += character;
    }
  }
  if (quoted) throw new Error("Le fichier CSV contient un guillemet non fermé.");
  row.push(cell);
  if (row.some((item) => item.trim())) rows.push(row);
  return rows;
}

function removeAccents(value) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toLocaleLowerCase();
}

export function parseCsvImport(text) {
  const content = String(text ?? "").replace(/^\uFEFF/, "");
  const firstLine = content.split(/\r?\n/, 1)[0] || "";
  const delimiter = firstLine.includes(";") ? ";" : firstLine.includes("\t") ? "\t" : ",";
  const rows = parseCsvRows(content, delimiter);
  if (rows.length === 0) throw new Error("Aucune matière trouvée dans ce fichier.");

  const header = rows[0].map(removeAccents);
  const nameColumn = header.findIndex((value) => ["matiere", "subject"].includes(value));
  const gradeColumn = header.findIndex((value) => ["note", "grade"].includes(value));
  const sessionColumn = header.findIndex((value) => ["session", "periode", "period"].includes(value));
  const hasHeader = nameColumn >= 0 && gradeColumn >= 0;
  const start = hasHeader ? 1 : 0;
  const nameIndex = hasHeader ? nameColumn : 0;
  const noteIndex = hasHeader ? gradeColumn : 1;
  const imported = [];

  for (let rowIndex = start; rowIndex < rows.length; rowIndex += 1) {
    const row = rows[rowIndex];
    const name = (row[nameIndex] || "").trim();
    const normalizedName = removeAccents(name);
    if (!name || ["matiere", "subject"].includes(normalizedName)
        || (normalizedName.startsWith("moyenne")
          && (sessionColumn >= 0 || !(row[1] || "").trim()))
        || (normalizedName === "reprises" && !(row[1] || "").trim())) continue;
    const session = hasHeader && sessionColumn >= 0 ? (row[sessionColumn] || "").trim() : "";
    try {
      imported.push({
        ...(session ? { session } : {}),
        name,
        grade: parseGrade(row[noteIndex] || ""),
      });
    } catch (error) {
      throw new Error(`Note illisible pour « ${name} » : ${row[noteIndex] || ""}`);
    }
  }
  if (imported.length === 0) throw new Error("Aucune matière trouvée dans ce fichier.");
  return imported;
}

function csvCell(value) {
  const text = String(value);
  return /[;"\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function exportPeriodsCsv(periods, passMark) {
  const rows = [["Session", "Matière", "Note", "Statut"]];
  for (const period of periods) {
    for (const subject of period.subjects) {
      const status = subject.grade === null
        ? "En attente" : subject.grade >= passMark ? "Validé" : "Reprise";
      rows.push([
        period.name,
        subject.name,
        subject.grade === null ? "NULL" : String(subject.grade),
        status,
      ]);
    }
    rows.push([
      period.name,
      "Moyenne",
      average(period.subjects)?.toFixed(2).replace(".", ",") ?? "—",
      "",
    ]);
  }
  rows.push([
    "Générale",
    "Moyenne générale",
    averageAcrossPeriods(periods)?.toFixed(2).replace(".", ",") ?? "—",
    "",
  ]);
  return `\uFEFF${rows.map((row) => row.map(csvCell).join(";")).join("\r\n")}`;
}
