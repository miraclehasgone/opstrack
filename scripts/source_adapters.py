"""Executed by build_curriculum.py. Adds all analysed source units to the shared taxonomy."""
import difflib

def norm(s):
    return set(re.findall(r'[a-zа-яё0-9]{3,}', s.lower())) - {'для','через','как','что','это','или','при','про','без','после','основы','практика','теория'}

def match_existing(title, sub, source):
    a=norm(title)
    best=None; score=0
    for t in tasks:
        if t['subtopicId'] != sub: continue
        b=norm(t['title'])
        j=len(a&b)/max(1,len(a|b))
        seq=difflib.SequenceMatcher(None,title.lower(),t['title'].lower()).ratio()
        value=max(j,seq if min(len(title),len(t['title']))>12 else 0)
        if value>score:best,score=t,value
    if best and score>=.73:
        if source not in best['sources']:best['sources'].append(source)
        return best
    return None

road=read(R/'data/roadmap-structured.json')
for unit in road['units']:
    if unit.get('duplicateOf'): continue
    sub=classify(unit['title']+' '+unit.get('description',''))
    t=match_existing(unit['title'],sub,'Просто DevOps')
    if not t:
        typ=unit.get('type','Theory')
        if typ not in ['Theory','Video','Reading','Practice','Lab','Quiz','Project','Review','Optional']:typ='Theory'
        t=add(unit['title'],sub,'Просто DevOps',typ,None,None,unit.get('description',''),unit.get('optional',False) or typ=='Optional',[dict(file='sources/roadmap.pdf',label='Roadmap Просто DevOps',url=unit.get('url'))],20 if typ=='Video' else 30)
        t['sourceUnitId']=unit['id'];t['scheduleOrigin']='Встроено по теме из PDF roadmap'
    elif not any(r.get('label')=='Roadmap Просто DevOps' for r in t['sourceRefs']):t['sourceRefs'].append(dict(file='sources/roadmap.pdf',label='Roadmap Просто DevOps',url=unit.get('url')))

ym=read(R/'data/yandex-manifest.json');yc=read(R/'data/yandex-curated.json');yq=read(R/'data/yandex-quizzes.json')
curated={x['lessonId']:x for x in yc['practices']}
lessons={}
fallback={0:'projects-0',1:'git-0',2:'cicd-0',3:'linux-0',4:'cicd-3',5:'terraform-0',6:'databases-0',7:'docker-0',8:'web-2',9:'kubernetes-0',10:'monitoring-0'}
for module in ym['modules']:
    for lesson in module['lessons']:
        lessons[lesson['id']]=lesson
        joined=lesson['title']+' '+module['title']
        sub=classify(joined,fallback.get(module['number'],'projects-1'))
        kind=lesson.get('kind','theory')
        typ={'theory':'Reading','practice':'Lab','review':'Review','bonus':'Optional','instruction':'Practice','solution':'Review','introduction':'Reading'}.get(kind,'Theory')
        clean=curated.get(lesson['id'])
        desc=''
        if clean: desc='Результат: '+clean.get('artifact','')+'\n\nЧек-лист:\n'+'\n'.join('• '+x for x in clean.get('checklist',[]))
        else:
            points=[x for x in lesson.get('learningContext',[]) if len(x)<500][:4]
            desc='\n'.join(points)
        optional=kind in ['bonus','solution','introduction']
        t=match_existing(lesson['title'],sub,'Яндекс Практикум')
        if not t:t=add(lesson['title'],sub,'Яндекс Практикум',typ,None,None,desc,optional,[dict(file='sources/yandex-course.zip',label=f"Яндекс · глава {module['number']}",url=lesson.get('sourceUrl'))],60 if typ=='Lab' else 35)
        else:
            t['sourceRefs'].append(dict(file='sources/yandex-course.zip',label=f"Яндекс · глава {module['number']}",url=lesson.get('sourceUrl')))
            if desc and not t['description']:t['description']=desc
        t['yandexLessonId']=lesson['id']; t['sourceAccess']='Снимок 2024 года; практическая среда и внешние ссылки могут требовать замены.'
        for v in lesson.get('videos',[]):
            vt=add(v.get('title') or ('Видео к '+lesson['title']),sub,'Яндекс Практикум','Video',None,None,'Видео из материалов урока.',False,[dict(file='sources/yandex-course.zip',label='Яндекс · видео',url=v.get('url'))],20)
            vt['yandexLessonId']=lesson['id']
for q in yq:
    lesson=lessons.get(q['lessonId'])
    if not lesson:continue
    module_number=lesson['moduleNumber']; sub=classify(lesson['title'],fallback.get(module_number,'projects-1'))
    title=q['question'] or ('Проверочное задание к «'+lesson['title']+'»')
    qt=add(title,sub,'Яндекс Практикум','Quiz',None,None,'Самопроверка из сохранённого урока; ответы исходного снимка не считаются вашим прогрессом.',False,[dict(file='sources/yandex-course.zip',label=f'Яндекс · {lesson["title"]}',url=lesson.get('sourceUrl'))],8)
    qt['yandexLessonId']=lesson['id'];qt['sourceUnitId']=q['id']

# Assign source additions to the least loaded day of a matching Word week.
word_tasks=[t for t in tasks if t['source']=='Мой план' and t['scheduledDate']]
extra=[t for t in tasks if not t['scheduledDate']]
loads={}
for t in word_tasks: loads[t['scheduledDate']]=loads.get(t['scheduledDate'],0)+t['estimatedMinutes']
topic_weeks={}
for t in word_tasks:topic_weeks.setdefault(t['topicId'],set()).add(t['week'])
for t in extra:
    candidate_weeks=topic_weeks.get(t['topicId'],set())
    candidates=[]
    for wno in candidate_weeks:
        w=weeks[wno-1]
        candidates.extend(add_days for add_days in [(datetime.date.fromisoformat(w['start_date'])+datetime.timedelta(days=i)).isoformat() for i in range(7)])
    if not candidates:
        candidates=[(datetime.date.fromisoformat('2027-10-04')+datetime.timedelta(days=i)).isoformat() for i in range(180)]
    day=min(candidates,key=lambda d:(loads.get(d,0),d))
    t['scheduledDate']=day;t['originalDate']=day;t['scheduleOrigin']='Интегрировано по совпадающей теме и доступной дневной нагрузке'
    loads[day]=loads.get(day,0)+t['estimatedMinutes']

source_summary=[
 {'id':'my-plan','title':'Мой Word-план','file':'sources/study-plan.docx','weeks':56,'items':388,'routes':168,'outcomes':56,'note':'Календарная основа 07.09.2026—03.10.2027. Дневное распределение рассчитано из недельных списков.'},
 {'id':'yandex','title':'Яндекс Практикум','file':'sources/yandex-course.zip','pages':92,'lessons':91,'practices':24,'quizzes':252,'videos':5,'note':'Снимки 2024 года. Исторические ответы, пароли и токены не перенесены в интерфейс.'},
 {'id':'roadmap','title':'Roadmap Просто DevOps','file':'sources/roadmap.pdf','sections':8,'subtopics':49,'items':437,'videos':21,'links':3,'note':'PDF из одной большой страницы; очищенные единицы сопоставлены с общей таксономией.'}
]
write(R/'data/source-summary.json',source_summary)
