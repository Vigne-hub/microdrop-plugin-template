import shutil
from argparse import ArgumentParser
import fnmatch
import re
import sys
from tempfile import mkdtemp
from pathlib import Path

import git

# Python 3.8 compatibility for importlib.resources
try:
    from importlib import resources as importlib_resources
except ImportError:
    import importlib_resources

CRE_PLUGIN_NAME = re.compile(r'^[A-Za-z_][\w_]+$')



def create_plugin(output_directory, overwrite=False, init_git=True):
    '''
    Parameters
    ----------
    output_directory : str
        Output directory path.  Directory name must be a valid Python module
        name.
    overwrite : bool, optional
        Overwrite existing output directory.

    Returns
    -------
    path_helpers.path
        Output directory path.

    Raises
    ------
    ValueError
        If `output_directory` name is not a valid Python module name.
    IOError
        If `output_directory` exists and `overwrite` is ``False``.
    '''
    output_directory = Path(output_directory).resolve()
    new_name = output_directory.name
    if not CRE_PLUGIN_NAME.match(new_name):
        raise ValueError(f'Invalid plugin name, "{new_name}".  Name must be valid Python module name.')

    # TODO Load ignore list from `.templateignore`
    ignore_list = ('*.pyc __init__.py create_plugin.py init_hooks.py rename.py'
                   '*bash.exe.stackdump'.split(' '))

    def collect_package_resource_files(root=Path('.')):
        files = []
        if root.is_dir():
            for p_i in root.iterdir():
                if p_i.is_dir():
                    files.extend(collect_package_resource_files(p_i))
                else:
                    if p_i.name not in ignore_list:
                        files.append(p_i)
        return files

    if output_directory.is_dir() and not overwrite:
        raise IOError('Output directory already exists.  Use `overwrite=True` to overwrite.')

    working_directory = Path(mkdtemp(prefix='create_plugin-'))

    try:
        template_dir = Path(importlib_resources.files('microdrop_plugin_template').name)
        template_files = collect_package_resource_files(template_dir)
        for f in template_files:
            target_filename = working_directory / f.relative_to(template_dir)
            target_filename.parent.mkdir(parents=True, exist_ok=True)
            target_filename.write_bytes(f.read_bytes())

        source_file = working_directory / '__init__.py.template'
        target_file = working_directory / '__init__.py'
        if source_file.exists():
            source_file.rename(target_file)

        def rename_contents(directory, old_string, new_string, exclude=None):
            exclude = exclude or []
            for path in directory.rglob('*.py'):
                if path.name in exclude:
                    continue
                content = path.read_text()
                content = content.replace(old_string, new_string)
                path.write_text(content)

        rename_contents(working_directory, 'microdrop-plugin-template', new_name.replace('_', '-'),
                        exclude=['on_plugin_install.py'])

        if init_git:
            try:
                repo = git.Repo.init(working_directory)
                repo.git.add(A=True)
                repo.index.commit('Initial commit')
                tag = 'v0.1'
                repo.create_tag(tag, message='Initial release')
                print(f'Initialized plugin as git repo (tag={tag})')
            except Exception as exception:
                print('Error initializing git repo.', file=sys.stderr)
                print(exception, file=sys.stderr)
            else:
                version_initialized = True

        if not version_initialized:
            version_path = working_directory / 'RELEASE-VERSION'
            version_path.write_text('0.1')
            print('Wrote version to file: RELEASE-VERSION')

        if output_directory.exists():
            for item in output_directory.glob('*'):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        working_directory.rename(output_directory)

        return output_directory
    except Exception as exception:
        print(exception)
        raise
    finally:
        if working_directory.exists():
            shutil.rmtree(working_directory)


def parse_args(args=None):
    '''Parses arguments, returns ``(options, args)``.'''
    from mpm.bin import LOG_PARSER

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Create a new Microdrop plugin',
                            parents=[LOG_PARSER])
    parser.add_argument('-f', '--force-overwrite', action='store_true',
                        help='Force overwrite of existing directory')
    parser.add_argument('--no-git', action='store_true',
                        help='Disable git repo initialization')
    parser.add_argument('output_directory', type=Path, help='Output '
                        'directory.  Directory name must be a valid Python '
                        'module.')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    try:
        output_directory = create_plugin(args.output_directory,
                                         overwrite=args.force_overwrite,
                                         init_git=not args.no_git)
    except IOError as exception:
        print('Output directory exists.  Use `-f` to overwrite', file=sys.stderr)
        raise SystemExit(-5)
    except ValueError as exception:
        print(exception, file=sys.stderr)
        raise SystemExit(-10)
    else:
        print('Wrote plugin to: {}'.format(output_directory))