import test from "node:test";
import assert from "node:assert/strict";

import {
  average,
  averageAcrossPeriods,
  countRetakes,
  exportPeriodsCsv,
  filterSubjects,
  normalizeState,
  parseCsvImport,
  parseGrade,
  sortSubjects,
} from "../web/core.mjs";

const subjects = [
  { id: "1", name: "Sans note", grade: null },
  { id: "2", name: "Moyenne", grade: 70 },
  { id: "3", name: "Meilleure", grade: 95 },
  { id: "4", name: "Faible", grade: 40 },
];

test("parses decimal commas and empty grades while rejecting out-of-range values", () => {
  assert.equal(parseGrade("15,5"), 15.5);
  assert.equal(parseGrade(""), null);
  assert.equal(parseGrade("NULL"), null);
  assert.throws(() => parseGrade("100,1"), /entre 0 et 100/);
  assert.throws(() => parseGrade("texte"), /nombre/);
});

test("calculates an unweighted mean and retakes while ignoring missing grades", () => {
  assert.equal(average(subjects), 68.33333333333333);
  assert.equal(countRetakes(subjects, 70), 1);
  assert.equal(average([{ grade: null }]), null);
});

test("sorts grades in the requested direction and keeps missing grades last", () => {
  assert.deepEqual(sortSubjects(subjects, "best").map((subject) => subject.name),
    ["Meilleure", "Moyenne", "Faible", "Sans note"]);
  assert.deepEqual(sortSubjects(subjects, "worst").map((subject) => subject.name),
    ["Faible", "Moyenne", "Meilleure", "Sans note"]);
  assert.deepEqual(sortSubjects(subjects, "graded").map((subject) => subject.name),
    ["Moyenne", "Meilleure", "Faible", "Sans note"]);
});

test("keeps the original add order when subjects have been manually reordered", () => {
  const reordered = [
    { id: "2", name: "Second", grade: null, addedOrder: 1 },
    { id: "1", name: "First", grade: null, addedOrder: 0 },
  ];
  assert.deepEqual(sortSubjects(reordered, "custom").map((subject) => subject.name), ["Second", "First"]);
  assert.deepEqual(sortSubjects(reordered, "added").map((subject) => subject.name), ["First", "Second"]);
});

test("filters subject names without changing the source order", () => {
  assert.deepEqual(filterSubjects(subjects, "ME"), [subjects[2]]);
  assert.deepEqual(filterSubjects(subjects, "  "), subjects);
});

test("imports quoted CSV subjects and decimal-comma grades", () => {
  const imported = parseCsvImport('\uFEFFMatière;Note\r\n"Sciences; nature";82,5\r\nMaths;\r\n');
  assert.deepEqual(imported, [
    { name: "Sciences; nature", grade: 82.5 },
    { name: "Maths", grade: null },
  ]);
});

test("imports a legacy single-session CSV without treating its summary as a subject", () => {
  const csv = "\uFEFFMatière;Coef;Note;Statut\r\n"
    + "Maths;100;95;Validé\r\n"
    + "Français;100;40;Reprise\r\n"
    + "Moyenne;;67,50;\r\n";
  assert.deepEqual(parseCsvImport(csv).map(({ name, grade }) => [name, grade]), [
    ["Maths", 95],
    ["Français", 40],
  ]);
});

test("exports and reimports both sessions with simple period and general averages", () => {
  const periods = [
    {
      name: "1ère session",
      subjects: [
        { id: "1", name: "Maths", grade: 80 },
        { id: "2", name: "Physique", grade: 60 },
      ],
    },
    {
      name: "2ème session",
      subjects: [{ id: "3", name: "Histoire", grade: 90 }],
    },
  ];
  const csv = exportPeriodsCsv(periods, 70);

  assert.match(csv, /Session;Matière;Note;Statut/);
  assert.match(csv, /1ère session;Moyenne;70,00;/);
  assert.match(csv, /2ème session;Moyenne;90,00;/);
  assert.match(csv, /Générale;Moyenne générale;76,67;/);
  assert.equal(averageAcrossPeriods(periods), 76.66666666666667);
  assert.deepEqual(parseCsvImport(csv), [
    { session: "1ère session", name: "Maths", grade: 80 },
    { session: "1ère session", name: "Physique", grade: 60 },
    { session: "2ème session", name: "Histoire", grade: 90 },
  ]);
});

test("rejects malformed or incomplete backup files", () => {
  assert.throws(() => normalizeState({ version: 2 }), /pas reconnu/);
  assert.throws(() => normalizeState({
    version: 1,
    profile: { level: "L5", name: "Test" },
    periods: [],
    activePeriodId: null,
    sortMode: "added",
  }), /profil.*invalide/);
});

test("accepts a full backup exported by the desktop application", () => {
  const imported = normalizeState({
    version: 1,
    profile: { level: "L2", name: "Test" },
    periods: [{
      id: "2",
      name: "Semestre 2",
      subjects: [{ id: "15", name: "Physique", grade: 82.5, addedOrder: 15 }],
    }],
    activePeriodId: "2",
    sortMode: "custom",
    settings: { language: "en", theme: "dark", textSize: "large" },
  });
  assert.equal(imported.periods[0].subjects[0].addedOrder, 15);
  assert.equal(imported.settings.theme, "dark");
  assert.equal(imported.periods[1].name, "2ème session");
});

test("migrates a one-period backup to two sessions without losing its grades", () => {
  const imported = normalizeState({
    version: 1,
    profile: { level: "L1", name: "Test" },
    periods: [{
      id: "old-period",
      name: "Période actuelle",
      subjects: [{ id: "maths", name: "Maths", grade: 84 }],
    }],
    activePeriodId: "old-period",
    sortMode: "added",
  });

  assert.equal(imported.periods[0].name, "1ère session");
  assert.equal(imported.periods[0].subjects[0].grade, 84);
  assert.equal(imported.periods[1].name, "2ème session");
  assert.deepEqual(imported.periods[1].subjects, []);
  assert.equal(imported.activePeriodId, "old-period");
  assert.equal(imported.sessionsInitialized, true);
});

test("does not recreate a session that the user intentionally removed", () => {
  const state = normalizeState({
    version: 1,
    profile: { level: "L1", name: "Test" },
    periods: [{
      id: "first",
      name: "1ère session",
      subjects: [],
    }],
    sessionsInitialized: true,
    activePeriodId: "first",
    sortMode: "added",
  });

  assert.equal(state.periods.length, 1);
});
