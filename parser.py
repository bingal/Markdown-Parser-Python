# -*- encoding: utf-8 -*-
'''Parses Markdown strings and return a Markdown object.

First split strings into blocks as paragraphs. For each paragraph,
parse it when it is a List item, a Header, an Emphasis, a Bold, or just simple text.

Usage:

>>> parse_markdown('This is a paragraph.')
Markdown([Paragraph([Text('This is a paragraph.')])])

>>> parse_markdown('The first paragraph.\\n\\nThe second paragraph.')
Markdown([Paragraph([Text('The first paragraph.')]), Paragraph([Text('The second paragraph.')])])

>>> parse_markdown('Emphasis *is* supported.')
Markdown([Paragraph([Text('Emphasis '), Emphasis('is'), Text(' supported.')])])

>>> parse_markdown('Bold **is** supported.')
Markdown([Paragraph([Text('Bold '), Bold('is'), Text(' supported.')])])

>>> parse_markdown('- a list')
Markdown([List([Paragraph([Text('a list')])])])

>>> parse_markdown('- the first item\\n- the second item')
Markdown([List([Paragraph([Text('the first item')]), Paragraph([Text('the second item')])])])

>>> parse_markdown('- Emphasis *is* supported.')
Markdown([List([Paragraph([Text('Emphasis '), Emphasis('is'), Text(' supported.')])])])

>>> parse_markdown('* the first item\\n* the second item')
Markdown([List([Paragraph([Text('the first item')]), Paragraph([Text('the second item')])])])

>>> parse_markdown('- item1\\n- item2\\n - item2.1\\n - item2.2\\n- item3')
Markdown([List([Paragraph([Text('item1')]), Paragraph([Paragraph([Text('item2')]), List([Paragraph([Text('item2.1')]), Paragraph([Text('item2.2')])])]), Paragraph([Text('item3')])])])

>>> parse_markdown('#######this is header')
Markdown([Paragraph([Header(6,[Text('#this is header')])])])

>>> parse_markdown('#######this is *header* and **header**')
Markdown([Paragraph([Header(6,[Text('#this is '), Emphasis('header'), Text(' and '), Bold('header'), Text('')])])])

>>> parse_markdown('#header1\\n##header2\\n\\nanother paragraph')
Markdown([Paragraph([Header(1,[Text('header1')]), Header(2,[Text('header2')])]), Paragraph([Text('another paragraph')])])

>>> parse_markdown('hello ##this is not *header* and **header**')
Markdown([Paragraph([Text('hello ##this is not '), Emphasis('header'), Text(' and '), Bold('header'), Text('')])])
'''
import re
import doctest

def parse_markdown(string):
    return Markdown([parse_block(block) for block in split_into_blocks(string)])


def split_into_blocks(string):
    '''Return a list of blocks split by '\n\n'

    >>> split_into_blocks('The first block.\\n\\n\\nThe second block.')
    ['The first block.', 'The second block.']'''
    _blocks =  re.split(r'\n{2,}', string)
    blocks = []
    tmp = []
    closed = True
    for block in _blocks:
        if closed:
            tmp.clear()
        # code start
        tmp.append(block)
        if closed:
            if re.match('```[\s\S]*[^`]$', block):
                closed = False
        # code end
        else:
            if re.match('[\s\S]*```$', block):
                closed = True
        if closed:
            blocks.append('\n\n'.join(tmp))
    return blocks


def parse_block(block):
    '''Handle block that contains list items
    '''
    # parse code block
    match = re.match(r'^```', block)
    if match:
        return Paragraph([Code(block)])
    
    # extract headers before list
    block = parse_header(block)
    if not isinstance(block, str):
        for header in block.items:
            parts = re.split('(\\*\\*[^\\*]*\\*\\*|\\*[^\\*]*\\*)', header.items)
            header.items = list(map(parse_part, parts))
        return block
    # List items begins with ' - ' or ' * '
    match = re.match(r'^[-|\*]\s+', block)
    if match is not None:
        # '^' should match at the beginning of the string and at the beginning of each line
        items = [item.strip() for item in re.split(r'^[-|\*]\s+', block, flags=re.M)[1:]]
        lists = List(list(map(parse_paragraph, items)))
        for item in lists.items:
            match = re.search(r'\s+[-|\*]\s+', item.items[0].text)
            if match is not None:
                inner_items = [inner_item.strip() for inner_item in re.split(r'\s+[-|\*]\s+', item.items[0].text, flags=re.M)]
                item.items = list()
                item.items.append(parse_paragraph(inner_items[0]))
                inner_lists = List(list(map(parse_paragraph, inner_items[1:])))
                item.items.append(inner_lists)
        return lists
    return parse_paragraph(block)


