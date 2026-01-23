import requests
from bs4 import BeautifulSoup
import pandas as pd
import time as time

SKATER_COLUMNS = ["Name", "Pos", "Yr", "GP", "G", "A", "Pts.", "Pt/GP", "Shots", "Sh%", "PIM", "GWG", "PPG", "SHG", "+/-"]
GOALIE_COLUMNS = ["Name", "Yr", "GP", "W", "L", "T", "GA", "MIN", "GAA", "SH", "SV"]

def split_skater_name_column(df):
    df[['Name', 'Pos', 'Yr']] = df['Name, Yr'].str.split(', ', expand=True, n=2)
    return df.drop(columns=['Name, Yr'])

def split_goalie_name_column(df):
    df[['Name', 'Yr']] = df['Name, Yr'].str.split(', ', expand=True, n=1)
    return df.drop(columns=['Name, Yr'])

def scrape_team_stats(season, team_number, team_name):
    url = f"https://www.collegehockeynews.com/stats/team/{team_name}/{team_number}/overall,{season}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data for {team_name} in {season}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all("table")
    print(f"Number of tables found: {len(tables)}")

    if len(tables) < 2:
        print(f"Incorrect tables found for {team_name} in {season}")
        return None, None

    # First table (skaters)
    skater_table = tables[-2]
    skater_headers = [th.text.strip() for th in skater_table.find("thead").find_all("th")]
    skater_rows = [[td.text.strip() for td in tr.find_all("td")] for tr in skater_table.find("tbody").find_all("tr")]
    print(skater_table)
    skater_df = pd.DataFrame(skater_rows, columns=skater_headers)
    skater_df = split_skater_name_column(skater_df)
    skater_df = skater_df.reindex(columns=SKATER_COLUMNS, fill_value="")
    skater_df.insert(0, "Season", season)
    skater_df.insert(1, "Team", team_name)

    # Second table (goalies)
    goalie_table = tables[-1]
    goalie_headers = [th.text.strip() for th in goalie_table.find("thead").find_all("th")]
    goalie_rows = [[td.text.strip() for td in tr.find_all("td")] for tr in goalie_table.find("tbody").find_all("tr")]
    goalie_df = pd.DataFrame(goalie_rows, columns=goalie_headers)
    goalie_df = split_goalie_name_column(goalie_df)
    goalie_df = goalie_df.reindex(columns=GOALIE_COLUMNS, fill_value="")
    goalie_df.insert(0, "Season", season)
    goalie_df.insert(1, "Team", team_name)

    return skater_df, goalie_df

def save_all_teams_to_excel():
    teams_df = pd.read_excel("../Datasets/team_names_numbers.xlsx")
    all_skater_data = []
    all_goalie_data = []
    seasons = [str(year) + str(year + 1) for year in range(2012, 2013)]

    for _, row in teams_df.iterrows():
        team_number = row["Rk"]
        team_name = row["Team"].replace(" ", "-")

        for season in seasons:
            skater_df, goalie_df = scrape_team_stats(season, team_number, team_name)
            if skater_df is not None:
                all_skater_data.append(skater_df)
            if goalie_df is not None:
                all_goalie_data.append(goalie_df)
        time.sleep(13)


    if all_skater_data:
        final_skater_df = pd.concat(all_skater_data, ignore_index=True)
        final_skater_df.to_excel("../Datasets/team_player_stats.xlsx", index=False)

    if all_goalie_data:
        final_goalie_df = pd.concat(all_goalie_data, ignore_index=True)
        final_goalie_df.to_excel("../Datasets/team_goalie_stats.xlsx", index=False)

# Run the function to scrape data and save to Excel
save_all_teams_to_excel()
