(function (root) {
  'use strict';
  const DAY = 86400000;
  const TYPES = { Theory: 'Теория', Video: 'Видео', Reading: 'Чтение', Practice: 'Практика', Lab: 'Лаборатория', Quiz: 'Тест', Project: 'Проект', Review: 'Повторение', Optional: 'Дополнительно' };
  const iso = d => [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'), String(d.getDate()).padStart(2, '0')].join('-');
  const today = state => state?.settings?.referenceDate || iso(new Date());
  const parse = s => new Date(s + 'T12:00:00');
  const validDate = s => typeof s === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(parse(s)) && iso(parse(s)) === s;
  const addDays = (s, n) => { const d = parse(s); d.setDate(d.getDate() + n); return iso(d); };
  const diff = (a, b) => Math.round((Date.parse(a + 'T12:00:00Z') - Date.parse(b + 'T12:00:00Z')) / DAY);
  const weekStart = s => addDays(s, -(parse(s).getDay() + 6) % 7);
  const percent = (a, b) => b ? Math.round(a / b * 1000) / 10 : 0;
  const core = tasks => tasks.filter(t => !t.optional);
  function progress(tasks) { const req = core(tasks); return { total: req.length, done: req.filter(t => t.completed).length, percent: percent(req.filter(t => t.completed).length, req.length), bonusTotal: tasks.length - req.length, bonusDone: tasks.filter(t => t.optional && t.completed).length }; }
  const overdue = (tasks, day) => tasks.filter(t => !t.optional && !t.completed && t.scheduledDate && t.scheduledDate < day);
  const range = (tasks, from, to) => tasks.filter(t => t.scheduledDate && t.scheduledDate >= from && t.scheduledDate <= to);
  function unresolved(state, task) {
    const topic = state.topics.find(x => x.id === task.topicId);
    const sub = state.subtopics.find(x => x.id === task.subtopicId);
    const ids = [...(topic?.prerequisites || []), ...(sub?.prerequisites || [])];
    return ids.filter(id => { const ts = state.tasks.filter(t => t.topicId === id || t.subtopicId === id); return ts.some(t => !t.optional && !t.completed); });
  }
  function debtPriority(state, task, day) {
    const age = Math.max(0, diff(day, task.scheduledDate || day));
    const blocking = state.topics.some(x => x.prerequisites.includes(task.topicId)) || state.subtopics.some(x => (x.prerequisites || []).includes(task.subtopicId));
    const score = age + (blocking ? 10 : 0) + ({ critical: 20, high: 10, medium: 4, low: 0 }[task.priority] || 0);
    return { score: score - (task.optional ? 100 : 0), label: score >= 25 ? 'Critical' : score >= 12 ? 'High' : 'Medium', age, blocking };
  }
  function recommend(state, tasks = state.tasks, day = today(state)) {
    return tasks.filter(t => !t.completed).sort((a, b) => Number(a.optional) - Number(b.optional) || Number(unresolved(state, a).length > 0) - Number(unresolved(state, b).length > 0) || Number(!(a.scheduledDate && a.scheduledDate < day)) - Number(!(b.scheduledDate && b.scheduledDate < day)) || (a.scheduledDate || '9999').localeCompare(b.scheduledDate || '9999') || debtPriority(state, b, day).score - debtPriority(state, a, day).score);
  }
  function streak(state, day = today(state)) {
    const completed = new Set(state.tasks.filter(t => t.completedAt && t.completed).map(t => t.completedAt.slice(0, 10)));
    const start = state.settings.startDate;
    let current = 0, longest = 0;
    for (let d = start; d <= day; d = addDays(d, 1)) {
      const expected = state.settings.studyDays.includes(parse(d).getDay());
      if (completed.has(d)) { current++; longest = Math.max(longest, current); }
      else if (expected && d < day) current = 0;
    }
    return { current, longest, studiedToday: completed.has(day) };
  }
  function stats(state, day = today(state)) {
    const total = progress(state.tasks), req = core(state.tasks), due = req.filter(t => t.scheduledDate && t.scheduledDate <= day);
    const start = weekStart(day), month = day.slice(0, 7);
    const expected = percent(due.length, req.length), delta = Math.round((total.percent - expected) * 10) / 10;
    const debts = overdue(state.tasks, day), debtDays = new Set(debts.map(t => t.scheduledDate)).size;
    const n = diff(day, state.settings.startDate);
    const activeDates = [...new Set(req.filter(t => t.scheduledDate && t.scheduledDate < day).map(t => t.scheduledDate))];
    return { total, today: progress(range(state.tasks, day, day)), week: progress(range(state.tasks, start, addDays(start, 6))), month: progress(state.tasks.filter(t => t.scheduledDate?.startsWith(month))), expected, delta, debts, debtDays, studyWeek: n < 0 ? 0 : Math.floor(n / 7) + 1, studyDay: n < 0 ? 0 : n + 1, dayOfWeek: n < 0 ? 0 : n % 7 + 1, status: delta > 0 ? 'Опережаю план' : debts.length === 0 ? 'По графику' : debtDays >= 7 || delta < -5 ? 'Серьёзное отставание' : 'Небольшое отставание', streak: streak(state, day), doneWeek: state.tasks.filter(t => t.completed && t.completedAt?.slice(0, 10) >= start && t.completedAt?.slice(0, 10) <= day).length, doneMonth: state.tasks.filter(t => t.completed && t.completedAt?.startsWith(month) && t.completedAt.slice(0, 10) <= day).length, average: activeDates.length ? Math.round(activeDates.reduce((a, d) => a + progress(range(req, d, d)).percent, 0) / activeDates.length) : 0 };
  }
  function history(state, from, to, step = 7) {
    const required = core(state.tasks), points = [];
    for (let d = from; d <= to; d = addDays(d, step)) points.push({ date: d, planned: percent(required.filter(t => t.scheduledDate && t.scheduledDate <= d).length, required.length), actual: d <= today(state) ? percent(required.filter(t => t.completed && t.completedAt && t.completedAt.slice(0, 10) <= d).length, required.length) : null });
    if (points.at(-1)?.date !== to) points.push(...history(state, to, to, step));
    return points;
  }
  function moveTasks(state, ids, date) {
    if (!validDate(date)) throw Error('Укажите корректную дату.');
    state.tasks.forEach(t => { if (ids.includes(t.id)) { t.scheduledDate = date; t.manuallyScheduled = true; } });
  }
  function spread(state, ids, start) {
    if (!state.settings.studyDays.length) throw Error('Выберите хотя бы один учебный день.');
    let date = start, used = 0;
    const moved = [];
    for (const task of recommend(state, state.tasks.filter(t => ids.includes(t.id)))) {
      for (let guard = 0; guard < 4000; guard++) {
        const weekday = parse(date).getDay(), capacity = (weekday === 0 || weekday === 6 ? state.settings.weekendHours : state.settings.weekdayHours) * 60;
        const existing = state.tasks.filter(t => !ids.includes(t.id) && !t.completed && t.scheduledDate === date).reduce((n, t) => n + t.estimatedMinutes, 0);
        if (state.settings.studyDays.includes(weekday) && (used + existing === 0 || used + existing + task.estimatedMinutes <= capacity)) break;
        date = addDays(date, 1); used = 0;
      }
      task.scheduledDate = date; task.manuallyScheduled = true; used += task.estimatedMinutes; moved.push(task);
    }
    return moved;
  }
  root.OpsModel = { TYPES, iso, today, parse, validDate, addDays, diff, weekStart, percent, core, progress, overdue, range, unresolved, debtPriority, recommend, streak, stats, history, moveTasks, spread };
})(typeof window !== 'undefined' ? window : globalThis);
