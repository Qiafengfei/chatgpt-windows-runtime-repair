import importlib.util
import pathlib
import tempfile

script = pathlib.Path(__file__).parents[1] / 'repair_runtime.py'
spec = importlib.util.spec_from_file_location('repair_runtime', script)
repair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repair)
with tempfile.TemporaryDirectory(dir=pathlib.Path(__file__).parent) as tmp:
    root = pathlib.Path(tmp)
    source = root / 'source'
    for name in repair.KEY_FILES + ['bin/node_modules/example/index.js']:
        file = source / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(name.encode())
    cache = root / 'cache'
    target = cache / repair.runtime_key(source)
    assert not repair.complete(source, target)
    repair.prepare(source, cache)
    assert repair.complete(source, target)
    (target / 'bin/node.exe').write_bytes(b'broken')
    assert not repair.complete(source, target)
    repair.prepare(source, cache)
    assert repair.complete(source, target)
    backups = list(cache.glob('*.backup-*'))
    assert len(backups) == 1
    assert (backups[0] / 'bin/node.exe').read_bytes() == b'broken'
print('PASS: cache identity, stream copy, corruption detection, backup preservation')
