import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os

# Read team names and numbers from Excel file
teams_df = pd.read_excel("../Datasets/team_names_numbers.xlsx")

# Define the output file
output_file = "../Datasets/college_hockey_goalie_stats.xlsx"

# Define the range of seasons
seasons = [f"{year}{year + 1}" for year in range(2011, 2024)]

# Load existing data if available
if os.path.exists(output_file):
    existing_df = pd.read_excel(output_file)
    if "Season" in existing_df.columns and "Rk" in existing_df.columns:
        existing_seasons_teams = set(zip(existing_df["Season"], existing_df["Rk"]))
    else:
        print("Warning: 'Season' or 'Rk' column missing in existing file. Available columns:", existing_df.columns)
        existing_seasons_teams = set()
    all_data = [existing_df]
else:
    all_data = []
    existing_seasons_teams = set()

# Columns expected in the table
columns = ["Player", "Team", "Season", "GP", "W", "L", "T", "GA", "SA", "Sv", "SO", "A", "GAA", "SV%", "Min", "Rk"]

# Set up session with cookies for authentication
session = requests.Session()
cookies = {
    "userCode": "24264be98b275e76e7b3086774c4b9fd",
    "userLogin": "btc2628%40g.rit.edu",
    "PHPSESSID": "a652f90237ab50d086ff83b160cfdc6d"
}
session.cookies.update(cookies)

# Iterate through each team and season
for _, row in teams_df.iterrows():
    team_number = row["Rk"]
    team_name = row["Team"]

    for season in seasons:
        if (season, team_number) in existing_seasons_teams:
            print(f"Skipping {team_name} ({team_number}) - Season {season}, already in dataset.")
            continue

        url = f"https://www.collegehockeynews.com/stats/custom/index.php?search_type=goalie_sum&pos=G&season_min={season}&season_max={season}&team={team_number}&game_type%5B%5D=conf&active=0"
        print(f"Fetching data for {team_name} ({team_number}) - Season {season}")

        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the table
            table = soup.find("table")
            if table:
                df = pd.read_html(str(table))[0]
                df.rename(columns={"Season(s)": "Season"}, inplace=True)
                df["Team"] = team_name
                df["Season"] = season
                df["Rk"] = team_number
                all_data.append(df)
            else:
                print(f"No data found for {team_name} ({team_number}) - Season {season}")

        except requests.RequestException as e:
            print(f"Error fetching data for {team_name} ({team_number}) - Season {season}: {e}")

        # Save data periodically to prevent data loss
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df.to_excel(output_file, index=False, columns=final_df.columns.intersection(columns))
            print(f"Data saved to {output_file}")

        time.sleep(1)  # Sleep to prevent overwhelming the server

print("Script execution completed.")
