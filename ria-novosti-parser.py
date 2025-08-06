import argparse
import requests
from bs4 import BeautifulSoup
import json
import re
from tqdm import tqdm
from datetime import datetime, timedelta
import requests
import pandas as pd
import time
import os



class CollectNewsPages:
    def __init__(self, start_date, end_date,):
        #self.search_words = search_words.split(' ') # currently not implemented, awaiting updates 
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 "
                          "Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8,af;q=0.7"
        }
        self.start_date = start_date
        self.end_date = end_date

    def _generate_date_range(self):
        """generates the dates in the input range in yyyymmdd format for further parsing"""
        start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(self.end_date, "%Y-%m-%d")

        result = []
        current_date = start_date
        while current_date <= end_date:
            result.append(current_date.strftime("%Y%m%d"))
            current_date += timedelta(days=1)
        return result




    def get_news_pages_for_a_range(self, day):
        base_url = "https://ria.ru"
        url = f"{base_url}/{day}"
        links_df = pd.DataFrame(columns=['Title', "URL"])
        
        page = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(page.text, "html.parser")

        links_df = pd.concat([links_df, self._extract_articles_links(page.text)], ignore_index=True)

        more_button = soup.find('div', class_='list-more')

        pbar = tqdm(desc=f"Loading more pages for {day}", unit="page")
        while more_button:
            data_url = more_button.get('data-url')
            if not data_url:
                break

            more_url = base_url + data_url
            more_resp = requests.get(more_url, headers=self.headers)

            res_df = self._extract_articles_links(more_resp.text)
            if res_df.empty:
                break

            links_df = pd.concat([links_df, res_df], ignore_index=True)

            more_soup = BeautifulSoup(more_resp.text, "html.parser")
            more_button = more_soup.find('div', class_='list-more')

            time.sleep(0.5)
            pbar.update(1)
        pbar.close()
        return links_df
    

    def _extract_articles_links(self, page_code):
        """helper method, parsing the page with links to news articles
           saves as pandas DataFrame with titles and links columns"""
        interim_df = pd.DataFrame(columns=['Title', 'URL'])
        soup = BeautifulSoup(page_code, 'html.parser')
        article_blocs = soup.find_all('div', class_='list-item')
        for article_bloc in article_blocs:
            link_tag = article_bloc.find('a', class_="list-item__title color-font-hover-only")
            if link_tag:
                news_title = link_tag.get_text(strip=True)
                link_href = link_tag['href']
                interim_df.loc[len(interim_df)] = [news_title, link_href]
        return interim_df
    
    def _extract_metadata(self,soup):
        """
        helper method which extracts the articles metadata from JavaScript headers
        """
        script_tag = soup.find("script", string=re.compile(r"dataLayer\.push\s*\(\s*\{"))
        if not script_tag:
            return None
        
        match = re.search(r"dataLayer\.push\s*\(\s*\{(.+?)\}\s*\);", script_tag.string, re.S)
        if not match:
            return None

        js_content = match.group(1)

        js_content = re.sub(r"(\s*)'([^']+)'\s*:", r'"\2":', js_content)  # keys
        js_content = re.sub(r":\s*'([^']*)'", r': "\1"', js_content)      # string values

        try:
            metadata = json.loads("{" + js_content + "}")
            return metadata
        except json.JSONDecodeError as e:
            print("JSON parsing error:", e)
            return None
    
    def _parse_news_body(self, news_url):
        page = requests.get(news_url, headers=self.headers)
        soup = BeautifulSoup(page.text,'html.parser')
        metadata = self._extract_metadata(soup)
        if metadata:
            title = metadata['page_title']
            keywords = metadata['page_tags']
            theme = metadata['page_rubric']
        else: title, keywords, theme = None, None, None

        blocks = soup.find_all("div", class_="article__text")
        if blocks:
            full_text = " ".join(block.get_text(strip=True) for block in blocks)
        else: 
            full_text = None
        
        return title, theme, keywords, full_text

        
    
    def extract_all_news(self):
        date_range = self._generate_date_range()

        for date in tqdm(date_range):
            year_month = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m")

            links_df_path = f'RIA-Novosti_news_links_{year_month}.csv'
            news_df_path = f'RIA-Novosti_news_texts_{year_month}.csv'

            interim_df = self.get_news_pages_for_a_range(date)
            interim_df.to_csv(
                links_df_path,
                mode="a",
                index=False,
                header=not os.path.exists(links_df_path)  # write header if file doesn't exist
            )

            links = list(interim_df['URL'])
            for link in links:
                res = self._parse_news_body(link)
                row_data = {
                    "Date": date,
                    "Title": res[0],
                    "Theme": res[1],
                    "Keywords": res[2],
                    "Full Text": res[3],
                    "URL": link
                }
                pd.DataFrame([row_data]).to_csv(
                    news_df_path,
                    mode="a",
                    index=False,
                    header=not os.path.exists(news_df_path)
                )
                time.sleep(0.8)





def main():
    parser = argparse.ArgumentParser(description="Ria-Novosti parser")
    
    #parser.add_argument(
    #    "--keyword", 
    #    type=str, 
    #    required=True, 
    #    help="Search keywords separated by spaces"
    #) will be implement in further revisions

    parser.add_argument(
        "--start_date", 
        type=str, 
        required=True, 
        help="Start date in yyyy-mm-dd format"
    )

    parser.add_argument(
        "--end_date", 
        type=str, 
        required=True, 
        help="End date in yyyy-mm-dd format"
    )
    
    args = parser.parse_args()

    ria_parser = CollectNewsPages(args.keyword, args.start_date, args.end_date)
    ria_parser.extract_all_news()


if __name__ == "__main__":  
    main()