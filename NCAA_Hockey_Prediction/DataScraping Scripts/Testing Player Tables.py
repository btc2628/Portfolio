import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

SKATER_COLUMNS = ["Name", "Pos", "Yr", "GP", "G", "A", "Pts.", "Pt/GP", "Shots", "Sh%", "PIM", "GWG", "PPG", "SHG",
                  "+/-"]
GOALIE_COLUMNS = ["Name", "Yr", "GP", "W", "L", "T", "GA", "MIN", "GAA", "SH", "SV"]


def scrape_team_stats(season, team_number, team_name):
    url = f"https://www.collegehockeynews.com/stats/team/{team_name}/{team_number}/overall,{season}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for {team_name} in {season}: {e}")
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all("table")
    print(f"Number of tables found for {team_name}: {len(tables)}")

    if len(tables) != 2:
        print(f"Unexpected number of tables found for {team_name} in {season}, skipping...")
        return None, None

    # First table (skaters)
    skater_table = tables[-2]
    skater_rows = [[td.text.strip() for td in tr.find_all("td")] for tr in skater_table.find("tbody").find_all("tr")]

    for row in skater_rows:
        if len(row) > 0:
            name_split = row[0].split(", ")  # Splitting 'Name, Pos, Yr'
            if len(name_split) == 3:
                row[:1] = name_split  # Replace first column with split values
            else:
                row[:1] = [name_split[0], "", ""]  # Handle unexpected formats

    skater_rows = [row[:len(SKATER_COLUMNS)] for row in skater_rows]  # Ensure correct column count
    skater_df = pd.DataFrame(skater_rows, columns=SKATER_COLUMNS)
    skater_df.insert(0, "Season", season)
    skater_df.insert(1, "Team", team_name)
    skater_df.insert(2, "Team Number", team_number)

    # Second table (goalies)
    goalie_table = tables[-1]
    goalie_rows = [[td.text.strip() for td in tr.find_all("td")] for tr in goalie_table.find("tbody").find_all("tr")]

    for row in goalie_rows:
        if len(row) > 0:
            name_split = row[0].split(", ")  # Splitting 'Name, Yr'
            if len(name_split) == 2:
                row[:1] = name_split  # Replace first column with split values
            else:
                row[:1] = [name_split[0], ""]  # Handle unexpected formats

    goalie_rows = [row[:len(GOALIE_COLUMNS)] for row in goalie_rows]  # Ensure correct column count
    goalie_df = pd.DataFrame(goalie_rows, columns=GOALIE_COLUMNS)
    goalie_df.insert(0, "Season", season)
    goalie_df.insert(1, "Team", team_name)
    goalie_df.insert(2, "Team Number", team_number)

    return skater_df, goalie_df


def save_all_teams_to_excel():
    try:
        teams_df = pd.read_excel("../Datasets/team_names_numbers.xlsx")
    except FileNotFoundError:
        print("Error: team_names_numbers.xlsx not found.")
        return

    all_skater_data = []
    all_goalie_data = []
    seasons = [str(year) + str(year + 1) for year in range(2011, 2012)]

    try:
        for _, row in teams_df.iterrows():
            team_number = row["Rk"]
            team_name = row["Team"].replace(" ", "-")

            for season in seasons:
                skater_df, goalie_df = scrape_team_stats(season, team_number, team_name)
                if skater_df is not None:
                    all_skater_data.append(skater_df)
                if goalie_df is not None:
                    all_goalie_data.append(goalie_df)
                time.sleep(2)  # Sleep to avoid rate limiting
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

    # Save partial results
    if all_skater_data:
        final_skater_df = pd.concat(all_skater_data, ignore_index=True)
        final_skater_df.to_excel("../Datasets/team_player_stats.xlsx", index=False)

    if all_goalie_data:
        final_goalie_df = pd.concat(all_goalie_data, ignore_index=True)
        final_goalie_df.to_excel("../Datasets/team_goalie_stats.xlsx", index=False)


# Run the function to scrape data and save to Excel
save_all_teams_to_excel()
