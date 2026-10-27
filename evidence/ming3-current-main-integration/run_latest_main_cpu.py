from pathlib import Path
import os, json, subprocess, datetime, sys
root = Path(__file__).resolve().parent
manifest = json.loads((root / 'latest-main-integration-cpu-launch.json').read_text())
env = os.environ.copy()
env.update(manifest['env_overrides'])
with (root / 'latest-main-integration-cpu.log').open('w') as log:
    result = subprocess.run(manifest['command'], cwd=root / 'latest-main-integration', env=env, stdout=log, stderr=subprocess.STDOUT)
receipt = {'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exit_code': result.returncode, 'base': manifest['base'], 'head': manifest['head'], 'tree': manifest['tree'], 'command': manifest['command'], 'log': str(root / 'latest-main-integration-cpu.log')}
(root / 'latest-main-integration-cpu-result.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
sys.exit(result.returncode)
