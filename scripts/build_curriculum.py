"""Build a reproducible, source-grounded catalogue. Python standard library only."""
import json,pathlib,re,datetime,hashlib,shutil
R=pathlib.Path(__file__).resolve().parents[1]
def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def write(p,x): pathlib.Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
weeks=read(R/'data/word-weeks.json')
spec=[
 ('network','Networking','От физического уровня до маршрутизации и сетей провайдера.',[],['Физический уровень','OSI / TCP-IP','Ethernet / MAC','ARP / ICMP','IPv4 / IPv6 / Subnetting','VLAN / Trunk','STP / RSTP / LACP','Static Routing','ACL / NAT','OSPF / IS-IS','VPN / IPsec','BGP','Multicast','MPLS / LDP','MPLS L3VPN / VRF','MPLS L2VPN / EVPN','QoS / Traffic Engineering','DNS / DHCP','Network Troubleshooting']),
 ('git','Git','История изменений, ветки и совместная работа.',[],['Основы Git','Ветки / Merge / Workflow']),
 ('linux','Linux','Система, ресурсы, сервисы и диагностика.',[],['Файлы и команды','Пользователи и права','Процессы и сигналы','Systemd / Boot','Ресурсы / proc','Диски / LVM / RAID','Текст и потоки','SSH / Firewall','Troubleshooting']),
 ('bash','Bash / Python','Скрипты, автоматизация и инструменты разработки.',['linux'],['Bash','Python','Сборка приложений']),
 ('web','Web / HTTP','HTTP, TLS, Nginx и балансировка.',['network'],['HTTP / TLS','Nginx / HAProxy','Микросервисы / HA / Cache']),
 ('docker','Docker','Образы, контейнеры, сети и хранение данных.',['linux','git'],['Архитектура контейнеров','Dockerfile / Images','Networks / Volumes / Registry','Docker Compose']),
 ('cicd','CI/CD','От коммита до поставки приложения.',['git','docker'],['Методология / Agile','GitLab CI','Jenkins','Continuous Delivery','Интеграционный проект']),
 ('terraform','Terraform','Инфраструктура как код и управление состоянием.',['linux','git'],['IaC / Providers','State / Modules']),
 ('ansible','Ansible','Автоматизация конфигурации серверов.',['linux','bash'],['Inventory / Playbook','Roles / Jinja2 / Vault']),
 ('kubernetes','Kubernetes','Кластер, workloads, сеть, хранилища и надёжность.',['docker','cicd','network'],['Архитектура / kubectl','Pod / Deployment / ConfigMap','Service / Ingress / CNI','PV / PVC / StatefulSet','Probes / HPA / Rollout','Helm','RBAC / NetworkPolicy','Troubleshooting','Проект Kubernetes']),
 ('monitoring','Monitoring','Метрики, дашборды и оповещения.',['linux'],['Prometheus / Exporters','Grafana / Alertmanager','SRE / SLI / SLO']),
 ('logging','Logging','Сбор логов и поиск причин ошибок.',['linux'],['ELK / OpenSearch','Loki / Collectors']),
 ('databases','Databases / Brokers','Эксплуатация баз данных, репликация и очереди.',['linux'],['PostgreSQL / SQL','NoSQL / Redis','Kafka / RabbitMQ']),
 ('cloud','Cloud / Virtualization','Виртуальные машины и облачная инфраструктура.',['network','linux'],['Virtualization','Yandex Cloud / VPC / IAM','S3 / Managed Services']),
 ('security','Security / DevSecOps','Секреты, безопасная поставка и GitOps.',['cicd'],['Vault / Secrets','DevSecOps','GitOps / Argo CD']),
 ('projects','Architecture / Projects','Контрольные точки, интеграция и итоговый проект.',['linux','network'],['Буферы и повторение','Infrastructure Architecture / HA','Итоговый проект'])
]
topics=[];subs=[]
for order,(id,title,description,prerequisites,names) in enumerate(spec):
 topics.append(dict(id=id,title=title,description=description,category='Network' if id=='network' else 'DevOps',prerequisites=prerequisites,order=order))
 for i,n in enumerate(names):subs.append(dict(id=f'{id}-{i}',topicId=id,title=n,order=i,prerequisites=[]))
for a,b in [('network-4','network-1'),('network-7','network-4'),('network-9','network-7'),('network-11','network-9'),('network-13','network-11'),('network-14','network-13'),('network-15','network-14')]: next(x for x in subs if x['id']==a)['prerequisites']=[b]
week_sub=['network-1','network-2','network-5','network-4','network-6','network-8','network-9','network-10','network-11','network-12','network-13','network-14','network-15','network-16','projects-0','git-0','git-1','linux-0','linux-1','linux-2','linux-3','linux-4','linux-5','linux-6','bash-0','linux-7','linux-8','projects-1','docker-0','docker-1','docker-2','docker-3','cicd-0','cicd-1','terraform-0','terraform-1','ansible-0','ansible-1','cicd-3','cicd-4','projects-0','kubernetes-0','kubernetes-1','kubernetes-2','kubernetes-3','kubernetes-4','kubernetes-5','kubernetes-6','kubernetes-7','kubernetes-8','monitoring-0','logging-0','databases-0','cloud-1','security-2','projects-2']
rules=[('network-15',r'l2vpn|evpn'),('network-14',r'l3vpn|\bvrf\b'),('network-13',r'mpls|\bldp\b'),('network-16',r'\bqos\b|traffic engineering'),('network-11',r'\bbgp\b'),('network-9',r'ospf|is-is'),('network-12',r'multicast|igmp|\bpim\b'),('network-10',r'ipsec|\bgre\b|\bvpn\b'),('network-7',r'статическ.*маршрут|static rout|routing table|route table|next-hop'),('network-6',r'\bstp\b|rstp|lacp'),('network-5',r'vlan|trunk|802.1q'),('network-4',r'ipv4|ipv6|subnet|маск[аи]|подсет'),('network-8',r'\bacl\b|\bnat\b|\bpat\b'),('network-18',r'wireshark|tcpdump|traceroute'),('network-17',r'\bdns\b|\bdhcp\b'),('network-3',r'\barp\b|icmp'),('network-2',r'ethernet|mac-'),('network-0',r'физическ|duplex|negotiation')]
tasks=[]
def add(title,sub,source,kind='Theory',date=None,week=None,description='',optional=False,refs=None,minutes=40):
 title=title.strip().lstrip('•').strip()
 tid='t-'+hashlib.sha1((source+'|'+str(week)+'|'+title).encode()).hexdigest()[:14]
 existing=next((x for x in tasks if x['id']==tid),None)
 if existing:return existing
 task=dict(id=tid,topicId=sub.rsplit('-',1)[0],subtopicId=sub,source=source,sources=[source],type=kind,title=title,description=description,scheduledDate=date,originalDate=date,week=week,estimatedMinutes=minutes,completed=False,completedAt=None,optional=optional,priority='high' if sub.startswith('network') else 'medium',notes='',custom=False,sourceRefs=refs or [],scheduleOrigin='Распределено внутри недели Word-плана' if week else 'Дополнительный материал')
 tasks.append(task);return task
