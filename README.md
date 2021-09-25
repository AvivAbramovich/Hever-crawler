# Hever (חבר) crawl and parse

Crawl and parse data from the Hever (חבר) website and format into CSV.

So, I just released from the IDF and wanted to keep the data of businesses and restaurants from the "Hever" website before it blocks me, so I made this Python scripts to keep this data and format it into CSV so I can upload into a Google Map and view it easily.

[The Google Map with all the data](https://www.google.com/maps/d/viewer?hl=iw&mid=1fs9u9Z4_ID8wCs8GACboK7NgG7qTrDx3&ll=31.585829973273615%2C35.57174168252162&z=7&fbclid=IwAR2iawIiBL6cubMfSy5oU_t4bSatkELrd7hPMQdYcD5y4QsbZO0XN4Q5id8)

## The Blue Card (חבר טעמים)
In this case, I just download the full page with the table of all restaurants and branches into single static HTML page.

The `parse_blue.py` script just parse this HTML using `BeautifulSoup`.

### Using
1. Download the page as complete webpage into single HTML file.
2. Install `BeautifulSoup`
    ```shell
    pip install bs4
    ```
3. Run script
    ```shell
    python parse_blue.py /path/to/page.html -o result.csv
    ```

## The Yellow Card (חבר של קבע)
This one was a bit more complicated because there was no single page with all the data I can simply save like in the previous case because the main page include all the chains and businesses, and each component lead to a page that list the branches and information about the branches.

So in this case I used `Selenium` to crawl all the different businesses and their branches.

Because of this process can take a while (there was about 180+ different businesses) and it crashed so often when the website takes a time to load the data, I used `redis` to cache the data I already crawled, so this script requires a redis instance running.

Note: In this method you should log in into to Hever website, so you need to specify your credentials. 

### Using
1. Run an instance of `redis`. I used a docker container, but you can run it any way you'd like it.
2. Install python packages dependencies
    ```shell
    pip install -r yellow_requirements.txt
    ```
3. Create a `.env` file and add your credentials inside (the `REDIS_HOST` is optional).
   ```dotenv
   USER_ID=123456789
   PASSWORD=my-password
   REDIS_HOST=localhost
   ```
4. Run the script
   ```shell
   python crawl_yellow.py -o yellow.csv
   ```
## Raayonit (רעיונית)

Crawl the "Raayonit" restaurants from their website.

This one also uses `Selenium` to crawl the website.

### Usage

1. Install `Selenium`
   ```shell
   pip install selenium
   ```
2. Run the script
   ```shell
   python crawl_raayonit.py -o result.csv
   ```
