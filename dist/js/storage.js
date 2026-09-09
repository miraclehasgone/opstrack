(function (root) {
  'use strict';
  const KEY = 'opstrack.state.v2';
  const clone = x => JSON.parse(JSON.stringify(x));
  function initial(catalog) {
    return { schemaVersion: 1, catalogVersion: catalog.version, settings: { startDate: catalog.startDate, studyDays: [1, 2, 3, 4, 5, 6, 0], weekdayHours: 1, weekendHours: 3, theme: 'dark', referenceDate: '' }, topics: clone(catalog.topics), subtopics: clone(catalog.subtopics), tasks: clone(catalog.tasks), reviewQueue: [], quickNotes: '', activity: [], savedAt: null };
  }
  function validate(data) {
    const fail = msg => { throw Error('Неверный backup: ' + msg); };
    if (!data || data.schemaVersion !== 1) fail('неподдерживаемая версия.');
    if (!Array.isArray(data.tasks) || data.tasks.length > 30000 || !Array.isArray(data.topics) || !Array.isArray(data.subtopics)) fail('нет структуры учебного плана.');
    const validId = id => typeof id === 'string' && /^[a-zA-Z0-9_-]{1,100}$/.test(id);
    for (const list of [data.tasks, data.topics, data.subtopics]) {
      if (new Set(list.map(x => x.id)).size !== list.length) fail('повторяющиеся идентификаторы.');
      if (list.some(x => !validId(x.id) || typeof x.title !== 'string' || x.title.length > 20000)) fail('повреждённые записи.');
    }
    const topics = new Set(data.topics.map(x => x.id)), subs = new Map(data.subtopics.map(x => [x.id, x]));
    if (data.topics.some(x => !Array.isArray(x.prerequisites) || x.prerequisites.some(id => !topics.has(id)))) fail('зависимости тем.');
    if (data.subtopics.some(x => !topics.has(x.topicId) || (x.prerequisites || []).some(id => !subs.has(id)))) fail('связи подтем.');
    const m = root.OpsModel;
    for (const t of data.tasks) {
      if (!topics.has(t.topicId) || !subs.has(t.subtopicId) || subs.get(t.subtopicId).topicId !== t.topicId) fail('связи заданий.');
      if (!(t.type in m.TYPES) || typeof t.completed !== 'boolean' || typeof t.optional !== 'boolean' || !Number.isFinite(t.estimatedMinutes) || t.estimatedMinutes < 0 || t.estimatedMinutes > 10000) fail('поля задания.');
      if (t.scheduledDate !== null && !m.validDate(t.scheduledDate)) fail('дата задания.');
      if (t.completed && (!t.completedAt || !m.validDate(t.completedAt.slice(0, 10)))) fail('дата выполнения.');
      if (typeof t.source !== 'string' || typeof t.description !== 'string' || typeof t.notes !== 'string') fail('текст задания.');
      if (!['critical','high','medium','low'].includes(t.priority)) fail('приоритет.');
    }
    const s = data.settings;
    if (!s || !m.validDate(s.startDate) || s.referenceDate && !m.validDate(s.referenceDate) || !Array.isArray(s.studyDays) || !s.studyDays.length || s.studyDays.some(x => !Number.isInteger(x) || x < 0 || x > 6) || !['light','dark'].includes(s.theme)) fail('настройки.');
    if (![s.weekdayHours, s.weekendHours].every(x => Number.isFinite(x) && x > 0 && x <= 24)) fail('учебная нагрузка.');
    if (!Array.isArray(data.reviewQueue) || data.reviewQueue.some(x => !topics.has(x) && !subs.has(x)) || typeof data.quickNotes !== 'string') fail('заметки и повторения.');
    const graph = new Map([...data.topics, ...data.subtopics].map(x => [x.id, x.prerequisites || []]));
    const seen = new Set(), stack = new Set();
    function visit(id) { if (stack.has(id)) fail('цикл зависимостей.'); if (seen.has(id)) return; stack.add(id); (graph.get(id) || []).forEach(visit); stack.delete(id); seen.add(id); }
    graph.forEach((_, id) => visit(id));
    return data;
  }
  function mergeCatalog(saved, catalog) {
    if (saved.catalogVersion === catalog.version) return saved;
    const old = new Map(saved.tasks.map(t => [t.id, t]));
    const merged = initial(catalog);
    merged.settings = { ...merged.settings, ...saved.settings };
    merged.tasks = catalog.tasks.map(task => {
      const prior = old.get(task.id);
      return prior ? { ...task, completed: prior.completed, completedAt: prior.completedAt, notes: prior.notes || '', scheduledDate: prior.manuallyScheduled ? prior.scheduledDate : task.scheduledDate, manuallyScheduled: Boolean(prior.manuallyScheduled) } : task;
    });
    merged.topics.push(...saved.topics.filter(x => x.custom && !merged.topics.some(y => y.id === x.id)));
    merged.subtopics.push(...saved.subtopics.filter(x => x.custom && !merged.subtopics.some(y => y.id === x.id)));
    merged.tasks.push(...saved.tasks.filter(x => x.custom && !merged.tasks.some(y => y.id === x.id)));
    merged.reviewQueue = saved.reviewQueue.filter(id => merged.topics.some(x => x.id === id) || merged.subtopics.some(x => x.id === id));
    merged.quickNotes = saved.quickNotes || '';
    merged.activity = saved.activity || [];
    merged.savedAt = saved.savedAt;
    return merged;
  }
  function load(catalog) {
    try { const text = localStorage.getItem(KEY); return text ? { state: validate(mergeCatalog(JSON.parse(text), catalog)), error: null } : { state: initial(catalog), error: null }; }
    catch (error) { return { state: initial(catalog), error: 'Сохранённые данные не удалось прочитать. Они не перезаписаны. Экспортируйте аварийную копию в настройках. ' + error.message, recovery: true }; }
  }
  function save(state) { state.savedAt = new Date().toISOString(); localStorage.setItem(KEY, JSON.stringify(state)); }
  function backup(state) { return JSON.stringify({ app: 'OpsTrack', exportedAt: new Date().toISOString(), ...state }, null, 2); }
  root.OpsStorage = { KEY, initial, validate, load, save, backup, clone, mergeCatalog };
})(typeof window !== 'undefined' ? window : globalThis);