for w in weeks:
 default=week_sub[w['week']-1]; items=[]
 for i,title in enumerate(w['theory']):items.append((title,'Video' if re.search(r'видео|ролик',title,re.I) else 'Theory',min(i,3)))
 for i,title in enumerate(w['practice']):items.append((title,'Project' if re.search(r'проект',title,re.I) else 'Lab' if re.search(r'собрать|настроить|поднять|развернуть|создать',title,re.I) else 'Practice',4+min(i,2)))
 if w['outcome']:items.append(('Контрольная точка: '+w['outcome'],'Review',6))
 for title,kind,day in items:
  sub=default
  if default.startswith('network'):
   sub=next((sid for sid,pat in rules if re.search(pat,title,re.I)),default)
  date=(datetime.date.fromisoformat(w['start_date'])+datetime.timedelta(days=day)).isoformat()
  t=add(title,sub,'Мой план',kind,date,w['week'],f"Неделя {w['week']}: {w['title']}\n"+'\n'.join(s['route'] for s in w['source_routes']),refs=[dict(file='sources/study-plan.docx',label=f"Word · неделя {w['week']}")],minutes=60 if kind in ['Lab','Project'] else 35)
  if 'LinkMeUp' in title:t['sources'].append('LinkMeUp')

# Optional extra sources are attached below by the reproducible adapters.
def classify(text,fallback='projects-1'):
 s=text.lower()
 for pat,sub in [(r'helm','kubernetes-5'),(r'kubernetes|kubectl|k8s|kubelet|kube-proxy','kubernetes-0'),(r'ansible','ansible-0'),(r'terraform','terraform-0'),(r'gitops|argo|flux','security-2'),(r'vault','security-0'),(r'jenkins','cicd-2'),(r'gitlab|pipeline|ci/cd|continuous|пайплайн','cicd-1'),(r'docker compose|compose','docker-3'),(r'dockerfile|образ','docker-1'),(r'docker|контейнер','docker-0'),(r'prometheus|promql|exporter','monitoring-0'),(r'grafana|alertmanager','monitoring-1'),(r'loki|fluent|filebeat','logging-1'),(r'логи|логирование|elk|elastic|kibana','logging-0'),(r'kafka|rabbit|брокер|очеред','databases-2'),(r'postgres|sql|баз[аы] данных|репликаци','databases-0'),(r'redis|mongodb|clickhouse|nosql','databases-1'),(r'облак|cloud|iaas|paas|saas|\bvpc\b|\bs3\b','cloud-1'),(r'виртуал','cloud-0'),(r'nginx|haproxy|балансир|микросервис','web-1'),(r'http|tls|ssl','web-0'),(r'git|markdown','git-0'),(r'python','bash-1'),(r'bash|скрипт','bash-0'),(r'сборк|maven|gradle|npm','bash-2'),(r'systemd|unit|загрузк','linux-3'),(r'процесс|сигнал|oom|cgroup|namespace','linux-2'),(r'disk|диск|inode|lvm|raid|fstab','linux-5'),(r'прав[ао]|sudo|пользовател|chmod','linux-1'),(r'\bssh\b|firewall|iptables','linux-7'),(r'grep|awk|sed|поток','linux-6'),(r'linux|линукс|команд|ресурс|load average','linux-0')]:
  if re.search(pat,s):return sub
 for sid,pat in rules:
  if re.search(pat,s):return sid
 if re.search(r'сет[ьи]|tcp|udp|osi|network',s):return 'network-1'
 return fallback

adapter=R/'scripts/source_adapters.py'
if adapter.exists():exec(compile(adapter.read_text(encoding='utf-8'),str(adapter),'exec'))
catalog=dict(version=3,startDate='2026-09-07',endDate='2028-04-01',topics=topics,subtopics=subs,tasks=tasks,weeks=weeks,sourceSummary=[])
summary=R/'data/source-summary.json'
if summary.exists():catalog['sourceSummary']=read(summary)
write(R/'data/curriculum.json',catalog)
(R/'dist/data').mkdir(exist_ok=True)
(R/'dist/data/curriculum.js').write_text('window.CURRICULUM = '+json.dumps(catalog,ensure_ascii=False)+';\n',encoding='utf-8')
print(f'{len(topics)} topics, {len(subs)} subtopics, {len(tasks)} tasks, {len(weeks)} weeks')
