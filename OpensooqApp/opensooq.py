import requests
from bs4 import BeautifulSoup
import json
import datetime

class opensooq:

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

    def __rectify_generated_json(self, file_name):

        try:

            # read raw json and rectify it
            with open(file_name,"r") as f:

                data = "[" + f.read()[:-1] + "]"

            # write rectified data
            with open(file_name, "w") as f:

                f.write(data)
        
        except Exception as e:

            print("Error in rectifying json:", str(e))
            
    def __pages_total(self):

        try:

            URL = "https://kw.opensooq.com/en/find"

            resonpse = requests.get(URL)

            soup = BeautifulSoup(resonpse.text, 'html.parser')

            last_page_link = soup.find('a', {"title":"Go to last page"})

            return int(last_page_link["href"].split("=")[1])
    
        except:

            return None
        
    def __scrape_posts_links(self):

        TOTAL_PAGES = self.__pages_total()

        if TOTAL_PAGES == None:
            # create empty file
            with open("posts_links.json","a") as lp:
                lp.write(json.dumps(list()))
            
            return
            

        OPENSOOQ_BASE_URL = "https://kw.opensooq.com"

        OPENSOOQ_PAGE_URL = OPENSOOQ_BASE_URL + "/en/find?page="

        for page in range(1,TOTAL_PAGES+1):

            # Log 
            self.__log("posts_links_logs.txt","Page#" + str(page) + " Time: " + str(datetime.datetime.now()) + "\n")
            
            page_response = requests.get(url=OPENSOOQ_PAGE_URL+str(page))

            soup = BeautifulSoup(page_response.text, 'html.parser')

            listing_posts = soup.find('div', {'id': "listing_posts"})

            posts_links = listing_posts.find_all('a')

            for lnk in posts_links:

                try:

                    if lnk['href'].startswith('/en/search/'):

                        lnk = OPENSOOQ_BASE_URL + lnk['href']
                    
                        # save locally
                        with open("posts_links.json","a") as lp:
                            lp.write(json.dumps(lnk) + ",") # raw json, need to rectify after cmopletion of scraping by adding square brackets at start and end of the output file
                
                except Exception as e: 

                    self.__log("posts_links_logs.txt","Post Links Scraping Error: " + str(e) + " Time: " + str(datetime.datetime.now()) + "\n")


        # rectify generated json file
        self.__rectify_generated_json("posts_links.json")

    def __scrape_listing_data(self,post_url):

        listing_response = requests.get(post_url)

        soup = BeautifulSoup(listing_response.text, 'html.parser')

        post_data = json.loads(soup.find('script', {'id': '__NEXT_DATA__'}).text)

        post_data = post_data['props']['pageProps']['postsData']

        seller_url = "https://kw.opensooq.com/en/mid/" + post_data["searchMember"]["M_user_name"] + "?info=info"

        try:

            seller_data = self.__scrape_seller_data(seller_url)

            post_data["seller_data"] = seller_data

            #clean data
            post_data = self.__clean_post_data(post_data)
            
        except Exception as e:

            self.__log("post_scraping_logs.txt", "Post Scraping Error: " + str(e) + " Time: " + str(datetime.datetime.now()) + "\n")

        
        with open("products_data.json","a") as ld:
            ld.write(json.dumps(post_data) + ",") # raw json, need to rectify after cmopletion of scraping by adding square brackets at start and end of the output file

    def __scrape_seller_data(self,url):

        response = requests.get(url)

        soup = BeautifulSoup(response.text, 'html.parser')
        
        seller_data = json.loads(soup.find('script', {'id': '__NEXT_DATA__'}).text)

        seller_data = seller_data['props']['pageProps']['data']["info"]

        return seller_data
    
    def scrape(self):

        self.__scrape_posts_links()

        with open("posts_links.json","r") as lp:

            posts_links = json.loads(lp.read())

        
        for lnk_index in range(len(posts_links)):

            try:

                # Log in text file
                self.__log("post_scraping_logs.txt", "Link#" + str(lnk_index) + " Time: " + str(datetime.datetime.now()) + "\n")
                
                # scrape post data
                self.__scrape_listing_data(posts_links[lnk_index])

            except Exception as e:

                self.__log("post_scraping_logs.txt", "Post Scraping Error: " + str(e) + " Time: " + str(datetime.datetime.now()) + "\n")

                if "connection" in str(e):
                    break
        
        # rectify products data
        self.__rectify_generated_json("products_data.json")



        



