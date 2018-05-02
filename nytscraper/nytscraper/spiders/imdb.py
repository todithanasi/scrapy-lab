# -*- coding: utf-8 -*-
import scrapy
import unidecode
import re

cleanString = lambda x: '' if x is None else unidecode.unidecode(re.sub(r'\s+',' ',x))

class ImdbSpider(scrapy.Spider):
    name = "imdb"
    allowed_domains = ["www.imdb.com"]
    start_urls = ['https://www.imdb.com/title/tt0096463/fullcredits/']

    def parse(self, response):
        results = response.css('#fullcredits_content')
        movieTitleBlock = response.css('#content-2-wide .subpage_title_block').extract_first()
        movieTitleBlock2 = response.css('#content-2-wide .subpage_title_block')
        year = movieTitleBlock2.css('span.nobr')
        rerwerew = results.css("table.cast_list")
        url = rerwerew.css("tr.odd .primary_photo>a::attr(href)").extract_first()
        actorName = rerwerew.css("tr.odd .itemprop").extract_first()
        all = rerwerew.css("tr.odd .itemprop")
        actorPageUrl = all.css('a::attr(href)').extract_first()

        yield {
            'actor_page_url': actorPageUrl,
            'movieTitleBlock': movieTitleBlock,
            'movie_id': '',
            'movie_name': movieTitleBlock,
            'movie_year': cleanString(year.css('::text').extract_first()),
            'actor_name': cleanString(all.css('span.itemprop::text').extract_first()),
            'actor_id': cleanString(all.css('span.itemprop::text').extract_first()),
            'role_name': cleanString(all.css('span.itemprop::text').extract_first()),
       }


    def parse_actor(self, response):

        yield {

        }
