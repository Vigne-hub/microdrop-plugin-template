from pathlib import Path
from microdrop_plugin_template import install_requirements


if __name__ == '__main__':
    plugin_root = Path(__file__).parent.absolute()
    install_requirements(plugin_root)
