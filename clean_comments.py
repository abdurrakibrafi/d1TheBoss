import re, glob

for filepath in glob.glob('**/*.py', recursive=True):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    cleaned = re.sub(r'(?m)^\s*#.*\n?', '', content)
    cleaned = re.sub(r'\s*#[^\"\']*\$', '', cleaned, flags=re.MULTILINE)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(cleaned)
    print(f'Cleaned: {filepath}')
