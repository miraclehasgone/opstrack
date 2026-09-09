const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const context = { console, globalThis: null };
context.globalThis = context;
vm.createContext(context);
vm.runInContext(fs.readFileSync('dist/js/model.js','utf8'), context);
const M = context.OpsModel;
vm.runInContext(fs.readFileSync('dist/js/storage.js','utf8'), context);
const Storage = context.OpsStorage;
const catalog = JSON.parse(fs.readFileSync('data/curriculum.json','utf8'));
const state = {
  topics: JSON.parse(JSON.stringify(catalog.topics)),
  subtopics: JSON.parse(JSON.stringify(catalog.subtopics)),
  tasks: JSON.parse(JSON.stringify(catalog.tasks)),
  settings: { startDate:'2026-09-07', referenceDate:'2026-09-09', studyDays:[1,2,3,4,5,6,0], weekdayHours:1, weekendHours:3 }
};
assert.equal(catalog.topics.length,16);
assert.equal(catalog.subtopics.length,75);
assert.equal(catalog.tasks.length,1186);
assert.equal(catalog.sourceSummary.find(x=>x.id==='my-plan').items,388);
assert.equal(catalog.sourceSummary.find(x=>x.id==='yandex').quizzes,252);
assert.equal(catalog.sourceSummary.find(x=>x.id==='roadmap').items,437);
const initial = M.stats(state,'2026-09-09');
assert(Number.isFinite(initial.total.percent));
assert(initial.debts.length > 0, 'initial debt must exist');
assert.deepEqual([...new Set(initial.debts.map(x=>x.scheduledDate))].sort(),['2026-09-07','2026-09-08']);
assert.equal(M.overdue([{scheduledDate:'2026-09-08',completed:false,optional:true}], '2026-09-09').length,0);
const debtTask = initial.debts[0];
debtTask.completed=true; debtTask.completedAt='2026-09-09T12:00:00.000Z';
assert(!M.overdue(state.tasks,'2026-09-09').some(x=>x.id===debtTask.id));
debtTask.completed=false; debtTask.completedAt=null;
assert(M.overdue(state.tasks,'2026-09-09').some(x=>x.id===debtTask.id));
const before=M.progress(state.tasks).percent;
debtTask.completed=true; debtTask.completedAt='2026-09-09T12:00:00.000Z';
assert(M.progress(state.tasks).percent>=before);
debtTask.completed=false; debtTask.completedAt=null;
const copy=JSON.parse(JSON.stringify(state));
copy.settings.studyDays=[1,3,5];
const target=copy.tasks.slice(0,4); target.forEach(t=>{t.scheduledDate=null;t.completed=false});
M.spread(copy,target.map(t=>t.id),'2026-09-10');
assert(target.every(t=>copy.settings.studyDays.includes(M.parse(t.scheduledDate).getDay())));
assert.equal(M.validDate('2026-09-09'),true);
assert.equal(M.validDate('2026-02-31'),false);
assert(M.history(state,'2026-09-07','2026-09-20',7).length>=3);
const persisted=Storage.initial(catalog);
assert.doesNotThrow(()=>Storage.validate(persisted));
assert.doesNotThrow(()=>Storage.validate(JSON.parse(Storage.backup(persisted))));
const brokenDate=JSON.parse(JSON.stringify(persisted));brokenDate.tasks[0].scheduledDate='2026-02-31';
assert.throws(()=>Storage.validate(brokenDate),/дата задания/);
const brokenLink=JSON.parse(JSON.stringify(persisted));brokenLink.tasks[0].topicId='missing';
assert.throws(()=>Storage.validate(brokenLink),/связи заданий/);
const old=JSON.parse(JSON.stringify(persisted));old.catalogVersion=1;old.tasks[0].completed=true;old.tasks[0].completedAt='2026-09-09T12:00:00.000Z';
const merged=Storage.mergeCatalog(old,catalog);
assert.equal(merged.tasks[0].completed,true);
assert.equal(merged.catalogVersion,3);
assert(catalog.tasks.some(t=>t.subtopicId==='network-7'));
console.log('model.test.js: all assertions passed');
