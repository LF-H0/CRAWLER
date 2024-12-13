import aiohttp
import asyncio
import re
import urllib.parse
import optparse
from bs4 import BeautifulSoup
import random

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
    (options, arguments) = parser.parse_args()

    if not options.target_url:
        print("[-] Please specify URL, -h for help")
        exit()

    return options.target_url, options.exclude_extensions, options.output_file, options.crawl_depth, options.num_threads

target_url, exclude_extensions, output_file, crawl_depth, num_threads = get_arguments()
target_domain = urllib.parse.urlparse(target_url).netloc
target_link = set()
crawled_link = set()

async def get_robots_txt(url):
    parsed_url = urllib.parse.urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(robots_url) as response:
                return await response.text()
    except Exception as e:
        print(f"Error fetching robots.txt: {e}")
        return ""

async def can_crawl(url, robots_txt):
    if not robots_txt:
        return True
    user_agent = "*"
    lines = robots_txt.splitlines()
    for line in lines:
        if line.startswith("User -agent:"):
            user_agent = line.split(":")[1].strip()
        elif line.startswith("Disallow:") and user_agent == "*":
            disallowed_path = line.split(":")[1].strip()
            if url.startswith(urllib.parse.urljoin(target_url, disallowed_path)):
                return False
    return True

async def get_links(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                return [link.get('href') for link in soup.find_all('a', href=True)]
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

async def crawl(url, depth, robots_txt):
    if depth > crawl_depth:
        return

    if not await can_crawl(url, robots_txt):
        print(f"[-] Crawling disallowed by robots.txt: {url}")
        return

    href_links = await get_links(url)
    for link in href_links:
        link = urllib.parse.urljoin(url, link)

        if "#" in link:
            link = link.split("#")[0]

        if link not in crawled_link:
            crawled_link.add(link)

            # Checking if the link belongs to the target domain or subdomains
            if target_domain in urllib.parse.urlparse(link).netloc:
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
                        await crawl(link, depth + 1, robots_txt)
                else:
                    target_link.add(link)
                    if output_file:
                        with open(output_file, "a") as file:
                            file.write(link + "\n")
                    else:
                        print(link)
                    await crawl(link, depth + 1, robots_txt)

async def worker(queue, robots_txt):
    while not queue.empty():
        url, depth = await queue.get()  # Await the get() method
        await crawl(url, depth, robots_txt)
        queue.task_done()
        # Random delay to avoid getting blocked
        await asyncio.sleep(random.uniform(0.5, 1.5))

async def main():
    queue = asyncio.Queue()
    await queue.put((target_url, 0))

    # Fetch robots.txt
    robots_txt = await get_robots_txt(target_url)

    tasks = []
    for _ in range(num_threads):
        task = asyncio.create_task(worker(queue, robots_txt))
        tasks.append(task)

    await queue.join()
    for task in tasks:
        task.cancel()

    print("Crawling completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Crawling interrupted. Exiting.")