"""Prepare the installed ChatGPT runtime cache without copying EFS metadata.

Requires Python 3. Default: read-only check. --repair: close ChatGPT first.
Only targets the current version's cua_node cache, never app or chat files.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

KEY_FILES = ['manifest.json', 'bin/node.exe', 'bin/node_repl.exe']


def digest(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def runtime_key(source):
    result = hashlib.sha256()
    for name in KEY_FILES:
        result.update(name.encode() + b'\0' + digest(source / name).encode() + b'\0')
    return result.hexdigest()[:16]


def complete(source, target):
    try:
        return (all(digest(source / n) == digest(target / n) for n in KEY_FILES)
                and (target / 'bin/node_modules').is_dir()
                and all((target / f.relative_to(source)).stat().st_size == f.stat().st_size
                        for f in source.rglob('*') if f.is_file()))
    except OSError:
        return False


def installed():
    command = """
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$p = Get-AppxPackage -Name OpenAI.Codex
if (-not $p) { throw 'OpenAI.Codex is not registered for this user.' }
@{location=$p.InstallLocation;running=[bool](Get-Process -Name ChatGPT -ErrorAction SilentlyContinue)} | ConvertTo-Json -Compress
"""
    result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', command],
                            capture_output=True, encoding='utf-8', check=True)
    return json.loads(result.stdout.lstrip('\ufeff'))


def prepare(source, cache):
    key = runtime_key(source)
    target = cache / key
    if complete(source, target):
        print('Cache is already complete. No changes needed.')
        return
    cache.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='repair-staging-', dir=cache))
    for number, file in enumerate((f for f in source.rglob('*') if f.is_file()), 1):
        dest = stage / file.relative_to(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with file.open('rb') as reader, dest.open('wb') as writer:
            shutil.copyfileobj(reader, writer)
        if number % 500 == 0:
            print(f'Prepared {number} files...', flush=True)
    if runtime_key(source) != key or not complete(source, stage):
        raise RuntimeError(f'Validation failed; existing cache unchanged. Diagnostic copy: {stage}')
    if target.exists():
        backup = target.with_name(key + '.backup-' + uuid.uuid4().hex[:8])
        target.rename(backup)
        print('Previous cache preserved:', backup)
    stage.rename(target)
    print('Runtime cache prepared:', target)
    print('Now launch ChatGPT from the ORIGINAL Applications entry.')


def main():
    state = installed()
    source = Path(state['location']) / 'app/resources/cua_node'
    cache = Path(os.environ['LOCALAPPDATA']) / 'OpenAI/Codex/runtimes/cua_node'
    key = runtime_key(source)
    print('Installed package:', state['location'])
    print('Current runtime:', key)
    if '--repair' not in sys.argv:
        print('Cache complete:', complete(source, cache / key))
        print('CHECK ONLY: no files modified.')
        return
    if state['running']:
        raise RuntimeError('Fully quit ChatGPT first. This tool will not stop it for you.')
    prepare(source, cache)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('STOP:', error, file=sys.stderr)
        sys.exit(1)
