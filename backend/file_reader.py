"""Read text files from an untrusted ZIP without extracting it to disk."""
from __future__ import annotations
import io
import zipfile
from pathlib import PurePosixPath

MAX_UPLOAD = 6 * 1024 * 1024
MAX_FILES = 65
MAX_SINGLE_FILE = 220_000
MAX_TOTAL_TEXT = 650_000
ALLOWED_EXT = {'.py','.java','.md','.txt','.json','.yml','.yaml','.toml','.xml','.properties','.sh','.ps1','.sql','.js','.jsx','.ts','.tsx','.html','.css','.env','.gitignore'}
ALLOWED_NAMES = {'Dockerfile','Makefile','.gitignore','.env.example'}
BLOCK_PARTS = {'node_modules','.git','.venv','venv','__pycache__','dist','build','.next','coverage'}


def read_zip(data: bytes) -> dict[str,str]:
    if len(data) > MAX_UPLOAD:
        raise ValueError('ZIP exceeds the 6 MB upload limit.')
    files: dict[str,str] = {}
    total = 0
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
        with z:
            entries = [i for i in z.infolist() if not i.is_dir()]
            if len(entries) > 500:
                raise ValueError('Too many entries in the ZIP.')
            for item in entries:
                name = item.filename.replace('\\','/')
                p = PurePosixPath(name)
                if name.startswith('/') or '..' in p.parts or any(x in BLOCK_PARTS for x in p.parts):
                    continue
                if p.suffix.lower() not in ALLOWED_EXT and p.name not in ALLOWED_NAMES:
                    continue
                if item.file_size > MAX_SINGLE_FILE or item.flag_bits & 0x1:
                    continue
                if len(files) >= MAX_FILES:
                    break
                with z.open(item) as f:
                    content = f.read(MAX_SINGLE_FILE + 1)
                if len(content) > MAX_SINGLE_FILE:
                    continue
                decoded = content.decode('utf-8',errors='replace')
                if decoded.count('\ufffd') > 30:
                    continue
                total += len(content)
                if total > MAX_TOTAL_TEXT:
                    break
                # Do not ship potential secrets or entire .env files to an LLM
                if p.name == '.env':
                    continue
                files[name] = decoded
    except (zipfile.BadZipFile,zipfile.LargeZipFile) as e:
        raise ValueError('Please upload a valid ZIP archive.') from e
    if not files:
        raise ValueError('No supported readable project files were found.')
    return files


def prepare_context(files: dict[str,str], specification: str) -> str:
    """Bound context shared across agents to limit API cost."""
    out = ['SPECIFICATION / CTKS / EVALUATION CRITERIA:\n'+specification[:16000]]
    budget = 65000
    for name, value in files.items():
        chunk = f'\n--- FILE {name} ---\n{value[:10000]}\n--- END FILE ---\n'
        if len(chunk) > budget:
            chunk = chunk[:budget]
        out.append(chunk)
        budget -= len(chunk)
        if budget <= 0:
            break
    return '\n'.join(out)
