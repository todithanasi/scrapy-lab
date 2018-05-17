# -*- coding: utf-8 -*-
import scrapy
import unidecode
import re
import os
import uuid
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

cleanString = lambda x: '' if x is None else unidecode.unidecode(re.sub(r'\s+',' ',x))



ELASTIC_API_URL_HOST = os.environ['ELASTIC_API_URL_HOST']
ELASTIC_API_URL_PORT = os.environ['ELASTIC_API_URL_PORT']
ELASTIC_API_USERNAME = os.environ['ELASTIC_API_USERNAME']
ELASTIC_API_PASSWORD = os.environ['ELASTIC_API_PASSWORD']

es=Elasticsearch(host=ELASTIC_API_URL_HOST,
                 scheme='https',
                 port=ELASTIC_API_URL_PORT,
                 http_auth=(ELASTIC_API_USERNAME,ELASTIC_API_PASSWORD))



class ImdbSpider(scrapy.Spider):
    name = "imdb"
    allowed_domains = ["www.imdb.com"]
    start_urls = ['https://www.imdb.com/title/tt0096463/fullcredits/']

    domain = "www.imdb.com"



    movieFullCreditsUrl = ""




    def parse(self, response):

        results = response.css('#fullcredits_content')

        # Movie data
        movieInfo = response.css('div.subpage_title_block')
        movieYear = unidecode.unidecode(
            re.sub(r'\s+', ' ', cleanString(movieInfo.css('span.nobr::text').extract_first()))).strip()[1:5]

        if(response.meta.get('movie_year', ) and len(str(response.meta['movie_year'])) > 0):
            movieYear = response.meta['movie_year']
        movieName = movieInfo.css('.parent a::text').extract_first().strip()
        movieUrl = movieInfo.css('a::attr(href)').extract_first()
        movieId = movieUrl.split("/")[2].strip()

        self.movieFullCreditsUrl = self.domain + movieUrl.split("?")[0] + "fullcredits/"

        # Actor data
        castList = results.css("table.cast_list")

        totalNrCast = len(castList.css("tr td.itemprop").extract())

        actorPageUrl = castList.css('tr .itemprop a::attr(href)').extract_first()

        for item in range(0,totalNrCast):
            actorId = castList.css('tr .itemprop a::attr(href)')[item].extract().split("/")[2].strip()
            actorName = cleanString(castList.css('tr .itemprop span.itemprop::text')[item].extract()).strip()
            # Role name missing when it is tr .character a::text
            roleName = cleanString(castList.css('tr .character::text')[item].extract()).strip()
            actorBioUrl = castList.css('tr .itemprop a::attr(href)')[item].extract().split("?")[0] + "bio/"

            next_page = actorBioUrl
            if next_page is not None:
                 yield response.follow(next_page, callback=self.parse_actor_bio, meta={'movie_id': movieId, 'movie_name': movieName, 'movie_year':movieYear,
                                                                                       'actor_name':actorName, 'actor_id':actorId, 'role_name':roleName})

        if  actorPageUrl is not None:
            yield response.follow(actorPageUrl, callback=self.parse_actor,
                                  meta={'movie_id': movieId, })





    def parse_actor(self, response):

        allMovies = response.css('div.filmo-category-section')[0]
        totalNrMovies = len(allMovies.css('div span.year_column::text').extract())
        for item in range(0,totalNrMovies):
            year = unidecode.unidecode(
                re.sub(r'\s+', ' ', cleanString(allMovies.css('div span.year_column::text')[item].extract()))).strip()
            if(len(year) > 3):
                year = int(year[0:4])
            else:
                year = 0
            if(year > 1979 and year < 1990):
                movieUrl = allMovies.css('b a::attr(href)')[item].extract()
                movieId = movieUrl.split("/")[2].strip()
                if(movieId !=  response.meta['movie_id']):
                    movieFullCreditsUrl = movieUrl.split("?")[0] + "fullcredits/"

                    if movieFullCreditsUrl is not None:
                        yield response.follow(movieFullCreditsUrl, callback=self.parse, meta={'movie_year':year})



    def parse_actor_bio(self, response):
        results = response.css('table#overviewTable.dataTable.labelValueTable')
        allBioRaws = results.css('td').extract()
        birthdate = results.css('time::attr(datetime)').extract_first()
        birthName = ""
        height = ""
        for index, raw in enumerate(allBioRaws):
            if raw.find('Height') != -1:
                if len(allBioRaws) > index:
                    height =  unidecode.unidecode(re.sub(
                        r'\s+',' ',BeautifulSoup(allBioRaws[index + 1], "html.parser").select("td")[0].get_text())).strip()
            if raw.find('Birth Name') != -1:
                birthName = unidecode.unidecode(
                    re.sub(r'\s+', ' ', BeautifulSoup(allBioRaws[index + 1], "html.parser").select("td")[0].get_text())).strip()
        yield {
        'movie_id': response.meta['movie_id'],
        'movie_name': response.meta['movie_name'],
        'movie_year': response.meta['movie_year'],
        'actor_name': response.meta['actor_name'],
        'actor_id': response.meta['actor_id'],
        'role_name': response.meta['role_name'],
        'birthdate': birthdate,
        'birth_name': birthName,
        'height': height,
        }

        # es.index(index='imdb',
        #          doc_type='movies',
        #          id=uuid.uuid4(),
        #          body={
        #             'movie_id': response.meta['movie_id'],
        #             'movie_name': response.meta['movie_name'],
        #             'movie_year': response.meta['movie_year'],
        #             'actor_name': response.meta['actor_name'],
        #             'actor_id': response.meta['actor_id'],
        #             'role_name': response.meta['role_name'],
        #             'birthdate': birthdate,
        #             'birth_name': birthName,
        #             'height': height,
        #          })

        # next_page = self.actorPageUrl
        # if next_page is not None:
        #     yield response.follow(next_page, callback=self.parse_actor)
