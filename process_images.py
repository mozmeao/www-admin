#!/usr/bin/env python

import hashlib
import re
from itertools import chain
from pathlib import Path
from shutil import rmtree, copy


IMAGES_PATH = Path('static/img')
IMAGES_HASHED = Path('tmp_static/img')
CARDS_PATH = Path('content')
# Default chunk size from Django
CHUNK_SIZE = 64 * 2 ** 10


def clean_dirs():
    rmtree(str(IMAGES_HASHED), ignore_errors=True)


def get_all_images():
    images = IMAGES_PATH.glob('**/*.jpg')
    images = chain(images, IMAGES_PATH.glob('**/*.png'))
    return images


def get_hashed_filename(file_obj, md5hash):
    shorthash = md5hash[:12]
    name = file_obj.stem
    ext = file_obj.suffix
    file_obj = IMAGES_HASHED / file_obj.relative_to(IMAGES_PATH)
    return file_obj.with_name('%s.%s%s' % (name, shorthash, ext))


def hash_filenames(files):
    files_changed = []
    for fobj in files:
        hasher = hashlib.md5()
        with fobj.open('rb') as fh:
            while True:
                chunk = fh.read(CHUNK_SIZE)
                if not chunk:
                    break

                hasher.update(chunk)

        md5hash = hasher.hexdigest()
        hashed_fobj = get_hashed_filename(fobj, md5hash)
        hashed_fobj.parent.mkdir(parents=True, exist_ok=True)
        files_changed.append((fobj, hashed_fobj))

    return files_changed


def copy_files(files_changed):
    for forig, fhashed in files_changed:
        print('Copying %s to %s' % (forig, fhashed))
        copy(forig, fhashed)


def fix_data_files(files_changed):
    cards = CARDS_PATH.glob('**/*.md')
    for card in cards:
        lines = []
        print('Updating %s' % card)
        with card.open(encoding='utf-8') as fh:
            for line in fh:
                if line.startswith('image:'):
                    for forig, fhashed in files_changed:
                        orig_path = str(forig.relative_to(IMAGES_PATH))
                        hashed_path = str(fhashed.relative_to(IMAGES_HASHED))
                        if orig_path in line:
                            line = line.replace(orig_path, hashed_path)

                lines.append(line)

        with card.open('w', encoding='utf-8') as fh:
            fh.writelines(lines)


if __name__ == '__main__':
    clean_dirs()
    images = get_all_images()
    files_changed = hash_filenames(images)
    copy_files(files_changed)
    fix_data_files(files_changed)
