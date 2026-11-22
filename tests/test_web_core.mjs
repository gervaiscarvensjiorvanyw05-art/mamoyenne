import test from "node:test";
import assert from "node:assert/strict";

import {
  average,
  countRetakes,
  exportCsv,
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

test("exports an importable CSV with the pass status and summary", () => {
  const csv = exportCsv(subjects, 70);
  assert.match(csv, /Meilleure;100;95;Validé/);
  assert.match(csv, /Faible;100;40;Reprise/);
  assert.deepEqual(parseCsvImport(csv).map(({ name, grade }) => [name, grade]), [
    ["Sans note", null],
    ["Moyenne", 70],
    ["Meilleure", 95],
    ["Faible", 40],
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
});
