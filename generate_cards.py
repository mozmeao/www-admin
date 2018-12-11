#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from textwrap import dedent


def print_card(card):
    c_file_name = f'content/home/card_{card["id"]}.en-US.md'
    content = dedent(f"""\
        ---
        # card {card['id']}, size: {card['card_size']}
        title: "{card['title']}"
        image: "{card['image_url']}"
        link_url: "{card['link_url']}"
        tag_label: "{card['tag_label']}"
        aspect_ratio: "{card['aspect_ratio']}"
        highres_image: {card['include_highres_image']}
        """)
    if 'youtube_id' in card:
        content += f'''youtube_id: "{card['youtube_id']}"\n'''
    if 'media_icon' in card:
        content += f'''media_icon: "{card['media_icon']}"\n'''

    content += dedent(f"""\
        ---
        {card['desc']}
        """)
    with open(c_file_name, 'w') as cf:
        cf.write(content)


RE_CARD_ID = re.compile(r'\<\!-- (\d{1,2}) --\>')
RE_ARG_LINE = re.compile(r'(\w+)=(.+)$')
CARD_START = '{{ card('
CARD_END = ')}}'


def extract_cards(template_file):
    current_card = {}
    in_card = False
    for line in template_file:
        line = line.strip()
        match = RE_CARD_ID.search(line)
        if match:
            current_card['id'] = match.group(1)
            print('card:', current_card['id'])
            continue

        if current_card and line == CARD_START:
            in_card = True
            continue

        if in_card and line == CARD_END:
            in_card = False
            process_card(current_card)
            print_card(current_card)
            current_card = {}
            continue

        if current_card and in_card:
            match = RE_ARG_LINE.search(line)
            if match:
                current_card[match.group(1)] = process_value(match.group(2))


def process_card(card):
    print(card)
    card['image_url'] = 'home/' + card['image_url'].split('/')[-1]

    if 'include_highres_image' in card:
        card['include_highres_image'] = card['include_highres_image'].lower()
    else:
        card['include_highres_image'] = 'false'

    parts = card['aspect_ratio'].split('-')
    card['aspect_ratio'] = f'{parts[-2]}-{parts[-1]}'

    if 'class' in card:
        card['card_size'] = card['class'].split('-')[-1]
        del card['class']
    else:
        card['card_size'] = 'small'

    if 'media_icon' in card:
        card['media_icon'] = card['media_icon'].split('-')[-1]


def process_value(value):
    if value.startswith("_('"):
        value = value[3:]
    if value.startswith("url('"):
        value = value[5:]
    if value.startswith("'"):
        value = value[1:]
    if value.startswith('"'):
        value = value[1:]
    if value.endswith(","):
        value = value[:-1]
    if value.endswith("')"):
        value = value[:-2]
    if value.endswith("'"):
        value = value[:-1]
    if value.endswith('"'):
        value = value[:-1]

    return value


if __name__ == '__main__':
    with open('../bedrock/bedrock/mozorg/templates/mozorg/home/home-en.html') as tf:
        extract_cards(tf)
