# Python script to go through all pages of a vwVortex thread and download all pictures, and then save them to the
#  requested local folder
# motivating target: https://www.vwvortex.com/threads/introducing-the-new-vwvortex-project-car.6916032/

# basic algorithm:
#  1. get first page of thread, calculate if there are any more pages
#  2. parse page content, find and download pictures, saving to specified folder as we go
#  3. possible to check if we've already downloaded a picture? if so, don't download
#  4. continue to next page, repeat

### IMPORTS ###
import os
import pathlib
import re
import requests
import bs4
import shutil


### CONSTANTS ###
url_regex = r"https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,4}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)"


### CLASSES ###
class VortexScraper:

    def __init__(self, url, path, name, create=False):
        self.start_url = url
        self.parent_folder = os.path.join(path, name)
        self.pic_prefix = name
        self.create_folders = create
        self.validate_url()
        self.validate_path()
        print("Current working directory: {0}".format(os.getcwd()))
        os.chdir(self.parent_folder)
        print("Switching to working directory of: {0}".format(os.getcwd()))

        self.next_url = self.start_url
        self.previous_pics = []
        self.previous_urls = []
        self.pic_count = 0

        while self.next_url is not None:
            self.scrape_page()

    def scrape_page(self):
        page_contents = None

        while page_contents is None and self.next_url is not None:
            try:
                print("Starting page:", self.next_url)
                response = requests.get(self.next_url)
                response.raise_for_status()
                page_contents = response.text
                self.next_url = None  # reset next url after successfully reading page contents
            except requests.exceptions.Timeout as errt:
                print('Page Timeout:', errt)
                continue
            except requests.exceptions.HTTPError as errh:
                print("HTTP Error:", errh)
                return None
            except requests.exceptions.RequestException as errr:
                print("Request Exception:", errr)
                return None

        # create the soup
        soup = bs4.BeautifulSoup(page_contents, "html.parser")

        picture_tags = soup.findAll('picture')

        root_url = response.url.split('/threads/')[0]
        try:
            next_path = soup.nav.select("a.california-page-nav-jump-next")[0].get('href')
        except IndexError:
            next_path = None

        if next_path:
            next_url = root_url + next_path
            pattern = re.compile(url_regex)
            if pattern.search(next_url):
                if next_url not in self.previous_urls:
                    self.next_url = next_url

        for pic in picture_tags:
            print("Photo Found at:", pic.img['data-src'])
            data_url = pic.img['data-src']
            if data_url not in self.previous_pics:
                if "/cdn-cgi/" in data_url:
                    # catching urls formatted like this: /cdn-cgi/image/format=auto,onerror=redirect,width=1920,height=1920,fit=scale-down/http://www.vwvortex.com/john/BBStease2.jpg
                    data_url = data_url.split("fit=scale-down/")[-1]
                try:
                    # get end of the url to determine file type
                    filetype = data_url.split('.')[-1]
                    # request pic url with stream set to true to avoid interruptions
                    pic_stream = requests.get(data_url, stream=True, timeout=10)
                    # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
                    pic_stream.raw.decode_content = True
                    # format file name
                    filename = "{}_{}.{}".format(self.pic_prefix, self.pic_count, filetype)
                    # Open a local file with wb ( write binary ) permission.
                    with open(filename, 'wb') as f:
                        shutil.copyfileobj(pic_stream.raw, f)

                    # prepare for next loop
                    self.previous_pics.append(data_url)
                    self.pic_count += 1
                    print("\tImage successfully downloaded to:", filename)
                except:
                    print("\tFailed to fetch photo.")
            else:
                print("\tPhoto already downloaded, moving on.")

    def validate_url(self) -> bool:
        # verify URL is correctly formatted, if not, raise error
        pattern = re.compile(url_regex)
        if pattern.search(self.start_url):
            return True
        else:
            raise ValueError('URL seems to be incorrectly formatted')

    def validate_path(self) -> bool:
        path_exists = os.path.exists(self.parent_folder)
        if path_exists:
            return True
        if self.create_folders:
            # create the folder if not found
            pathlib.Path(self.parent_folder).mkdir(parents=True, exist_ok=True)
            return True
        else:
            # check if folder/path exists, if not raise error
            raise FileNotFoundError('The specified path does not exist')


### FUNCTIONS ###
if __name__ == '__main__':
    VortexScraper("https://www.vwvortex.com/threads/introducing-the-new-vwvortex-project-car.6916032/",
                  r"C:\Users\taylor\Pictures\VWVortex", "AbeFromanGolfMk2", True)


