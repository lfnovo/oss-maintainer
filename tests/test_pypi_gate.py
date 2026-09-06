"""Execute the shipped shell recipes against an offline pure-Python wheel fixture.

A fake uv only builds/installs the fixture; directory and Python isolation are performed
by the real documented shell command and a real fresh virtual environment.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib
import venv
import zipfile

import pytest

from tests.conftest import PLUGIN

REFERENCE = PLUGIN / 'skills/release/references/archetypes/pypi-library.md'

GIT_IDENTITY = {'GIT_AUTHOR_NAME': 'test', 'GIT_AUTHOR_EMAIL': 'test@example.invalid',
                'GIT_COMMITTER_NAME': 'test', 'GIT_COMMITTER_EMAIL': 'test@example.invalid'}


def git_commit_all(repo: Path) -> None:
    env = dict(os.environ, **GIT_IDENTITY)
    subprocess.run(['git', 'init', '-q'], cwd=repo, check=True, env=env)
    subprocess.run(['git', 'add', '-A'], cwd=repo, check=True, env=env)
    subprocess.run(['git', 'commit', '-q', '-m', 'candidate'], cwd=repo, check=True, env=env)


@pytest.mark.parametrize('packaged', [True, False])
@pytest.mark.parametrize('recipe', ['wheel', 'registry'])
def test_clean_room_recipe_cannot_import_source(tmp_path, packaged, recipe):
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    (checkout / 'example_lib.py').write_text('value = "source-only"\n')
    git_commit_all(checkout)
    # An untracked file in the working tree must never reach the build input.
    (checkout / 'UNTRACKED.md').write_text('local only\n')
    wheel = tmp_path / 'example_lib-1.0.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr('example_lib-1.0.0.dist-info/METADATA', 'Metadata-Version: 2.1\nName: example-lib\nVersion: 1.0.0\n')
        archive.writestr('example_lib-1.0.0.dist-info/WHEEL', 'Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n')
        if packaged:
            archive.writestr('example_lib.py', 'value = "installed-wheel"\n')
    env_dir = tmp_path / 'venv'
    venv.EnvBuilder(with_pip=False, symlinks=True).create(env_dir)
    python = env_dir / 'bin/python'
    site = subprocess.check_output([str(python), '-I', '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], text=True).strip()
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(site)
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    uv = bin_dir / 'uv'
    uv.write_text(f'#!{sys.executable}\n' + '''import os, pathlib, shutil, sys
args = sys.argv[1:]
if args == ['build']:
    here = pathlib.Path.cwd().resolve()
    assert here != pathlib.Path(os.environ['FIXTURE_CHECKOUT']).resolve(), 'build ran in the working tree'
    assert (here / 'example_lib.py').is_file(), 'build input is not the candidate commit'
    assert not (here / 'UNTRACKED.md').exists(), 'untracked file leaked into the build input'
    pathlib.Path('dist').mkdir()
    shutil.copy(os.environ['FIXTURE_WHEEL'], 'dist')
else:
    dependency = args[args.index('--with') + 1]
    if dependency.endswith('.whl'):
        assert pathlib.Path(dependency).is_absolute() and pathlib.Path(dependency).is_file()
    assert pathlib.Path.cwd() != pathlib.Path(os.environ['FIXTURE_CHECKOUT'])
    assert '--isolated' in args and '--no-project' in args
    rest = args[args.index('python') + 1:]
    os.execv(os.environ['FIXTURE_PYTHON'], [os.environ['FIXTURE_PYTHON'], *rest])
''')
    uv.chmod(0o755)
    text = REFERENCE.read_text()
    blocks = re.findall(r'```bash\n(.*?)\n```', text, re.S)
    command = blocks[0 if recipe == 'wheel' else 1].replace('<package>==<version>', 'example-lib==1.0.0').replace('<module>', 'example_lib')
    env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}', PYTHONPATH=str(checkout),
               FIXTURE_WHEEL=str(wheel), FIXTURE_PYTHON=str(python), FIXTURE_CHECKOUT=str(checkout))
    proc = subprocess.run(['bash', '-c', command], cwd=checkout, env=env, capture_output=True, text=True)
    assert (proc.returncode == 0) is packaged, proc.stderr
    if recipe == 'wheel':
        assert 'excluded from the build (not in HEAD): ?? UNTRACKED.md' in proc.stdout
        assert (checkout / 'dist' / wheel.name).is_file(), 'artifacts are copied back for digests'
        worktrees = subprocess.check_output(['git', 'worktree', 'list', '--porcelain'], cwd=checkout, text=True)
        assert worktrees.count('worktree ') == 1, 'temporary worktree was not removed'
    if packaged:
        assert str(Path(site) / 'example_lib.py') in proc.stdout
    else:
        assert 'ModuleNotFoundError' in proc.stderr


def test_readme_example_uses_the_tested_recipe():
    text = (PLUGIN.parents[1] / 'README.md').read_text()
    profile_block = next(block for block in re.findall(r'```toml\n(.*?)\n```', text, re.S) if '[artifacts.pypi]' in block)
    profile = tomllib.loads(profile_block)
    recipe = re.findall(r'```bash\n(.*?)\n```', REFERENCE.read_text(), re.S)[0]
    assert profile['artifacts']['pypi']['gate'].strip() == recipe


def test_unconfigured_template_gate_is_explicitly_unresolved():
    path = PLUGIN / 'skills/init/templates/profile.pypi-library.toml'
    assert tomllib.loads(path.read_text())['artifacts']['pypi']['gate'].startswith('TODO')
