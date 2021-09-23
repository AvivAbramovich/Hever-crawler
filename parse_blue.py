import argparse
import re
import csv

from typing import Tuple

import bs4


PATTERN = re.compile(r'([^\(]+)(?:\(.+\))?')


def parse_children(child) -> Tuple[str, str]:
    row = child.find('div', {'class': 'row'})
    items = [i for i in row.children if type(i) is bs4.element.Tag]
    name = items[0].find('a').text
    address_raw = [i for i in items[2].children if type(i) is bs4.element.Tag][1].find('span').text
    address = PATTERN.findall(address_raw)[0]
    return name, address


def main(argv=None):
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('file_path')
    args_parser.add_argument('-o')
    args = args_parser.parse_args(argv)

    with open(args.file_path) as f:
        s = bs4.BeautifulSoup(f.read(), features='html.parser')

        results = []

        for child in s.find('div', {'id': 'branch-list'}).children:
            if child.get('id') == 'branch-list-header':
                continue
            results.append(parse_children(child))

    with open(args.o, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(('Name', 'Address'))
        writer.writerows(results)


if __name__ == '__main__':
    main()
