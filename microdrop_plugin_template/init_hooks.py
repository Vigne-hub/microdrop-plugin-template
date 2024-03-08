from argparse import ArgumentParser
import datetime as dt
import logging
import sys
from pathlib import Path
import importlib.resources as pkg_resources

logger = logging.getLogger(__name__)


def init_hooks(plugin_directory, overwrite=False):
    '''
    Copy default hook scripts to specified plugin.

    Prompt to overwrite a hook script if it already exists (unless
    ``overwrite==True``).

    Parameters
    ----------
    plugin_directory : str
        Microdrop plugin directory
    overwrite : bool
        If `True`, overwrite existing file with same name as output file.
    '''
    plugin_directory = Path(plugin_directory)

    # Hook files to copy from plugin template.
    hook_paths = ('hooks/Windows/on_plugin_install.bat',
                  'hooks/Linux/on_plugin_install.sh',
                  'on_plugin_install.py')

    with pkg_resources.path('microdrop_plugin_template', '') as package_path:
        template_hook_paths = [package_path / p for p in hook_paths]

    plugin_hook_paths = [plugin_directory / p for p in hook_paths]

    for plugin_path_i, template_path_i in zip(plugin_hook_paths, template_hook_paths):
        if plugin_path_i.read_text() == template_path_i.read_text():
            logger.debug('File contents match: "%s" and "%s"', plugin_path_i, template_path_i)
            continue
        if plugin_path_i.is_file():
            if not overwrite:
                response = None
                skip_file = False
                while response is None:
                    print(f'File exists: {plugin_path_i}. [(s)kip]/s(k)ip all/(b)ackup/(o)verwrite/overwrite (a)ll?'),
                    response = input() or 's'
                    if response in ('s', 'skip'):
                        logger.debug('Skipping: %s', plugin_path_i)
                        skip_file = True
                        break
                    elif response in ('k', 'skip all'):
                        logger.debug('Skipping all remaining files')
                        return
                    elif response in ('b', 'backup'):
                        backup_path_i = plugin_path_i.with_suffix(
                            plugin_path_i.suffix + '.' + dt.datetime.now().strftime('%Y-%m-%dT%Hh%Mm%S'))
                        logger.debug('Wrote backup to: %s', backup_path_i)
                        backup_path_i.write_text(plugin_path_i.read_text())
                        break
                    elif response in ('o', 'overwrite'):
                        logger.debug('Overwriting: %s', plugin_path_i)
                        break
                    elif response in ('a', 'overwrite all'):
                        logger.debug('Overwriting: %s', plugin_path_i)
                        overwrite = True
                        break
                    else:
                        response = None
                if skip_file:
                    continue
            else:
                logger.debug('Overwriting: %s', plugin_path_i)
        plugin_path_i.write_text(template_path_i.read_text())


def parse_args(args=None):
    '''Parses arguments, returns ``(options, args)``.'''
    from mpm.bin import LOG_PARSER

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='Initialize plugin directory with '
                                        'latest hook scripts from the '
                                        '`microdrop-plugin-template` package.',
                            parents=[LOG_PARSER])
    parser.add_argument('-f', '--force-overwrite', action='store_true',
                        help='Force overwrite of existing files')
    parser.add_argument('plugin_directory', type=Path, default=Path('.'),
                        help='Plugin directory')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    init_hooks(args.plugin_directory, overwrite=args.force_overwrite)