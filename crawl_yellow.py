import logging
import csv
import re
import os
import json
import argparse
from time import sleep
from typing import Tuple, List, Optional, Dict, Iterable

import redis
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver import Chrome
from dotenv import load_dotenv
from retrying import retry


__BASE_URL__ = 'https://www.hvr.co.il/site/pg/gift_card_company'
__COMPANY_PAGE__ = 'https://www.hvr.co.il/site/pg/gift_card_store?sn={}'

# redis consts
SN_DICT_KEY = 'sn-dict'
STATUS_KEY = '{}-status'
STATUS_OK = b'OK'
DATA_KEY = '{}-data'


def filter_internet_store(iterable: Iterable):
    return not any(map(lambda i:  'אינטרנטי' in i, iterable))


SN_PATTERN = re.compile(r'javascript:gotoBranches\((\d+)\)')

logger = logging.getLogger('HvrCrawler')
logger.addHandler(logging.StreamHandler())


def get(driver, url):
    logger.debug('fetch url "%s"', url)
    driver.get(url)

    if driver.current_url != url:
        logger.info('Sign in')
        if 'signin.aspx' not in driver.current_url:
            raise Exception(f'Unknown state: url="{driver.current_url}"')
        sign_in(driver)
        assert driver.current_url == url
        logger.info('Sign in succeed')


def sign_in(driver, user_id=None, pwd=None):
    user_id = user_id or os.environ['USER_ID']
    pwd = pwd or os.environ['PASSWORD']

    logger.info('Sign in with user id "%s"', user_id)

    driver.find_element_by_xpath('//*[@id="tz"]').send_keys(user_id)
    driver.find_element_by_xpath('//*[@id="password"]').send_keys(pwd)
    driver.find_element_by_xpath('/html/body/div[1]/div[1]/div[2]/div/button').click()


def crawl_companies_sn(driver) -> Dict[str, str]:
    get(driver, __BASE_URL__)

    sleep(1)

    companies_divs = driver.find_element_by_xpath('//*[@id="company-list"]').find_elements_by_xpath("*")
    logger.info('Num companies: %d', len(companies_divs))

    result = {}

    # get all companies ids
    for ind, company_div in enumerate(companies_divs, 1):
        name: str = company_div.find_element_by_xpath('.//p[1]').text
        href = company_div.find_element_by_xpath('.//a[@id="branches-link"]').get_attribute('href')
        sn = SN_PATTERN.findall(href)
        assert sn
        sn = sn[0]

        logger.info('%d - Company "%s" - sn=%s', ind, name, sn)

        result[name] = sn

    return result


def crawl_company_branches(driver, sn, retries) -> List[Tuple[str, str]]:
    url = __COMPANY_PAGE__.format(sn)
    get(driver, url)

    sleep(3)

    assert driver.current_url == url

    @retry(wait_fixed=1000, stop_max_attempt_number=retries)
    def get_branches():
        # get branches list
        branches_elements = driver.find_element_by_xpath('//*[@id="branch-list"]').find_elements_by_xpath('*')
        branches = map(parse_branch, branches_elements)
        branches = list(filter(lambda x: x, branches))

        if not len(branches):
            raise Exception('No branches found')

        return branches

    return get_branches()


def parse_branch(element: WebElement) -> Optional[Tuple[str, str]]:
    if element.get_attribute('id') == 'branch-list-header':
        return
    rows = element.find_element_by_xpath('.//div/div[1]/div')
    branch_name = rows.find_element_by_xpath('.//div[1]').text
    branch_address = rows.find_element_by_xpath('.//div[2]').text
    return branch_name, branch_address


def main(argv=None):
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-o', metavar='outfile', type=argparse.FileType('a'), required=True, help='output csv file')
    args_parser.add_argument('--user-id')
    args_parser.add_argument('--password')
    args_parser.add_argument('--redis-host')
    args_parser.add_argument('--retries', type=int, default=20)
    args_parser.add_argument('--log-level', default='INFO')
    args = args_parser.parse_args(argv)

    logger.setLevel(args.log_level)
    load_dotenv()

    with redis.Redis(host=args.redis_host or os.environ['REDIS_HOST'] or 'localhost') as r:
        with Chrome() as driver:

            if r.exists(SN_DICT_KEY):
                companies_sn = json.loads(r.get(SN_DICT_KEY))
            else:
                companies_sn = crawl_companies_sn(driver)
                assert companies_sn
                r.set(SN_DICT_KEY, json.dumps(companies_sn))

            for ind, (company, sn) in enumerate(companies_sn.items(), 1):
                status_key = STATUS_KEY.format(sn)

                if r.get(status_key) == STATUS_OK:
                    logger.info('%d - "%s" (sn=%s) Already crawled, Skip', ind, company, sn)
                else:
                    logger.info('%d - Crawling branches of "%s" (sn=%s)', ind, company, sn)

                    branches = crawl_company_branches(driver, sn, args.retries)
                    logger.info('"%s" has %d branches', company, len(branches))

                    branches_str = json.dumps(branches)
                    r.set(DATA_KEY.format(sn), branches_str)
                    r.set(status_key, STATUS_OK)

        logger.info('Creating CSV from results in "%s"', args.o.name)
        writer = csv.writer(args.o)
        # headers row
        writer.writerow(('Name', 'Branch Name', 'Branch Address', 'Full Branch Name'))

        for ind, (company, sn) in enumerate(companies_sn.items(), 1):
            branches_str = r.get(DATA_KEY.format(sn))
            branches = json.loads(branches_str)

            # filter out internet stores
            branches = filter(filter_internet_store, branches)

            for branch_name, branch_address in branches:
                writer.writerow((company, branch_name, branch_address, f'{company} {branch_name}'))

        logger.info('Done!')


if __name__ == '__main__':
    main()
