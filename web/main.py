import sys
sys.path.append('/app')

import db.dbwrapper as dbw
import data.polygon as d_poly
import data.alpaca as d_alpaca
import screening.new_records as nr
import models.asset as asset
import models.asset_price as asset_price
import models.strategy as strategy

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="/app/web/static"), name="static")

templates = Jinja2Templates(directory="/app/web/templates")

dbw.initDb()

@app.get("/")
def index(request:Request):
    
    asset_filter = request.query_params.get('filter', False)

    latest_price_date = get_latest_price_date()

    if asset_filter =='new_close_high':
        assets = nr.get_symbols_close_highest_on_date(latest_price_date)
    elif asset_filter =='new_intra_high':
        assets = nr.get_symbols_intra_highest_on_date(latest_price_date)
    elif asset_filter =='new_vol_high':
        assets = nr.get_symbols_intra_highest_on_date(latest_price_date)
    elif asset_filter =='new_intra_low':
        assets = nr.get_symbols_intra_highest_on_date(latest_price_date)
    elif asset_filter =='new_close_low':
        assets = nr.get_symbols_close_lowest_on_date(latest_price_date)
    elif asset_filter =='new_vol_low':
        assets = nr.get_symbols_volume_lowest_on_date(latest_price_date)
    else:
        assets = get_all_active_symbols()
    
    rows = cursor.fetchall()
    
    indicator_values = {}

    # cursor.execute ("""
    #     SELECT symbol, rsi_14, sma_20, sma_50, close
    #     from asset join asset_price on asset_price.asset_id = asset.id
    #     where date = ?;
    # """, (latest_price_date,))

    # indicator_rows = cursor.fetchall()

    # for row in indicator_rows:
    #     indicator_values[row['symbol']] = row

    return templates.TemplateResponse("index.html", {"request": request, "assets": assets, "indicators":indicator_values})

@app.get("/asset/{symbol}")
def asset_details(request:Request, symbol):

    assets = asset.get_all_symbol_data(symbol)
    
    asset_prices = asset_price.get_all_prices_for_symbol(symbol)

    strategies =  get_all_strategies()

    return templates.TemplateResponse("asset.html", {"request": request, "asset": assets, "prices":asset_prices, "strategies":strategies})

@app.post("/apply_strategy")
def apply_strategy(strategy_id:int = Form(...), asset_id:int = Form(...)):

    strategy.register_strategy_for_asset_id(asset_id, strategy_id)

    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code=303)

@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):

    strategy = strategy.get_strategy_by_id()

    assets = strategy.get_all_assets_by_strategy_id(strategy_id)

    return templates.TemplateResponse("strategy.html", {"request": request, "assets": assets, "strategy":strategy})

@app.get("/patterns")
def pattern(request:Request):
    selected_pattern = request.query_params.get('scan',False)
    asset_dict = {}
    if selected_pattern != False:
        
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute("""
            SELECT symbol, name, exchange, max_volume, 'bla2' as pattern  FROM asset 
            join 
            (select asset_id, max(volume) as max_volume from asset_price group by asset_id) as t on t.asset_id = asset.id
            order by max_volume DESC LIMIT 500
        """)
        assets = cursor.fetchall()
        
        for asset in assets:
            asset_dict[asset['symbol']] = {'name':asset['name']}

        #print(asset_dict)
        for asset in asset_dict:
            df = pd.read_sql("""
            SELECT * from asset_price
            JOIN asset on asset.id = asset_price.asset_id
            where asset.symbol = ?
            """, connection, params = [asset])
            pattern_function = getattr(talib, selected_pattern)
            if len(df) > 0:
                try:
                    result = pattern_function(df['open'], df['high'], df['low'], df['close'])
                    last = result.tail(1).values[0]
                    if last > 0:
                        asset_dict[asset][selected_pattern]='bullish'
                    elif last < 0:
                        asset_dict[asset][selected_pattern]='bearish'
                    else:
                        asset[pattern]=None
                except:
                    pass
    return templates.TemplateResponse("pattern.html", {"request": request, "patterns":patterns, "assets":asset_dict, "selected_pattern":selected_pattern})








# @app.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.get("/tradingview_widget")
# async def tradingview_widget(request: Request):
#     return templates.TemplateResponse("tradingview_widget.html", {"request": request})