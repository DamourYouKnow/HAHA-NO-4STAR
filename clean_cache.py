from itertools import chain
from pathlib import Path

from idol_images import member_img_path
from logs import log_path


def clean():
    for _path in chain(log_path.iterdir(), member_img_path.iterdir()):
        path = Path(_path)
        if not path.name.endswith('.py') and not path.is_dir():
            path.unlink()


if __name__ == '__main__':
    clean()
