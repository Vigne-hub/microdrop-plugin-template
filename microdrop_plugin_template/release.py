import itertools
import os
import sys
from pathlib import Path
import tarfile
import yaml

from microdrop_utility import Version

package_name = 'microdrop_plugin_template'
plugin_name = 'wheelerlab.microdrop_plugin_template'

package_dir = Path(__file__).resolve().parent

if __name__ == '__main__':
    current_dir = Path(os.getcwd())
    os.chdir(package_dir)

    try:
        # create a version string based on the git revision/branch
        version = str(Version.from_git_repository())

        # Create the tar.gz plugin archive
        tar_path = current_dir / f"{package_name}-{version}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            # write the 'properties.yml' file
            properties = {'plugin_name': plugin_name, 'package_name': package_name, 'version': version}

            properties_path = package_dir / 'properties.yml'
            with properties_path.open('w') as f:
                yaml.dump(properties, f)
                print(f'Wrote: {properties_path}')

            # Using pathlib for iterating and adding files to tarfile
            here = Path('.')
            for path_i in itertools.chain(here.glob('*.py'),
                                          [Path('properties.yml'), Path('hooks'), Path('requirements.txt')]):
                if path_i.exists():
                    tar.add(path_i.as_posix(), arcname=path_i.relative_to(here))
            print(f'Wrote: {tar_path.relative_to(current_dir)}')
    finally:
        os.chdir(current_dir)