from bs4 import BeautifulSoup
import requests
import datetime
import os
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString
import xmltodict
from tabulate import tabulate
import pandas as pd

class MubasherAPI:
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

    def _ensure_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    def _validateCountry(self, country):
        if not country in ["eg", "sa", "ae", "qa", "bh", "om", "kw", "jo", "tn", "ma", "ps", "iq"]:
            raise ValueError("wrong country code, please use listCountries to see available country codes")
        return country

    def _GetCompanies(self):
        self._ensure_directory(self.CompaniesDirectory)  # Ensure the directory exists
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
        with open(self.outputFile, "w") as file_object:
            file_object.write(xmlData)

        print("Import complete, saved to : " + self.outputFile)

    def DownloadHistorical(self, company):
        historical_dir = os.path.join(self.HistoricalDirectory, self.country)  # Define full path
        self._ensure_directory(historical_dir)  # Ensure the directory exists

        r = requests.get(company["csv"], allow_redirects=True)
        open(os.path.join(historical_dir, company["symbol"] + ".csv"), 'wb').write(r.content)

    def DownloadAllHistorical(self):
        for company in self.dataBase.values():
            self.DownloadHistorical(company)
            print(company["symbol"] + " data downloaded")

        print("All historical data downloaded successfully to " + self.HistoricalDirectory)
        self.dataDownloaded = True

    def getHistoricalFileWithApi(self,symbol):
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


    def getHistoricalFileWithScraping(self,url):
    html_doc =requests.get(self.HostURL+url)
    bs = BeautifulSoup(html_doc.text, "html.parser")
    historical_file = None
    for item in bs.find_all(lambda tag: any(isinstance(attr, str) and attr.endswith('.csv') for attr in tag.attrs.values())):
      if "historical-data-url" in item.attrs:
        historical_file= item["historical-data-url"]
    return historical_file

    def getHistoricalFile(self,company):
    historical_file = self.getHistoricalFileWithApi(company["symbol"])
    if not historical_file:
      historical_file = self.getHistoricalFileWithScraping(company["url"])
    if historical_file is None:
      raise Exception(f"Historical data for company with symbol {company['symbol']} cannot be imported")
    return historical_file

    
    def LoadCompaines(self):
        self._ensure_directory(self.CompaniesDirectory)  # Ensure the directory exists before loading
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
        print("Companies data loaded successfully!")

    def UpdatePrices(self):
    self.lastPrices = requests.get(self.HostURL+self.PricesAPI,{"country": self.country}).json()
    print("Prices updated successfully to date " + self.lastPrices["lastUpdate"])

    def ListCompanies(self):
    table = tabulate([[company["symbol"],company["name"]]for company in self.dataBase.values()], headers=['Symbol', 'Name'], tablefmt='orgtbl')
    print(table)
    def ListCountries(self):
    table = tabulate([["eg","Egypt"],
                      ["sa","Saudi Arabia"],
                      ["ae","Emirates"],
                      ["qa","Qatar"],
                      ["bh","Bahrin"],
                      ["om","Oman"],
                      ["kw","Kuwait"],
                      ["jo","Jordan"],
                      ["tn","Tunisia"],
                      ["ma","Morocco"],
                      ["ps","Palestine"],
                      ["iq","Iraq"]], headers=['Symbol', 'Name'], tablefmt='orgtbl')
    print(table)


    def GetHistoricalData(self,code,startDate,endDate):

    if self.dataDownloaded:
      Data=pd.read_csv(self.HistoricalDirectory+self.country+"/"+code+".csv",header=None)
    else :
      Data=pd.read_csv(self._GetCompanyByCode(code)["csv"],header=None)

    startDate =self._FormatDate(startDate)
    endDate = self._FormatDate(endDate)
    higher_index = Data[Data[0]==endDate]
    lower_index =Data[Data[0]==startDate]
    if lower_index.empty :
      assert print("there is no record for selected start date, please select another date")
    if higher_index.empty:
      assert print ("there is no record for selected end date, please select another date")
    higher_index = higher_index.index[0]
    lower_index =lower_index.index[0]
    return Data[lower_index:higher_index].values.tolist()


    def _GetCompanyByCode(self,code,no_assert=False):
    if self.dataBase.keys().get(code,None)!= None:
      return self.dataBase[code]
    if no_assert:
      return None
    assert print("Invalid company code, please enter a valid company code")
    def _FormatDate ( self,dateToFormat):

    dateArray = dateToFormat.split("-")
    try:
      returnDate = datetime.datetime(int(dateArray[0]),
                              int(dateArray[1]),
                              int(dateArray[2])).strftime("%Y-%m-%d/%H:%M:%S")
    except :
      assert print ("Invalid date format, please enter a valid date")
    return returnDate

    def SelectCountry(self,contry):
    pass
    if not contry in ["eg","sa","ae","bh","qa","om"]:
      assert print("please select a valid country")
    self.country = country
    self.outputFile =self.CompaniesDirectory+ "companies_database_"+ country+".xml"
    self.HistoricalDirectory = self.ROOT+"historical_data/"+country+"/"
    print("country set to "+country+ ", now getting new selection companies ..")
    self.LoadCompaines()

    def PlotData(dataToPlot):
    fig = go.Figure(data=[go.Candlestick(x=dataToPlot[:][0],
                open=dataToPlot[:][1],
                high=dataToPlot[:][2],
                low=dataToPlot[:][3],
                close=dataToPlot[:][4])])

    fig.show()

    def getAllPrices(self,country):
    response = requests.get(self.HostURL+self.PricesAPI,{"country": self.country}).json()
    date = response['lastUpdate']
    data = {'date':date,'prices':{}}
    for company in response['prices']:
      data['prices'][company['code']]= [company['open'],company['high'],company['low'],company['value'],company['volume']]
    return data

    def updateCompanies(self):
    #get all prices first
    data = self.getAllPrices(self.country)
    for code,price in data['prices'].items():
      #check if file exists
      if not os.path.exists(self.HistoricalDirectory+self.country+"/"+code+".csv"):
        if not self._GetCompanyByCode(code,no_assert=True):
          continue
        self.DownloadHistorical(self.dataBase[code])

      df = pd.read_csv(
          self.HistoricalDirectory+self.country+"/"+code+".csv", header=None)
      df.columns =['date','open','high','low','close','volume']

      if data['date'] in df['date'].values:
        df.loc[df['date'] == data['date'], :] = price
      else:
        df = df.append(pd.Series(price, name=data['date']), ignore_index=True)
      df.to_csv(self.HistoricalDirectory+self.country+"/"+code+".csv", index=False)


if __name__ == "__main__":
  myapi = MubasherAPI("eg")
  myapi.LoadCompaines()
  myapi.updateCompanies()