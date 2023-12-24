from bs4 import BeautifulSoup
import requests
import datetime
import os
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
import xmltodict
from tabulate import tabulate
import pandas as pd

class MubasherAPI :
   def __init__(self, country):
       self.ROOT = "content/"
       self.HostURL = "http://www.mubasher.info"
       self.CompaniesAPI = "/api/1/listed-companies"
       self.PricesAPI = "/api/1/stocks/prices/all"
       self.performanceApi = "/api/1/analysis/performance-comparison/stock?query="
       self.HistoricalDirectory = self.ROOT + "historical_data/"
       self.CompaniesDirectory = self.ROOT + "companies_data/"
       self.outputFile = self.CompaniesDirectory + "companies_database_" + country + ".xml"
       self.dataBase = {}
       self.country = self._validateCountry(country)
       self.lastPrices = {}
       self.dataDownloaded = False

   def _validateCountry(self, country):
       if not country in ["eg", "sa", "ae", "qa", "bh", "om", "kw", "jo", "tn", "ma", "ps", "iq"]:
           raise ValueError("wrong country code, please use listCountries to see available country codes")
       return country

   def _GetCompanies(self):
       currentPage = 0
       allPages = 20
       pageSize = 20
       companiesNumber = int(requests.get(self.HostURL + self.CompaniesAPI, params={'country': self.country, 'size': 1}).json()["numberOfPages"])
       while allPages >= currentPage:
           ploads = {'country': self.country, 'size': pageSize, 'start': currentPage * pageSize}
           r = requests.get(self.HostURL + self.CompaniesAPI, params=ploads)
           response = r.json()
           allPages = int(response["numberOfPages"])
           for i in range(len(response["rows"])):
               company = response["rows"][i]
               print("importing companies :" + str(i + currentPage * pageSize) + "/" + str(companiesNumber))
               dataElement = {"name": company["name"],
                             "url": self.HostURL + company["url"],
                             "csv": self.getHistoricalFile(company),
                             "symbol": company["symbol"]}
               self.dataBase[company["symbol"]] = dataElement
           currentPage = currentPage + 1
       xmlData = dicttoxml(self.dataBase.values()).decode()
       if not (os.path.exists(self.CompaniesDirectory)):
           os.mkdir(self.CompaniesDirectory)
       with open(self.outputFile, "w") as file_object:
           file_object.write(xmlData)

       print("Import complete, saved to : " + self.outputFile)

   def DownloadHistorical(self, company):
       if not (os.path.exists(self.HistoricalDirectory)):
           os.mkdir(self.HistoricalDirectory)
           os.mkdir(self.HistoricalDirectory + self.country + "/")
       r = requests.get(company["csv"], allow_redirects=True)
       open(self.HistoricalDirectory + self.country + "/" + company["symbol"] + ".csv", 'wb').write(r.content)

   def DownloadAllHistorical(self):
       if not (os.path.exists(self.HistoricalDirectory)):
           os.mkdir(self.HistoricalDirectory)
           os.mkdir(self.HistoricalDirectory + self.country + "/")

       for company in self.dataBase.values():
           self.DownloadHistorical(company)

           print(company["symbol"] + " data downloaded")

       print("All historical data downloaded successfully to " + self.HistoricalDirectory)
       self.dataDownloaded = True

   def getHistoricalFileWithApi(self, symbol):
       company_data = requests.get(f"{self.HostURL}{self.performanceApi}{symbol}").json()
       company = None
       for c in company_data:
           if c["code"] == symbol:
               company = c
               break
       if company is None:
           return None
       else:
           return company["historicalFile"]

   def getHistoricalFileWithScraping(self, url):
       html_doc = requests.get(self.HostURL + url)
       bs = BeautifulSoup(html_doc.text, "html.parser")
       historical_file = None
       for item in bs.find_all(lambda tag: any(isinstance(attr, str) and attr.endswith('.csv') for attr in tag.attrs.values())):
           if "historical-data-url" in item.attrs:
               historical_file = item["historical-data-url"]
       return historical_file

   def getHistoricalFile(self, company):
       historical_file = self.getHistoricalFileWithApi(company["symbol"])
       if not historical_file:
           historical_file = self.getHistoricalFileWithScraping(company["url"])
       if historical_file is None:
           raise Exception(f"Historical data for company with symbol {company['symbol']} cannot be imported")
       return historical_file

   def LoadCompaines(self):
       if not (os.path.exists(self.outputFile)):
           print("Companies data has not been downloaded yet, starting downloading ..")
           self._GetCompanies()
       f = open(self.outputFile, 'r')
       raw_data = f.read()
       self.dataBase = {}
       for item in xmltodict.parse(raw_data)["root"]["item"]:
           self.dataBase[item["symbol"]["#text"]] = {"name": item["name"]["#text"],
                                                  "symbol": item["symbol"]["#text"],
                                                  "url": item["url"]["#text"],
                                                  "csv": item["csv"]["#text"]}

  def updateCompanies(self):
      if not self.dataDownloaded:
          self.DownloadAllHistorical()
      for company in self.dataBase.values():
          print("Updating company :" + company["symbol"])
          csvFilePath = self.HistoricalDirectory + self.country + "/" + company["symbol"] + ".csv"
          if not os.path.exists(csvFilePath):
              print("Unable to find historical data for company :" + company["symbol"])
              continue
          csvData = pd.read_csv(csvFilePath, parse_dates=[0], index_col=0)
          lastPrice = csvData.iloc[-1]['Close']
          company['lastPrice'] = lastPrice
          self.lastPrices[company["symbol"]] = lastPrice

  def printCompanies(self):
      for company in self.dataBase.values():
          print(company)

if __name__ == "__main__":
   myapi = MubasherAPI("eg")
   myapi.LoadCompaines()
   myapi.updateCompanies()
