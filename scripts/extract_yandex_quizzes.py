"""Create a safe, compact quiz index from the user's archived course export."""
import json, pathlib
source = pathlib.Path(r'C:\Users\рс\AppData\Local\Temp\opstrack-yandex\yandex-complete.json')
target = pathlib.Path(__file__).resolve().parents[1] / 'data' / 'yandex-quizzes.json'
data = json.loads(source.read_text(encoding='utf-8'))
rows = []
for module in data['modules']:
    for lesson in module['lessons']:
        for quiz in lesson.get('quizzes', []):
            question = ' '.join(quiz.get('question', '').split())
            rows.append({
                'id': quiz['id'], 'lessonId': lesson['id'],
                'question': question[:1500],
                'format': quiz.get('type', '').replace('theory-viewer__block', '').strip(),
            })
target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(rows)} quiz prompts -> {target}')
