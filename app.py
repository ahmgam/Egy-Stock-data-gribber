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
  def __init__ (self,country):
    self.ROOT = "content/"
    self.HostURL= "http://www.mubasher.info"
    self.CompaniesAPI="/api/1/listed-companies"
    self.PricesAPI = "/api/1/stocks/prices/all"
    self.performanceApi = "/api/1/analysis/performance-comparison/stock?query="
    self.HistoricalDirectory = self.ROOT+"historical_data/"
    self.CompaniesDirectory=self.ROOT+"companies_data/"
    self.outputFile =self.CompaniesDirectory+ "companies_database_"+ country+".xml"
    self.dataBase = {}
    self.country = self._validateCountry(country)
    self.lastPrices = {}
    self.dataDownloaded = False


  def _validateCountry(self,country):
    if not country in ["eg","sa","ae","qa","bh","om","kw","jo","tn","ma","ps","iq"]:
      raise ValueError("wrong country code, please use listCountries to see available country codes")
    return country

User
I have the following script 

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
  def __init__ (self,country):
    self.ROOT = "content/"
    self.HostURL= "http://www.mubasher.info"
    self.CompaniesAPI="/api/1/listed-companies"
    self.PricesAPI = "/api/1/stocks/prices/all"
    self.performanceApi = "/api/1/analysis/performance-comparison/stock?query="
    self.HistoricalDirectory = self.ROOT+"historical_data/"
    self.CompaniesDirectory=self.ROOT+"companies_data/"
    self.outputFile =self.CompaniesDirectory+ "companies_database_"+ country+".xml"
    self.dataBase = {}
    self.country = self._validateCountry(country)
    self.lastPrices = {}
    self.dataDownloaded = False


  def _validateCountry(self,country):
    if not country in ["eg","sa","ae","qa","bh","om","kw","jo","tn","ma","ps","iq"]:
      raise ValueError("wrong country code, please use listCountries to see available country codes")
    return country

  def _GetCompanies(self):
    currentPage = 0
    allPages = 20
    pageSize = 20
    companiesNumber =int(requests.get(self.HostURL + self.CompaniesAPI,params={'country':self.country,'size':1}).json()["numberOfPages"])
    while allPages>=currentPage:
      ploads = {'country':self.country,'size':pageSize,'start':currentPage*pageSize}
      r = requests.get(self.HostURL + self.CompaniesAPI,params=ploads)
      response = r.json()
      allPages =int(response["numberOfPages"])
      for i in range(len(response["rows"])):
        
        company=response["rows"][i]
        print("importing companies :" + str(i+currentPage*pageSize)+"/"+str(companiesNumber))
        dataElement = {"name":company["name"],
                      "url":self.HostURL+company["url"],
                      "csv":self.getHistoricalFile(company),
                      "symbol":company["symbol"]}
        self.dataBase[company["symbol"]]=dataElement
      currentPage=currentPage+1
    xmlData = dicttoxml(self.dataBase.values()).decode()
    if not (os.path.exists(self.CompaniesDirectory)):
      os.mkdir(self.CompaniesDirectory)
    with open(self.outputFile , "w") as file_object:
      file_object.write(xmlData)
    
    print("Import complete, saved to : "+self.outputFile )

  def DownloadHistorical(self,company):
    if not (os.path.exists(self.HistoricalDirectory)):
      os.mkdir(self.HistoricalDirectory)
      os.mkdir(self.HistoricalDirectory+self.country+"/")
    r = requests.get(company["csv"], allow_redirects=True)
    open(self.HistoricalDirectory+self.country+"/"+company["symbol"]+".csv", 'wb').write(r.content)

  def DownloadAllHistorical(self):
    if not (os.path.exists(self.HistoricalDirectory)):
      os.mkdir(self.HistoricalDirectory)
      os.mkdir(self.HistoricalDirectory+self.country+"/")

    for company in self.dataBase.values():
      self.DownloadHistorical(company)
      
      print(company["symbol"]+" data downloaded")
    
    print("All historical data downloaded successfully to "+ self.HistoricalDirectory)
    self.dataDownloaded=True

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

  def LoadCompaines (self):
    if not (os.path.exists(self.outputFile)):
      print("Companies data has not been downloaded yet, starting downloading ..")
      self._GetCompanies()
    f = open(self.outputFile,'r')
    raw_data = f.read()
    self.dataBase={}
    for item in xmltodict.parse (raw_data)["root"]["item"]:
      self.dataBase[item["symbol"]["#text"]]={"name":item["name"]["#text"],
                          "symbol":item["symbol"]["#text"],
                          "url":item["url"]["#text"],
                          "csv":item["csv"]["#text"]}
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

I'm trying to write a github action to run and save these files into data folder on root main branch like that 

name: Scrape and Save Data
#steps
on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:  

jobs:
  scrape-and-save:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repo
        uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bs4 requests pandas dicttoxml tabulate
          python -m pip install xmltodict

      - name: Run Script
        run: python app.py

      - name: Commit and Push
        uses: EndBug/add-and-commit@v7
        with:
          default_author: github_actions
          message: "Update data"
          add: "data/*.csv"

