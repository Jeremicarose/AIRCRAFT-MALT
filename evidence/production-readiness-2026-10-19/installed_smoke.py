import json, os, socket, subprocess, time, urllib.request
from pathlib import Path
root=Path.cwd(); out=root/'artifacts/readiness-2026-10-19'
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
env={**os.environ,'MLAT_ENV_FILE':'/dev/null','DATABASE_PATH':str(out/'installed-api.db'),'API_HOST':'127.0.0.1','API_PORT':str(port),'ENABLE_ADMIN_API':'false','ENABLE_BACKGROUND_BROADCASTER':'false','RATE_LIMIT_ENABLED':'true','DEMO_MODE':'false','STRICT_PRODUCTION_MODE':'false'}
env.pop('PYTHONPATH',None)
env['PATH']=str(out/'venv/bin')+':'+os.environ['PATH']
with (out/'installed-api.log').open('x') as log:
    process=subprocess.Popen([str(out/'venv/bin/mlat-api')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            if process.poll() is not None: raise RuntimeError('installed API exited')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/healthz',timeout=1) as r:
                    assert r.status==200
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/diagnostics/bundle',timeout=1) as r:
                    bundle=json.load(r)
                assert bundle['source_context']['data_provenance']=='UNKNOWN'
                print(json.dumps({'status':'PASS','installed_entrypoint':'mlat-api','source_pythonpath':False,'liveness':200,'diagnostics':200,'provenance':'UNKNOWN'}))
                break
            except OSError: time.sleep(.2)
        else: raise RuntimeError('installed API did not start within 30 seconds')
    finally:
        process.terminate()
        try: process.wait(timeout=15)
        except subprocess.TimeoutExpired: process.kill();process.wait();raise
        print(json.dumps({'shutdown_exit_code':process.returncode}))
