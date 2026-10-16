"""Offline evidence runner. It never declares live equivalence from mocked tests."""
import argparse
import ast
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def inventory():
    violations=[]
    for path in (ROOT/'radar').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            if isinstance(node,ast.ImportFrom):
                forbidden='aisa' in (node.module or '').split('.') or any(v.name=='aisa' for v in node.names)
            elif isinstance(node,ast.Import):forbidden=any('aisa' in v.name.split('.') for v in node.names)
            else:continue
            if forbidden:violations.append(str(path.relative_to(ROOT)))
    return {'legacy_imports':violations,'legacy_module_exists':(ROOT/'radar/aisa.py').exists(),
            'status':'PASS' if not violations and not (ROOT/'radar/aisa.py').exists() else 'FAIL',
            'scope':'Static import scan only; does not certify live traffic or supplier provenance.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['inventory','contracts','no-aisa','report'])
    p.add_argument('--run-dir',type=Path,default=Path('state/acceptance/latest'))
    args=p.parse_args(argv)
    args.run_dir = args.run_dir.resolve()
    args.run_dir.mkdir(parents=True,exist_ok=True)
    if args.command=='inventory':
        data=inventory()
        (args.run_dir/'inventory.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
        print(json.dumps(data))
        return int(data['status']!='PASS')
    if args.command in ('contracts','no-aisa'):
        if not (ROOT/'tests').is_dir():
            print('Evidence collection requires a source checkout with tests.');return 2
        if __import__('importlib.util',fromlist=['find_spec']).find_spec('pytest') is None:
            print('Install development dependency pytest before collecting evidence.');return 2
        xml=args.run_dir/(args.command+'.xml')
        command=[sys.executable,'-E','-X','utf8','-m','pytest','-q',str(ROOT/'tests'),
                 '--basetemp',str(args.run_dir/'tmp'), '--junitxml',str(xml.resolve())]
        if args.command=='no-aisa':command+=['-k','zero_aisa']
        result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (args.run_dir/(args.command+'.log')).write_bytes(result.stdout)
        summary={'command':args.command,'exit_code':result.returncode,
                 'checked_at_utc':datetime.now(timezone.utc).isoformat(),'mode':'OFFLINE_MOCKS',
                 'live_equivalence':'NOT_RUN','stdout_log':args.command+'.log'}
        if xml.exists():
            suites=ET.parse(xml).getroot()
            summary['tests']=sum(int(s.get('tests',0)) for s in suites.iter('testsuite'))
            summary['failures']=sum(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites.iter('testsuite'))
        (args.run_dir/(args.command+'.json')).write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary));return result.returncode
    manifest=json.loads((ROOT/'docs/plans/remove-aisa-capabilities.json').read_text(encoding='utf-8'))
    lines=['# remove-aisa 验收进度','','完整替换验收：**BLOCKED，尚未完成真实服务验收**。','',
           '离线测试不能证明线上覆盖、模型质量、服务商独立性或真实账单。','']
    for file in ('inventory.json','contracts.json','no-aisa.json'):
        path=args.run_dir/file
        if path.exists():lines += [f'## {file}','','```json',path.read_text(encoding='utf-8'),'```','']
    lines+=['## 真实验收项','']
    for c in manifest['capabilities']:
        lines += [f"- {c['id']} {c['name']}：NOT_RUN，缺少线上对照/人工核验。"]
    lines+=['','未执行7天14轮观察、真实14天复盘、费用对账。不能标记全功能PASS。','']
    (args.run_dir/'acceptance.md').write_text('\n'.join(lines),encoding='utf-8')
    print((args.run_dir/'acceptance.md').resolve());return 0


if __name__=='__main__':raise SystemExit(main())
