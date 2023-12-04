import streamlit as st
import pandas as pd
import gspread
import requests
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def search(query, api_key, cse_id, **kwargs):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
    }
    params.update(kwargs)
    response = requests.get(url, params=params)
    return json.loads(response.text)

def main():
    st.title("Google Custom Search API Integration")

    # User input for domain
    site = st.text_input("Enter your domain:")

    # User input for number of URLs
    n = st.number_input("Enter the number of URLs:", min_value=1, step=1, value=10)

    # User input for file name
    worksheet_title = st.text_input("Enter File Name:")

    if st.button("Run"):
        run_script(site, n, worksheet_title)

def run_script(site, n, worksheet_title):
    # Google API key and Custom Search Engine ID
    api_key = "AIzaSyAldBNS7Jy7oFNkMmy0HdSjGo6Qz0Yy0kI"
    cse_id = "d26e2f100f39f43c1"

    # Google Sheets credentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('internal-linking-406006-79de3fe050f5.json', scope)
    gc = gspread.authorize(credentials)

    # Create a new worksheet
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    new_worksheet_title = f'New_Data_{timestamp}'
    worksheet = gc.open(worksheet_title).add_worksheet(new_worksheet_title, rows=1, cols=1)

    # Retrieve data from the original worksheet
    df = pd.DataFrame(gc.open(worksheet_title).get_worksheet(0).get_all_records())

    # Process data and update the new worksheet
    results_df = pd.DataFrame()

    for index, row in df.iterrows():
        query = f"site:{site} \"{row['keyword']}\" -inurl:{row['target_page']}"

        # Initialize an empty list to store links
        link_list = []

        # Number of results to retrieve per request
        results_per_request = 10

        # Number of requests to make
        num_requests = n // results_per_request + (1 if n % results_per_request > 0 else 0)

        st.write(f"Processing row {index + 1} with query: {query}")

        for i in range(num_requests):
            # Calculate the start index for pagination
            start_index = i * results_per_request + 1

            try:
                # Make the API request with the start parameter
                results = search(query, api_key, cse_id, start=start_index)

                # Extract links from the results and append to the link_list
                links = [result.get('link', '') for result in results.get('items', [])]
                link_list.extend(links)

                st.write(f"   Request {i + 1}: Retrieved {len(links)} links")

            except Exception as e:
                st.write(f"   Request {i + 1}: Error in API request - {e}")

        # Ensure the link_list has the required number of links
        link_list = link_list[:n]

        # Pad with empty strings if needed
        while len(link_list) < n:
            link_list.append('')

        results_df = pd.concat([results_df, pd.Series(link_list, name=index)], axis=1)

    results_df = results_df.transpose()
    results_df.columns = [f'link{i+1}' for i in range(n)]
    df = pd.concat([df, results_df], axis=1)
    df = df.fillna('')

    # Clear the new worksheet and update with the data
    worksheet.clear()
    data_records = df.to_dict(orient='records')
    header = df.columns.values.tolist()
    worksheet.append_rows(values=[header] + [list(record.values()) for record in data_records])

    st.write(f"Data has been updated in the new worksheet '{new_worksheet_title}' in Google Sheets.")

if __name__ == "__main__":
    main()