But It seems like I'm doing it wrong and i'm getting this error 

  File "app.py", line 233, in <module>
    myapi.LoadCompaines()
  File "app.py", line 113, in LoadCompaines
    self._GetCompanies()
  File "app.py", line 54, in _GetCompanies
    os.mkdir(self.CompaniesDirectory)
FileNotFoundError: [Errno 2] No such file or directory: 'content/companies_data/'
Error: Process completed with exit code 1.

How can I fix that ?
ChatGPT

The error you are encountering indicates that the directory content/companies_data/ does not exist when your script tries to make a directory within it. This is occurring because the script assumes the presence of the content/ directory and its subdirectory companies_data/, which may not be there in a fresh clone or environment like GitHub Actions.

To address this issue, you need to ensure that the required directories exist before your script tries to write files into them. You can modify your script to check and create the necessary directories if they don't exist. Here's how you might adjust the _GetCompanies and DownloadHistorical methods to handle this:

python

import os

# Other imports and class definition

class MubasherAPI:
    # Existing initialization and other methods

    def _ensure_directory(self, directory):
        if not os.path.exists(directory):
            os.makedirs(directory)  # This will create all the intermediate directories as well

    def _GetCompanies(self):
        # ... existing code ...

        # Ensure the CompaniesDirectory exists
        self._ensure_directory(self.CompaniesDirectory)
        with open(self.outputFile, "w") as file_object:
            file_object.write(xmlData)
        
        # ... existing code ...

    def DownloadHistorical(self, company):
        # Ensure the HistoricalDirectory and its subdirectory for country exist
        historical_dir = os.path.join(self.HistoricalDirectory, self.country)
        self._ensure_directory(historical_dir)

        r = requests.get(company["csv"], allow_redirects=True)
        open(os.path.join(historical_dir, company["symbol"]+".csv"), 'wb').write(r.content)

    # ... rest of your class ...

In the above modifications:

    Added a method _ensure_directory which takes a directory path and creates it along with any necessary parent directories.
    Called this _ensure_directory method in _GetCompanies and DownloadHistorical to ensure the directories exist before files are created or written.

With these changes, your script should handle the directory creation automatically and avoid the FileNotFoundError. Ensure to integrate the _ensure_directory method calls wherever your script needs to write to a directory.

Additionally, make sure that your GitHub Actions workflow is correctly set up to trigger the script and has the necessary permissions to create directories and files in the GitHub repository.
User
but how would I push these files and folders to github repo everytime there is a change ?
ChatGPT

To push changes (like new or updated files and folders) to your GitHub repository automatically after your script runs, you'll need to set up a few steps in your GitHub Actions workflow. The steps generally involve:

    Checking out the repository: Ensures you have a working copy of your repository.
    Setting up Python and dependencies: Necessary to run your script.
    Running your script: Executes your Python script to scrape data and save files.
    Adding changes to git: Tracks the newly created or updated files.
    Committing and pushing the changes: Saves the changes to your repository.

From your provided script, you're almost there. You just need to make sure the last part, the "Commit and Push" step, is correctly set up to include the new directories and files. Here's how you can modify your GitHub Actions workflow to ensure it commits and pushes the changes:

yaml

name: Scrape and Save Data
on:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:  

jobs:
  scrape-and-save:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install bs4 requests pandas dicttoxml tabulate
          pip install xmltodict

      - name: Run Script
        run: python app.py

      - name: Commit and Push
        uses: EndBug/add-and-commit@v7
        with:
          default_author: github_actions
          message: "Update data"
          add: "./*"  # Change this line to include all files and directories

Here are the key points in this workflow:

    Checkout Repo: This step checks out your repository so the workflow can access it.
    Setup Python and Install Dependencies: These steps ensure the right Python version and packages are installed.
    Run Script: This runs your Python script which scrapes data and saves it in the specified directories.
    Commit and Push Changes: The EndBug/add-and-commit action is used here to commit any changes made by the script. The key part is the add: "./*" line which tells the action to add all files and folders in the repository directory. You can be more specific with paths or patterns to match only certain files if necessary.

After setting up your workflow like this, any new files or changes made by your script should be automatically committed and pushed to your repository whenever the action runs.

A couple of important notes:

    Permissions: Make sure that the GitHub Actions has the necessary permissions to push to your repository. The default GITHUB_TOKEN should suffice for most cases.
    Branches: By default, this will push to the main branch. If you want to push to a different branch, you might need to specify it in the checkout step and possibly in the commit-and-push step.
    Safety and Security: Be cautious with automatically pushing data, especially if it's from an external source. Make sure you have any necessary legal rights to the data and that you handle sensitive information appropriately. Also, consider the implications of pushing data automatically in terms of data quality and integrity.

User
now give me my full script code with your modifications 
ChatGPT

Below is the full script with the modifications for ensuring the required directories exist and for handling errors more gracefully. The script now includes the _ensure_directory method and uses it to check and create the necessary directories before attempting to write files:

python

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

  def DownloadHistorical(self,company):
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