(function(root){'use strict';
const e=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const date=s=>s?new Intl.DateTimeFormat('ru-RU',{day:'numeric',month:'long',year:'numeric'}).format(OpsModel.parse(s)):'Без даты';
const shortDate=s=>s?new Intl.DateTimeFormat('ru-RU',{day:'numeric',month:'short'}).format(OpsModel.parse(s)):'—';
const icon={Theory:'◫',Video:'▷',Reading:'≡',Practice:'◇',Lab:'⌘',Quiz:'?',Project:'⬡',Review:'↻',Optional:'+'};
function taskRow(t){return `<div class="task-row ${t.completed?'completed':''}" data-task="${e(t.id)}"><input class="task-check" type="checkbox" ${t.completed?'checked':''} aria-label="${t.completed?'Снять отметку':'Отметить выполненным'}: ${e(t.title)}" data-action="toggle"><button class="task-title-button" data-action="open-task"><span class="task-title">${e(t.title)}</span><span class="task-meta"><span>${e(t.source)}</span><span>${t.estimatedMinutes} мин</span>${t.scheduledDate?`<span>${shortDate(t.scheduledDate)}</span>`:''}</span></button><span class="type-pill">${icon[t.type]||'·'} ${e(OpsModel.TYPES[t.type]||t.type)}</span></div>`}
function progressBar(p){return `<div class="progress-track" aria-label="Выполнено ${p}%"><div class="progress-fill" style="width:${Math.max(0,Math.min(100,p))}%"></div></div>`}
function toast(msg){const el=document.getElementById('toast');el.textContent=msg;el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),2300)}
function modal(html){const d=document.getElementById('modal');document.getElementById('modal-content').innerHTML=html;d.showModal();}
function closeModal(){document.getElementById('modal').close()}
root.OpsUI={e,date,shortDate,icon,taskRow,progressBar,toast,modal,closeModal};
})(window);
