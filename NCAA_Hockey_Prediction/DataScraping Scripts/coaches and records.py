import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os


def get_team_history(team_name, team_number):
    url = f"https://www.collegehockeynews.com/reports/teamHistory/{team_name}/{team_number}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve data for {team_name}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')
    if not table:
        print(f"No table found for {team_name}")
        return None

    data = []
    headers = ["Team", "Team Number", "Season", "Wins", "Losses", "Ties", "Coach"]

    for row in table.find_all("tr")[1:]:  # Skip header row
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        season = cols[0].text.strip()
        season_year = season.split("-")[0]  # Extract only the starting year
        wins = cols[1].text.strip()
        losses = cols[2].text.strip()
        ties = cols[3].text.strip()
        coach = cols[5].text.strip() if len(cols) > 5 else "Unknown"

        data.append([team_name, team_number, season_year, wins, losses, ties, coach])

    return pd.DataFrame(data, columns=headers)


def main():
    input_file = "../Datasets/team_names_numbers.xlsx"  # Input file with team names and numbers
    output_file = "../Datasets/college_hockey_history.xlsx"

    teams_df = pd.read_excel(input_file)
    if os.path.exists(output_file):
        existing_df = pd.read_excel(output_file)
        processed_teams = set(existing_df["Team Number"].unique())
    else:
        existing_df = pd.DataFrame(columns=["Team", "Team Number", "Season", "Wins", "Losses", "Ties", "Coach"])
        processed_teams = set()

    all_data = [existing_df] if not existing_df.empty else []

    try:
        for _, row in teams_df.iterrows():
            team_name = row["Team"]
            team_number = row["Rk"]

            if team_number in processed_teams:
                print(f"Skipping {team_name}, already processed.")
                continue

            print(f"Fetching data for {team_name}...")
            team_data = get_team_history(team_name, team_number)

            if team_data is not None:
                all_data.append(team_data)

            time.sleep(1)  # Be kind to the server and avoid rate limiting
    except Exception as e:
        print(f"Error encountered: {e}. Saving collected data...")
    finally:
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df.to_excel(output_file, index=False)
            print(f"Data saved to {output_file}")
        else:
            print("No data collected.")


if __name__ == "__main__":
    main()
