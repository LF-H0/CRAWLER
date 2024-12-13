import requests                                                             import re
import urllib.parse                                                         import optparse
from threading import Thread
from queue import Queue
import random
import time

banner = """
    88 ----- 8888888   88888888   *888888
    88 V     88        88 -- 88   88
    88 1.0.0 8888888   88 -- 88   88
    88 ----- 88 -----  88 -- 88   88
    88       88 CRAWL  88 -- 88   88
    8888888  88 -----  88888888   °°88888

  -------------- MADE BY LF0 --------------
    """
print(banner)



def get_arguments():
    parser = optparse.OptionParser()
    parser.add_option("-u", "--url", dest="target_url", help="Specify URL, -h for help")
    parser.add_option("-e", "--exclude", dest="exclude_extensions", help="Specify file extensions to exclude (comma-separated)")
    parser.add_option("-o", "--output", dest="output_file", help="Specify output file name")
    parser.add_option("-d", "--depth", dest="crawl_depth", type="int", default=5, help="Specify crawl depth (default: 5)")
    parser.add_option("-t", "--threads", dest="num_threads", type="int", default=10, help="Specify number of threads (default: 10)")
    (options, argumants) = parser.parse_args()

    if not options.target_url:
        print("[-] Please specify URL, -h for help")
        exit()

    return options.target_url, options.exclude_extensions, options.output_file, options.crawl_depth, options.num_threads

target_url, exclude_extensions, output_file, crawl_depth, num_threads = get_arguments()
target_domain = urllib.parse.urlparse(target_url).netloc
target_link = set()
crawled_link = set()

# List of user agents to be used for randomization
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Firefox/90.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Safari/537.36"
]

def get_links(url):
    try:
        # Randomize user agent for each request
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(url, headers=headers, timeout=5)
        return re.findall('(?:href=")(.*?)"', response.content.decode())
    except:
        return []

def crawl(url, depth):
    if depth > crawl_depth:
        return

    href_links = get_links(url)
    for link in href_links:
        link = urllib.parse.urljoin(url, link)

        if "#" in link:
            link = link.split("#")[0]

        if link not in crawled_link:
            crawled_link.add(link)

            # Checking if the link belongs to the target domain
            if urllib.parse.urlparse(link).netloc == target_domain:
                # Checking if the link ends with any of the specified extensions
                if exclude_extensions:
                    exclude_list = exclude_extensions.split(",")
                    if not any(link.endswith(ext.strip()) for ext in exclude_list):
                        target_link.add(link)
                        if output_file:
                            with open(output_file, "a") as file:
                                file.write(link + "\n")
                        else:
                            print(link)
                        crawl(link, depth + 1)
                else:
                    target_link.add(link)
                    if output_file:
                        with open(output_file, "a") as file:
                            file.write(link + "\n")
                    else:
                        print(link)
                    crawl(link, depth + 1)

def worker(queue):
    while True:
        try:
            url, depth = queue.get()
            crawl(url, depth)
            queue.task_done()
            # Changing IP address every 30 seconds
            time.sleep(30)
        except KeyboardInterrupt:
            print("Crawling interrupted. Exiting.")
            break

def main():
    queue = Queue()
    queue.put((target_url, 0))

    for _ in range(num_threads):
        thread = Thread(target=worker, args=(queue,))
        thread.daemon = True
        thread.start()

    queue.join()

    print("Crawling completed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Crawling interrupted. Exiting.")
