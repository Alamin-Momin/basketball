from flask import Flask, render_template, make_response, send_file, redirect, url_for
from nba_api.stats.endpoints import shotchartdetail
from nba_api.stats.endpoints import playbyplayv2
import requests
import os
import json
import pandas as pd
import numpy as np
import time
from pandas import DataFrame

app = Flask(__name__)

UPLOAD_DIRECTORY = "/files/"

@app.route('/')
def main_page():
    return render_template("home.html")

@app.route('/historical') 
def historical():
    return send_file('files/historical.csv',
        mimetype='text/csv',
        attachment_filename='historical.csv',
        as_attachment=True)
    #resp1 = make_response(df1.to_csv())
    #resp1.headers["Content-Disposition"] = "attachment; filename=historical.csv"
    #resp1.headers["Content-Type"] = "text/csv"
    #return resp1  
  

@app.route('/current', methods=['GET', 'POST'])  
def current():  
    year = "2020-21"

    response = shotchartdetail.ShotChartDetail(
        context_measure_simple = 'FGA',
        team_id = 0,
        player_id = 0,
        season_nullable= year,
        season_type_all_star='Regular Season'
    )

    content = json.loads(response.get_json())

    results = content['resultSets'][0]
    headers = results['headers']
    rows = results['rowSet']
    df = pd.DataFrame(rows)
    df.columns = headers
    df.drop(['GRID_TYPE', 'PERIOD', 'MINUTES_REMAINING', 'SECONDS_REMAINING', "EVENT_TYPE", "TEAM_ID", "SHOT_ZONE_BASIC", "SHOT_ZONE_AREA", "ACTION_TYPE", "SHOT_ZONE_RANGE"], inplace=True, axis=1)
    df['ThreePointer'] = np.where(df['SHOT_TYPE']== '3PT Field Goal', 1, 0)
    df['Season'] = year
    df['Playoffs'] = 0

    response3 = shotchartdetail.ShotChartDetail(
        context_measure_simple = 'FGA',
        team_id = 0,
        player_id = 0,
        season_nullable=year,
        season_type_all_star='Playoffs'
    )

    content3 = json.loads(response3.get_json())

    results1 = content3['resultSets'][0]
    headers1 = results1['headers']
    rows1 = results1['rowSet']
    df1 = pd.DataFrame(rows1)
    if(rows1):
        df1.columns = headers1
        df1.drop(['GRID_TYPE', 'PERIOD', 'MINUTES_REMAINING', 'SECONDS_REMAINING', "EVENT_TYPE", "TEAM_ID", "SHOT_ZONE_BASIC", "SHOT_ZONE_AREA", "ACTION_TYPE", "SHOT_ZONE_RANGE"], inplace=True, axis=1)
        df1['ThreePointer'] = np.where(df1['SHOT_TYPE']== '3PT Field Goal', 1, 0)
        df1['Season'] = year
        df1['Playoffs'] = 1
        df = pd.concat([df, df1])
    df['Assist'] = 0

    df_last_date = pd.read_csv("files/2021.csv")
    column = df_last_date["Game Date"]
    max_value = column.max()

    df3 = df[df['GAME_DATE'] > str(max_value)]
   
    #for i in range(len(df)):
        #date = df.iloc[i]["GAME_DATE"]
        #if date > str(max_value):
            #df3.append(df.iloc[i])

    games = df3.GAME_ID.unique()
    
    for game in games:
        response = playbyplayv2.PlayByPlayV2(
            end_period=0,
            game_id=game,
            start_period=0
        )

        content2 = json.loads(response.get_json())

        results2 = content2['resultSets'][0]
        headers2 = results2['headers']
        rows2 = results2['rowSet']
        df2 = pd.DataFrame(rows2)
        df2.columns = headers2
        
        contain_values = df2[df2['HOMEDESCRIPTION'].str.contains('AST', na=False) | df2['VISITORDESCRIPTION'].str.contains('AST', na=False)]
        for i in range(len(contain_values)):
            play_id = contain_values.iloc[i]["EVENTNUM"]
            df3.loc[(df3['GAME_ID'] == game) & (df3['GAME_EVENT_ID'] == play_id), "Assist"] = 1
        
    df3['TEAM_NAME'] = df3['TEAM_NAME'].str.upper()
    df3["TEAM_NAME"].replace(teams, inplace=True)
    df3["Def Team"] = np.where(df3['TEAM_NAME'] == df3['HTM'], df3['VTM'], df3['HTM'])

    df3.rename(columns={"PLAYER_NAME": "Shooter Name", "TEAM_NAME": "Off Team", "LOC_X": "Shot Location (x)", "LOC_Y": "Shot Location (y)", "GAME_DATE" : "Game Date", "SHOT_MADE_FLAG": "Made", "Assist": "AST", "GAME_ID": "Game ID", "PLAYER_ID": "Player ID"}, inplace=True)
    df_copy = df3.drop(["GAME_EVENT_ID", 'SHOT_TYPE', "SHOT_DISTANCE", "SHOT_ATTEMPTED_FLAG", "HTM", "VTM"], inplace=True, axis=1)
    df_delta = df3[['Game ID', 'Shooter Name', 'Game Date', 'Season', 'Playoffs', 'Off Team', 'Def Team', 'Shot Location (x)', 'Shot Location (y)', 'Made', 'ThreePointer', 'AST']]

    df_updated = pd.concat([df_last_date, df_delta])
    df_updated.to_csv("files/2021.csv", index = False, header=True)

    resp = make_response(df_updated.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=current.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp 

@app.route('/total', methods=['GET', 'POST']) 
def total():
    df_hist = pd.read_csv("files/historical.csv")
    df_current = pd.read_csv("files/2021.csv")

    year = "2020-21"

    response = shotchartdetail.ShotChartDetail(
        context_measure_simple = 'FGA',
        team_id = 0,
        player_id = 0,
        season_nullable= year,
        season_type_all_star='Regular Season'
    )

    content = json.loads(response.get_json())

    time.sleep(1)

    results = content['resultSets'][0]
    headers = results['headers']
    rows = results['rowSet']
    df = pd.DataFrame(rows)
    df.columns = headers
    df.drop(['GRID_TYPE', 'PERIOD', 'MINUTES_REMAINING', 'SECONDS_REMAINING', "EVENT_TYPE", "TEAM_ID", "SHOT_ZONE_BASIC", "SHOT_ZONE_AREA", "ACTION_TYPE", "SHOT_ZONE_RANGE"], inplace=True, axis=1)
    df['ThreePointer'] = np.where(df['SHOT_TYPE']== '3PT Field Goal', 1, 0)
    df['Season'] = year
    df['Playoffs'] = 0

    response3 = shotchartdetail.ShotChartDetail(
        context_measure_simple = 'FGA',
        team_id = 0,
        player_id = 0,
        season_nullable=year,
        season_type_all_star='Playoffs'
    )

    content3 = json.loads(response3.get_json())

    time.sleep(1)

    results1 = content3['resultSets'][0]
    headers1 = results1['headers']
    rows1 = results1['rowSet']
    df1 = pd.DataFrame(rows1)
    if(rows1):
        df1.columns = headers1
        df1.drop(['GRID_TYPE', 'PERIOD', 'MINUTES_REMAINING', 'SECONDS_REMAINING', "EVENT_TYPE", "TEAM_ID", "SHOT_ZONE_BASIC", "SHOT_ZONE_AREA", "ACTION_TYPE", "SHOT_ZONE_RANGE"], inplace=True, axis=1)
        df1['ThreePointer'] = np.where(df1['SHOT_TYPE']== '3PT Field Goal', 1, 0)
        df1['Season'] = year
        df1['Playoffs'] = 1
        df = pd.concat([df, df1])
    df['Assist'] = 0

    column = df_current["Game Date"]
    max_value = column.max()

    df3 = df[df['GAME_DATE'] > str(max_value)]

    #for i in range(len(df)):
        #date = df.iloc[i]["GAME_DATE"]
        #if date > str(max_value):
            #df3.append(df.iloc[i])

    games = df3.GAME_ID.unique()

    for game in games:
        response = playbyplayv2.PlayByPlayV2(
            end_period=0,
            game_id=game,
            start_period=0
        )

        content2 = json.loads(response.get_json())

        results2 = content2['resultSets'][0]
        headers2 = results2['headers']
        rows2 = results2['rowSet']
        df2 = pd.DataFrame(rows2)
        df2.columns = headers2

        contain_values = df2[df2['HOMEDESCRIPTION'].str.contains('AST', na=False) | df2['VISITORDESCRIPTION'].str.contains('AST', na=False)]
        for i in range(len(contain_values)):
            play_id = contain_values.iloc[i]["EVENTNUM"]
            df3.loc[(df3['GAME_ID'] == game) & (df3['GAME_EVENT_ID'] == play_id), "Assist"] = 1

    df3['TEAM_NAME'] = df3['TEAM_NAME'].str.upper()
    df3["TEAM_NAME"].replace(teams, inplace=True)
    df3["Def Team"] = np.where(df3['TEAM_NAME'] == df3['HTM'], df3['VTM'], df3['HTM'])

    df3.rename(columns={"PLAYER_NAME": "Shooter Name", "TEAM_NAME": "Off Team", "LOC_X": "Shot Location (x)", "LOC_Y": "Shot Location (y)", "GAME_DATE" : "Game Date", "SHOT_MADE_FLAG": "Made", "Assist": "AST", "GAME_ID": "Game ID", "PLAYER_ID": "Player ID"}, inplace=True)
    df_copy = df3.drop(["GAME_EVENT_ID", 'SHOT_TYPE', "SHOT_DISTANCE", "SHOT_ATTEMPTED_FLAG", "HTM", "VTM"], inplace=True, axis=1)
    df_delta = df3[['Game ID', 'Shooter Name', 'Game Date', 'Season', 'Playoffs', 'Off Team', 'Def Team', 'Shot Location (x)', 'Shot Location (y)', 'Made', 'ThreePointer', 'AST']]

    df_updated = pd.concat([df_current, df_delta])
    df_updated.to_csv("files/2021.csv", index = False, header=True)
    df_total = pd.concat([df_hist, df_updated])

    resp = make_response(df_total.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=total.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp
    
teams = {"ATLANTA HAWKS" : "ATL",
    "ST. LOUIS HAWKS" : "SLH",
    "MILWAUKEE HAWKS" : "MIL",
    "TRI-CITIES BLACKHAWKS" : "TCB",
    "BOSTON CELTICS" : "BOS",
    "BROOKLYN NETS" : "BKN",
    "NEW JERSEY NETS" : "NJN",
    "CHICAGO BULLS" : "CHI",
    "CHARLOTTE HORNETS" : "CHA",
    "CHARLOTTE BOBCATS" : "CHA",
    "CLEVELAND CAVALIERS" : "CLE",
    "DALLAS MAVERICKS" : "DAL",
    "DENVER NUGGETS" : "DEN",
    "DETROIT PISTONS" : "DET",
    "FORT WAYNE PISTONS" : "FWP",
    "GOLDEN STATE WARRIORS" : "GSW",
    "SAN FRANCISCO WARRIORS" : "SFW",
    "PHILADELPHIA WARRIORS" : "PHI",
    "HOUSTON ROCKETS" : "HOU",
    "INDIANA PACERS" : "IND",
    "LA CLIPPERS" : "LAC",
    "SAN DIEGO CLIPPERS" : "SDC",
    "BUFFALO BRAVES" : "BUF",
    "LOS ANGELES LAKERS" : "LAL",
    "MINNEAPOLIS LAKERS" : "MIN",
    "MEMPHIS GRIZZLIES" : "MEM",
    "VANCOUVER GRIZZLIES" : "VAN",
    "MIAMI HEAT" : "MIA",
    "MILWAUKEE BUCKS" : "MIL",
    "MINNESOTA TIMBERWOLVES" : "MIN",
    "NEW ORLEANS PELICANS" : "NOP",
    "NEW ORLEANS/OKLAHOMA CITY HORNETS" : "NOK",
    "NEW ORLEANS HORNETS" : "NOH",
    "NEW YORK KNICKS" : "NYK",
    "OKLAHOMA CITY THUNDER" : "OKC",
    "SEATTLE SUPERSONICS" : "SEA",
    "ORLANDO MAGIC" : "ORL",
    "PHILADELPHIA 76ERS" : "PHI",
    "SYRACUSE NATIONALS" : "SYR",
    "PHOENIX SUNS" : "PHX",
    "PORTLAND TRAIL BLAZERS" : "POR",
    "SACRAMENTO KINGS" : "SAC",
    "KANSAS CITY KINGS" : "KCK",
    "KANSAS CITY-OMAHA KINGS" : "KCK",
    "CINCINNATI ROYALS" : "CIN",
    "ROCHESTER ROYALS" : "ROR",
    "SAN ANTONIO SPURS" : "SAS",
    "TORONTO RAPTORS" : "TOR",
    "UTAH JAZZ" : "UTA",
    "NEW ORLEANS JAZZ" : "NOJ",
    "WASHINGTON WIZARDS" : "WAS",
    "WASHINGTON BULLETS" : "WAS",
    "CAPITAL BULLETS" : "CAP",
    "BALTIMORE BULLETS" : "BAL",
    "CHICAGO ZEPHYRS" : "CHI",
    "CHICAGO PACKERS" : "CHI",
    "ANDERSON PACKERS" : "AND",
    "CHICAGO STAGS" : "CHI",
    "INDIANAPOLIS OLYMPIANS" : "IND",
    "SHEBOYGAN RED SKINS" : "SRS",
    "ST. LOUIS BOMBERS" : "SLB",
    "WASHINGTON CAPITOLS" : "WAS",
    "WATERLOO HAWKS" : "WAT"
}

if __name__ == '__main__':
    app.debug = True
    app.run()