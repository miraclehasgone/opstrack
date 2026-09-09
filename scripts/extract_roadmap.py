import sys,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'.tools'))
import pymupdf
sys.stdout.reconfigure(encoding='utf-8')
root=pathlib.Path(__file__).resolve().parents[1]
doc=pymupdf.open(r'C:\Users\рс\Downloads\Roadmap Просто Devops.pdf')
pages=[]
for i,p in enumerate(doc):
    pages.append({'page':i+1,'text':p.get_text(),'links':[{'uri':l.get('uri'),'page':l.get('page')} for l in p.get_links()]})
(root/'data/roadmap-extracted.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
(root/'docs/roadmap-text.txt').write_text('\n\n'.join(f"PAGE {p['page']}\n{p['text']}" for p in pages),encoding='utf-8')
print('Pages:',len(pages),'Links:',sum(len(p['links']) for p in pages))
for p in pages: print(p['page'],p['text'][:170].replace('\n',' | '))
