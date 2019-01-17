#!/usr/bin/env python

import hashlib
import json
import sys
from pathlib import Path
from shutil import rmtree, copy

from markdown import markdown
from ruamel.yaml import YAML


yaml = YAML()
OUTPUT_PATH = Path('output')
IMAGES_HASHED = OUTPUT_PATH / 'static/img'
CARDS_PATH = Path('content')
CARDS_POST_PATH = OUTPUT_PATH / 'content'
# Default chunk size from Django
CHUNK_SIZE = 64 * 2 ** 10


def parse_md_front_matter(lines):
    """Return the YAML and MD sections.

    :param: lines iterator
    :return: str YAML, str Markdown
    """
    # fm_count: 0: init, 1: in YAML, 2: in Markdown
    fm_count = 0
    yaml_lines = []
    md_lines = []
    for line in lines:
        # first line we care about is FM start
        if fm_count < 2 and line.strip() == '---':
            fm_count += 1
            continue

        if fm_count == 1:
            yaml_lines.append(line)

        if fm_count == 2:
            md_lines.append(line)

    if fm_count < 2:
        raise ValueError('Front Matter not found.')

    return ''.join(yaml_lines), ''.join(md_lines)


def parse_md_file(file_obj):
    """Return the all data for file_obj."""
    with file_obj.open(encoding='utf8') as fh:
        yamltext, mdtext = parse_md_front_matter(fh)

    data = yaml.load(yamltext)
    if mdtext.strip():
        data['html_content'] = markdown(mdtext)

    return data


def clean_dirs():
    rmtree(str(OUTPUT_PATH), ignore_errors=True)


def get_file_hash(file_obj):
    hasher = hashlib.md5()
    with file_obj.open('rb') as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break

            hasher.update(chunk)

    return hasher.hexdigest()


def get_hashed_filename(file_obj):
    shorthash = get_file_hash(file_obj)[:12]
    name = file_obj.stem
    ext = file_obj.suffix
    file_obj = IMAGES_HASHED / file_obj.relative_to(CARDS_PATH)
    return file_obj.with_name('%s.%s%s' % (name, shorthash, ext))


def get_highres_filename(file_obj):
    name = file_obj.stem
    ext = file_obj.suffix
    return file_obj.with_name('%s-high-res%s' % (name, ext))


def process_image_file(fobj):
    hashed_fobj = get_hashed_filename(fobj)
    hashed_fobj.parent.mkdir(parents=True, exist_ok=True)
    print('Copying %s to %s' % (fobj, hashed_fobj))
    copy(fobj, hashed_fobj)
    return hashed_fobj


def process_card_images(card, data):
    if 'image' in data:
        image_path = card.parent / data['image']
        try:
            hashed_img = process_image_file(image_path)
        except IOError:
            raise RuntimeError('Image referenced but not found: %s' % image_path)

        data['image'] = str(hashed_img.relative_to(IMAGES_HASHED))
        if data.get('include_highres_image', False):
            highres_path = get_highres_filename(image_path)
            try:
                hashed_highres_img = process_image_file(highres_path)
            except IOError:
                raise RuntimeError('Image referenced but not found: %s' % highres_path)

            data['highres_image'] = str(hashed_highres_img.relative_to(IMAGES_HASHED))
            del data['include_highres_image']


def get_json_card(card_obj):
    base_path = card_obj.parents[1]
    json_card = card_obj.with_suffix('.json')
    filename = '.'.join(json_card.parts[2:])
    return OUTPUT_PATH / base_path / filename


def process_card_files():
    """Ingest .md files and produce .json files

    Replace image paths with the hashed filename equivalents.
    """
    cards = CARDS_PATH.glob('**/*.md')
    for card in cards:
        print('Processing %s' % card)
        data = parse_md_file(card)
        process_card_images(card, data)
        json_card = get_json_card(card)
        json_card.parent.mkdir(parents=True, exist_ok=True)
        with json_card.open('w', encoding='utf-8') as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == '__main__':
    clean_dirs()
    try:
        process_card_files()
    except RuntimeError as e:
        sys.exit(str(e))

    print('Done')
