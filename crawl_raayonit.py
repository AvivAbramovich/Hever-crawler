import argparse
import csv
import logging
from typing import Tuple

from selenium.webdriver import Chrome
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


__URL__ = 'https://www.raayonit.co.il/club/?ClubNum=2&ClubVoucherTypeNum=17'
__ID_PATTERN__ = '//*[@id="summary_row_{}"]'

logger = logging.getLogger('HvrRaayonitCrawler')
logger.addHandler(logging.StreamHandler())


def parse_business(element: WebElement) -> Tuple[str, str]:
    name = element.find_element_by_xpath('./div[1]').text.strip()
    address = element.find_element_by_xpath('./div[3]').text.strip()
    return name, address


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-o', metavar='outfile', type=argparse.FileType('w'), required=True, help='output csv file')
    args_parser.add_argument('--log-level', default='INFO')
    args = args_parser.parse_args()

    logger.setLevel(args.log_level)

    results = []

    with Chrome() as driver:
        logger.info('driver get url "%s"', __URL__)
        driver.get(__URL__)

        try:
            div_id = 1
            while True:
                xpath = __ID_PATTERN__.format(div_id)
                logger.debug(f'={xpath=}')
                e = driver.find_element_by_xpath(xpath)
                name, address = parse_business(e)
                logger.info(f'{name=}, {address=}')
                results.append((name, address))
                div_id += 1
        except NoSuchElementException:
            logger.info('Done crawling (%d items)', div_id-1)

    logger.info('Creating csv file "%s"', args.o.name)
    
    csv_writer = csv.writer(args.o)
    csv_writer.writerow(['Name', 'Address', 'Name+Address'])
    for name, address in results:
        csv_writer.writerow([name, address, f'{name}, {address}'])

    logger.info('Done!')


if __name__ == '__main__':
    main()
