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
    """Return the all data for file_obj.

    :param file_obj pathlib.Path object of a .md file
    :return dict of frontmatter data and the parsed Markdown in
            the 'html_content' dict key
    """
    with file_obj.open(encoding='utf8') as fh:
        yamltext, mdtext = parse_md_front_matter(fh)

    data = yaml.load(yamltext)
    if mdtext.strip():
        data['html_content'] = markdown(mdtext)

    return data


def clean_dirs():
    """Delete the output directory in preparation for a clean build"""
    rmtree(str(OUTPUT_PATH), ignore_errors=True)


def get_file_hash(file_obj):
    """Return the md5 hash of a file

    :param file_obj pathlib.Path object for a file
    :return str md5 sum of the given file
    """
    hasher = hashlib.md5()
    with file_obj.open('rb') as fh:
        while True:
            chunk = fh.read(CHUNK_SIZE)
            if not chunk:
                break

            hasher.update(chunk)

    return hasher.hexdigest()


def get_hashed_filename(file_obj):
    """Return a filename that includes the md5 hash"""
    shorthash = get_file_hash(file_obj)[:12]
    name = file_obj.stem
    ext = file_obj.suffix
    file_obj = IMAGES_HASHED / file_obj.relative_to(CARDS_PATH)
    return file_obj.with_name('%s.%s%s' % (name, shorthash, ext))


def get_highres_filename(file_obj):
    """Return a filename for the High Resolution version of the given file.

    :param file_obj Path object
    :return Path object

    >>> get_highres_filename(Path('home/card_1/dude.jpg'))
    PosixPath('home/card_1/dude-high-res.jpg')
    """
    name = file_obj.stem
    ext = file_obj.suffix
    return file_obj.with_name('%s-high-res%s' % (name, ext))


def process_image_file(fobj):
    """Calculate the hashed filename for an image and copy it to
    that new name in the output directory.

    :param fobj Path object for an image file
    :return Path object for the new image file in the output dir
    """
    hashed_fobj = get_hashed_filename(fobj)
    hashed_fobj.parent.mkdir(parents=True, exist_ok=True)
    print('Copying %s to %s' % (fobj, hashed_fobj))
    copy(fobj, hashed_fobj)
    return hashed_fobj


def process_card_images(card, data):
    """Find and process images referenced by card file data.

    If a card has an `image` field, process that image, and if it has
    `include_highres_image: true` then calculate the high-res filename
    and process that image as well. Once processed save the new filenames
    to the card data. If a referenced image can't be found raise a RuntimeError.

    :param card Path object for a card data file
    :param data dict object of data parsed from `card`. Will be modified in place.
    :return None
    """
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
    """Given a card file object, return a new one for where the processed data should be written.

    :param card_obj Path object for a card .md file
    :return Path object for a .json file to which the processed data will be written.
    """
    base_path = card_obj.parents[1]
    json_card = card_obj.with_suffix('.json')
    filename = '.'.join(json_card.parts[2:])
    return OUTPUT_PATH / base_path / filename


def process_card_files():
    """Ingest .md files and produce .json files.

    Search for all *.md files in the content directory, parse the data therein,
    and replace image paths with the hashed filename equivalents.
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
