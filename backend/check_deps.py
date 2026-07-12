missing = []
deps = [
    'django', 'rest_framework', 'corsheaders', 'langchain', 'chromadb'
]
for d in deps:
    try:
        __import__(d)
    except Exception:
        missing.append(d)

if missing:
    print('Missing packages:', missing)
    print('Run: python install_deps.py')
else:
    print('All required packages import successfully')
