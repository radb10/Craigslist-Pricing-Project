import scrapy

LISTINGS_PER_PAGE = 120
PAGES_TO_CRAWL = 1
CITY_PREFIX = 'boston'


class CraigslistItem(scrapy.Item):
    date = scrapy.Field()
    title = scrapy.Field()
    link = scrapy.Field()
    price = scrapy.Field()
    beds = scrapy.Field()
    size = scrapy.Field()
    craigId = scrapy.Field()
    baths = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()
    content = scrapy.Field()


class MySpider(scrapy.Spider):
    name = "craig"
    allowed_domains = ["craigslist.org"]
    base_url = "http://{city}.craigslist.org/search/see/aap?".format(city=CITY_PREFIX)
    start_urls = []

    for i in range(PAGES_TO_CRAWL):
        start_urls.append(base_url + "s=" + str(i * LISTINGS_PER_PAGE))

    def parse(self, response):
        #find all postings
        postings = response.xpath("//li[@class='result-row']")
        #loop through the postings
        for posting in postings:
            item = CraigslistItem()
            #grab craiglist apartment listing ID
            item["craigId"] = int(posting.xpath("@data-pid").extract()[0])

            title_link = posting.xpath(".//a['result-title hdrlnk']")
            item["title"] = ' '.join(title_link.xpath("text()").extract()).strip().replace('\n', '')
            item["link"] = title_link.xpath("@href").extract()[0]

            item["date"] = posting.xpath(".//time[@class='result-date']/@datetime").extract()[0]

            item["price"] = posting.xpath(".//span[@class='result-price'][1]/text()").extract()[0].replace("$", "")

            #Parse request to follow the posting link into the actual post
            request = scrapy.Request(item["link"], callback=self.parse_item_page)
            request.meta['item'] = item
            yield request

    #Parsing method to grab items from inside the individual postings
    def parse_item_page(self, response):
        item = response.meta["item"]

        maplocation = response.xpath("//div[contains(@id,'map')]")
        latitude = ''.join(maplocation.xpath('@data-latitude').extract())
        longitude = ''.join(maplocation.xpath('@data-longitude').extract())
        if latitude:
            item['latitude'] = float(latitude)
        if longitude:
            item['longitude'] = float(longitude)

        attr = response.xpath("//p[@class='attrgroup']")
        try:
            item["beds"] = int(attr.xpath("span/b/text()").extract()[0].lower().replace('br', '').strip())
            item["baths"] = float(attr.xpath("span/b/text()").extract()[1].lower().replace('ba', '').strip())
            item["size"] = int(attr.xpath("span")[1].xpath("b/text()").extract()[0])
        except (ValueError, IndexError):
            pass

        item["content"] = ' '.join(response.xpath("//section[@id='postingbody']")
                                   .xpath("text()").extract()).strip().replace('\n', '')

        return item
