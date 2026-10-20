"""Extend the unchanged container smoke check with the new guide route and assets."""
import html
import json
from pathlib import Path
import re
import sys
import urllib.request

sys.path.insert(0, str(Path.cwd() / 'tools'))
import check_container_runtime as smoke

original_wait = smoke.wait_http
extra = {}

def wait_with_guide(url, expected_service=None):
    result = original_wait(url, expected_service)
    if expected_service == 'receiver-registry-operations':
        base = url.removesuffix('/healthz')
        with urllib.request.urlopen(base + '/app/guide', timeout=15) as response:
            document = response.read().decode('utf-8')
        assert re.search(r'<h1[^>]*>Explorer missions</h1>', document)
        assert '300' in document and 'Pause missions' in document
        assets = set(re.findall(r'(?:src|href)="(/_next/static/[^\"]+)"', document))
        assert assets
        for asset in assets:
            with urllib.request.urlopen(base + html.unescape(asset), timeout=15) as response:
                assert response.status == 200
        extra.update(guide_server_render=True, guide_static_assets=len(assets))
    return result

smoke.wait_http = wait_with_guide
status = smoke.main()
output = Path(sys.argv[sys.argv.index('--output') + 1])
report = json.loads(output.read_text())
report['checks'].update(extra)
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'guide_checks': extra}))
raise SystemExit(status)