def parse_paragraph(block):
    parts = re.split('(\\*\\*[^\\*]*\\*\\*|\\*[^\\*]*\\*)', block)  # split out Emphasis and Bold
    return Paragraph(list(map(parse_part, parts)))


def parse_part(string):
    '''Parse Emphasis and Bold
    '''
    for regexp, klass in INLINE_ELEMENTS:
        match = re.match(regexp, string)
        if match is not None:
            return klass(match.group(1))
    return Text(string)


def parse_header(string):
    '''Parse headers
    '''
    matches = re.findall(r'^#{1,6}', string, flags=re.M)
    header_items = re.split(r'^#{1,6}', string, flags=re.M)[1:]
    if len(matches) > 0:
        return Paragraph(list(map(lambda match_items: Header(len(match_items[0]), match_items[1].strip()), zip(matches, header_items))))
    return string


class Markdown(object):
    def __init__(self, blocks):
        self.blocks = blocks

    def __repr__(self):
        return 'Markdown({!r})'.format(self.blocks)


class Paragraph(object):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return 'Paragraph({!r})'.format(self.items)


class List(object):
    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return 'List({!r})'.format(self.items)


class Code(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return 'Code({!r})'.format(self.text)

class Text(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return 'Text({!r})'.format(self.text)


class Emphasis(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return 'Emphasis({!r})'.format(self.text)


class Bold(object):
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return 'Bold({!r})'.format(self.text)


class Header(object):
    def __init__(self, level, items):
        self.level = level
        self.items = items

    def __repr__(self):
        return 'Header({},{!r})'.format(self.level, self.items)


INLINE_ELEMENTS = [
    (r'\*\*([^\*]*)\*\*', Bold),
    (r'\*([^\*]*)\*', Emphasis)
]


def print_block(block, depth=0):
    if type(block) == Paragraph:
        print('======Paragraph start======')
        for sub_block in block.items:
            print_block(sub_block, depth+1)
        print('======Paragraph end======\n')
    elif type(block) == List:
        print('-----List start-----')
        for sub_block in block.items:
            print_block(sub_block, depth+1)
        print('-----List end-----\n')
    else:
        print('{} {}'.format('-'*depth, block))


def output_block(block, depth=0):
    result = []
    if type(block) == Paragraph:
        for sub_block in block.items:
            result.extend(output_block(sub_block, depth+1))
        result.append('\n')
    elif type(block) == List:
        for sub_block in block.items:
            result.append('- ')
            result.extend(output_block(sub_block, depth+1))
        result.append('\n\n')
    elif type(block) == Header:
        result.append('#'*block.level + ' ')
        for sub_block in block.items:
            result.extend(output_block(sub_block, depth+1))
        result.append('\n\n')
    elif type(block) == Emphasis:
        result.append('*{}*'.format(block))
    elif type(block) == Bold:
        result.append('**{}**'.format(block))
    elif type(block) == Code:
        result.append('\n')
        result.append(block.text)
    elif type(block) == Text:
        if block.text.startswith('>'):
            result.append('\n')
        result.append(block.text)
        if depth==0 and block.text.endswith('\n---'):
            result.append('\n\n')
        if depth == 0 and block.text.endswith('\n```'):
            result.append('\n\n')
        # fanyi
        if not (block.text.startswith('---') or block.text.startswith('>')):
            print(block.text)
            print('---------------------\n')
    if depth == 0:
        result.append('\n')

    return result


if __name__ == '__main__':
    doctest.testmod()
    with open('out.md', 'w') as fo:
        with open('installation.md', 'r') as f:
            string = f.read()
            for block in parse_markdown(string).blocks:
                fo.write(''.join(output_block(block, 0)))
                print_block(block)
