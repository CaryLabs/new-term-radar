"""Explicit offline migration. Never overwrite the source or copy gateway secrets."""
import argparse
import copy
import json
from pathlib import Path

from .config import DEFAULTS


def migrate(raw):
    if not isinstance(raw, dict):raise ValueError('Expected configuration object')
    result = copy.deepcopy(DEFAULTS)
    for k,v in raw.items():
        if k in result and k not in ('credentials','services','providers','limits','schema_version'):
            result[k] = {**result[k], **v} if isinstance(result[k],dict) and isinstance(v,dict) else v
    for group in ('credentials','services'):
        values=raw.get(group,{})
        if not isinstance(values,dict):raise ValueError('Invalid config group')
        for key,value in values.items():
            if key in result[group]: result[group][key]=value
    # Existing gateway model names are not automatically accepted by another API.
    for task in ('judge','usecases','asks','pains','tutorials'):
        result[task]['model']='deepseek-flash'
    result['limits']['network_enabled']=False
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=Path('config.json'))
    p.add_argument('--out',type=Path,default=Path('state/remove-aisa/config.json'))
    p.add_argument('--dry-run',action='store_true')
    args=p.parse_args(argv)
    try:
        result=migrate(json.loads(args.input.read_text(encoding='utf-8-sig')))
        if args.dry_run:
            print('Migration valid; no files written; secrets not displayed; network remains disabled.')
            return 0
        if args.out.exists() or args.out.resolve()==args.input.resolve():
            raise ValueError('Output must be a new file, distinct from source')
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('x',encoding='utf-8') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2)
        print(args.out.resolve())
        return 0
    except (OSError,ValueError,TypeError):
        print('Migration failed: invalid input or output already exists; source unchanged.')
        return 2


if __name__=='__main__':raise SystemExit(main())
