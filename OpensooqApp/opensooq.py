import requests
from bs4 import BeautifulSoup
import json
import datetime
import schedule
import time
import threading
from json_csv_converter import convert

class opensooq:

    def __init__(self):

        self.products_posts_links = list()

        self.products_data = list()

    def __clean_post_data(self, raw_product_data):

        clean_product_data = {"name": raw_product_data["title"],
                            "description" : raw_product_data["descriptionWithTags"],
                            "price": raw_product_data["price"],
                            "category": raw_product_data["category_reporting_name"],
                            "subcategory": raw_product_data["subcategory_name"],
                            "phone": raw_product_data["phone"],
                            "post_url": raw_product_data["post_url"],
                            "currency": raw_product_data["currency"],
                            "city": raw_product_data["city"]["name"],
                            "neighborhood": raw_product_data["neighborhood"]["name"] if "neighborhood" in raw_product_data.keys() and raw_product_data["neighborhood"] != None else None,
                            "product_attributes": [{"name":attribute["field_label"], "value":attribute["option_label"]} for attribute in raw_product_data["dynamicAttributesObject"]],
                            "seller_data": {
                                "name":raw_product_data["searchMember"]["full_name"],
                                "profile_picture": raw_product_data["searchMember"]["profile_picture"],
                                "profile_url": "https://kw.opensooq.com/en/mid/" + raw_product_data["searchMember"]["M_user_name"],
                                "member_isShop": raw_product_data["member_isShop"],
                                "authorised_seller": False,
                                "memberCountry":  None,
                                "rating": 0,
                                "followersCount": 0
                            },
                            "media": ["https://opensooq-images.os-cdn.com/previews/0x720/" + media["uri"] + ".webp" for media in raw_product_data["mediasWith360"]]
                            }
        

        if "seller_data" in raw_product_data.keys() and raw_product_data["seller_data"] != None:

            if "membersDetails" in raw_product_data["seller_data"].keys() and raw_product_data["seller_data"]["membersDetails"] != None:

                clean_product_data["seller_data"]["authorised_seller"] = raw_product_data["seller_data"]["membersDetails"]["authorised_seller"]

            if "memberCountry" in raw_product_data["seller_data"].keys():

                clean_product_data["seller_data"]["memberCountry"] = raw_product_data["seller_data"]["memberCountry"]

            clean_product_data["seller_data"]["rating"] = raw_product_data["seller_data"]["rating"]["average_rating"]
            
            clean_product_data["seller_data"]["followersCount"] = raw_product_data["seller_data"]["followersCount"]

        return clean_product_data

    def __log(self,file_name, message):

        with open(file_name,"a") as log:

            log.write(message)
            
    def __pages_total(self):

        try:

            URL = "https://kw.opensooq.com/en/find"

            resonpse = requests.get(URL)

            soup = BeautifulSoup(resonpse.text, 'html.parser')

            last_page_link = soup.find('a', {"title":"Go to last page"})

            return int(last_page_link["href"].split("=")[1])
    
        except:

            return None
    
    def __extract_posts_links_from_page(self, page_no):

        OPENSOOQ_BASE_URL = "https://kw.opensooq.com"

        OPENSOOQ_PAGE_URL = OPENSOOQ_BASE_URL + "/en/find?page="

        # Log 
        self.__log("posts_links_logs.txt","Page#" + str(page_no) + " Time: " + str(datetime.datetime.now()) + "\n")
        
        page_response = requests.get(url=OPENSOOQ_PAGE_URL+str(page_no))
        
        soup = BeautifulSoup(page_response.text, 'html.parser')
        
        listing_posts = soup.find('div', {'id': "listing_posts"})
        
        posts_links = listing_posts.find_all('a')
        
        for lnk in posts_links:

                try:

                    if lnk['href'].startswith('/en/search/'):

                        lnk = OPENSOOQ_BASE_URL + lnk['href']
                    
                        # save locally
                        self.products_posts_links.append(lnk)
                        # with open("posts_links.json","a") as lp:
                        #     lp.write(json.dumps(lnk) + ",") # raw json, need to rectify after cmopletion of scraping by adding square brackets at start and end of the output file
                
                except Exception as e: 

                    self.__log("posts_links_logs.txt","Post Links Scraping Error: " + str(e) + " Time: " + str(datetime.datetime.now()) + "\n")

    def __scrape_posts_links(self):

        TOTAL_PAGES = self.__pages_total()

        if TOTAL_PAGES == None:
            return
            
        start = 1
        page_no_step = 5

        for end in range(page_no_step + 1, TOTAL_PAGES+1, page_no_step ):

            print("Scraped Posts Links:", len(self.products_posts_links))
    
            threads = list()

            for page_no in range(start,end):

                th = threading.Thread(target=self.__extract_posts_links_from_page, args=(page_no, ))
                threads.append(th)
                th.start()
            
            for th in threads:
                th.join()

            start = end

        
        # Execute for any remaining pages
        threads = list()
        for page_no in range(start, TOTAL_PAGES+1):
            th = threading.Thread(target=self.__extract_posts_links_from_page, args=(page_no, ))
            threads.append(th)
            th.start()
        
        for th in threads:
            th.join()
        
        print("Scraped Posts Links:", len(self.products_posts_links))
            
    def __scrape_listing_data(self,post_url):

        try:

            listing_response = requests.get(post_url)

            soup = BeautifulSoup(listing_response.text, 'html.parser')

            post_data = json.loads(soup.find('script', {'id': '__NEXT_DATA__'}).text)

            post_data = post_data['props']['pageProps']['postsData']

            seller_url = "https://kw.opensooq.com/en/mid/" + post_data["searchMember"]["M_user_name"] + "?info=info"

            seller_data = self.__scrape_seller_data(seller_url)

            post_data["seller_data"] = seller_data

            #clean data
            post_data = self.__clean_post_data(post_data)

            self.products_data.append(post_data)
            
        except Exception as e:

            self.__log("post_scraping_logs.txt", "Post Scraping Error: " + str(e) + " Time: " + str(datetime.datetime.now()) + "\n")


    def __scrape_seller_data(self,url):

        response = requests.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        seller_data = json.loads(soup.find('script', {'id': '__NEXT_DATA__'}).text)

        seller_data = seller_data['props']['pageProps']['data']["info"]

        return seller_data

    def __write_data(self, filename, data):
        with open(filename, "w") as temp_f:
            temp_f.write(data)
    
    def scrape(self):

        self.__scrape_posts_links()

        try:
  
                TOTAL_POSTS = len(self.products_posts_links)

                print("TOTAL POST:", TOTAL_POSTS)

                start = 1
                post_no_step = 5

                for end in range(post_no_step + 1, TOTAL_POSTS+1, post_no_step ):
            
                    threads = list()

                    for post_lnk_index in range(start,end):
                        # Log in text file
                        self.__log("post_scraping_logs.txt", "Link#" + str(post_lnk_index) + " Time: " + str(datetime.datetime.now()) + "\n")
                        post_lnk = self.products_posts_links[post_lnk_index]
                        th = threading.Thread(target=self.__scrape_listing_data, args=(post_lnk, ))
                        threads.append(th)
                        th.start()
                    
                    for th in threads:
                        th.join()

                    start = end

                
                # Execute for any remaining pages
                threads = list()
                for post_lnk_index in range(start, TOTAL_POSTS+1):
                    # Log in text file
                    self.__log("post_scraping_logs.txt", "Link#" + str(post_lnk_index) + " Time: " + str(datetime.datetime.now()) + "\n")
                    post_lnk = self.products_posts_links[post_lnk_index]
                    th = threading.Thread(target=self.__scrape_listing_data, args=(post_lnk, ))
                    threads.append(th)
                    th.start()
                
                for th in threads:
                    th.join()

        except Exception as e:

                self.__log("post_scraping_logs.txt", "Post Scraping Error: " + str(e) + " Time: " + str(datetime.datetime.now()) + "\n")

        convert(self.products_data)

if __name__ == "__main__":

    op = opensooq()

    op.scrape()
    # schedule.every().day.at("1:00").do(op.scrape)

    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
        



