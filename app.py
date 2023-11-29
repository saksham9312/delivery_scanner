from flask import Flask
from nsepython import *
from datetime import datetime, timedelta
from mongo_config import *
import time
# import json
import pymongo
app = Flask(__name__)



def get_last_15th_day():
    # Get the current date and time
    current_date = datetime.now()

    # Subtract 15 days from the current date
    fifteen_days_ago = current_date - timedelta(days=15)

    # Format the date as DD-MM-YYYY
    formatted_date = fifteen_days_ago.strftime('%d-%m-%Y')

    return formatted_date




def fetchFnO():
  data = nsefetch('https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O')

  if 'data' in data:
    symbol_names = [item['symbol'] for item in data['data']]
    return symbol_names
  else:
    print("Error: 'data' key not found in the response JSON.")
    return False

def compareDelPerc(symbol, from_date, to_date):
  base_url = "https://www.nseindia.com/api/historical/r"
  url = f"{base_url}?from={from_date}&to={to_date}&symbol={symbol}&dataType=priceVolumeDeliverable&series=ALL" 

  try:
    response = nsefetch(url)
    if(response.status_code == 200):
      data = response.get("data", [])

    #   current_formatted_date = datetime.now().strftime("%d-%b-%Y")
      current_formatted_date = '28-Nov-2023'
      latest_data = [entry for entry in data if entry.get("mTIMESTAMP") == current_formatted_date]
      
      if not latest_data:
        print('No data for the latest mTIMESTAMP: '+symbol)
        return
      
      latest_cop_deliv_perc = latest_data[0].get("COP_DELIV_PERC", 0) 
      max_previous_cop_deliv_perc = max([entry.get("COP_DELIV_PERC", 0) for entry in data if entry.get("mTIMESTAMP") != current_formatted_date])

      result = latest_cop_deliv_perc > max_previous_cop_deliv_perc
      avg_cop_deliv_perc = sum([entry.get("COP_DELIV_PERC", 0) for entry in data]) / len(data) if data else 0

      latest_last_traded_price = latest_data[0].get("CH_LAST_TRADED_PRICE", 0)
      latest_tot_traded_qty = latest_data[0].get("CH_TOT_TRADED_QTY", 0)

      if result:
        stock_data = {
          "symbol": symbol,
          "ltp": latest_last_traded_price,
          "volume": latest_tot_traded_qty,
          "avgDelPerc": avg_cop_deliv_perc,
          "currentDelPerc": latest_cop_deliv_perc,
          "date": current_formatted_date
        }
        stocks.insert_one(stock_data);
        time.sleep(5)
        return True
      else:
        time.sleep(5)
        return False
    
    else:
      print(f"Error in fetching data: {response.status_code} - {response.text}")

  except Exception as e:
    print(f"Error in fetching: {str(e)}: "+symbol)
      

       



@app.route("/")
def hello():
    from_date = get_last_15th_day()
    to_date = datetime.now().strftime('%d-%m-%Y')
    symbol_names = fetchFnO()
    for stock in symbol_names:
        compareDelPerc(stock, from_date, '28-11-2023')
    # cursor = stocks.find().sort("currentDelPerc", pymongo.DESCENDING)
    # documents = list(cursor)
    # # json_data = json.dumps(documents, default=str)
    return {"data": "OK"}

if __name__ == "__main__":
  app.run(port=8000, debug=True)