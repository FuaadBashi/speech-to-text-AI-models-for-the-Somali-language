#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

STEPS = (
    'setup_and_install.py',
    'build_verification_clip.py',
    'training_imports_and_config.py',
    'training_configuration.py',
    'training_run.py',
    'evaluation_setup.py',
    'evaluation_comprehensive.py',
)


def run_pipeline(script_dir=None, steps=STEPS):
    script_dir = Path(script_dir or Path(__file__).parent).resolve()
    scripts = [script_dir / name for name in steps]
    for script in scripts:
        if not script.is_file():
            raise FileNotFoundError(f'Pipeline step not found: {script}')
    namespace = {'__name__': '__main__'}
    original_dir = Path.cwd()
    try:
        os.chdir(script_dir)
        for index, script in enumerate(scripts, 1):
            print(f'[{index}/{len(scripts)}] {script.name}', flush=True)
            namespace['__file__'] = str(script)
            exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), namespace)
    finally:
        os.chdir(original_dir)
    return namespace


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run the Somali ASR notebook workflow')
    parser.add_argument('--list-steps', action='store_true', help='Show steps without training or installing packages')
    args = parser.parse_args(argv)
    if args.list_steps:
        print('\n'.join(STEPS))
        return
    run_pipeline()


if __name__ == '__main__':
    main()
