import pandas as pd
import streamlit as st
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
    st.title("Custom Word Search App")

    site = st.text_input("Enter your domain:")
    api_key = "AIzaSyAldBNS7Jy7oFNkMmy0HdSjGo6Qz0Yy0kI"
    cse_id = "d26e2f100f39f43c1"
    n = st.number_input("Enter Number of URLs:", min_value=1, value=1, step=1)

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name('internal-linking-406006-79de3fe050f5.json', scope)
    gc = gspread.authorize(credentials)

    worksheet_title = st.text_input("Enter File Name:")
    
    # Add a "Run" button
    if st.button("Run"):
        spreadsheet = gc.open(worksheet_title)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        new_worksheet_title = f'New_Data_{timestamp}'
        worksheet = spreadsheet.add_worksheet(new_worksheet_title, rows=1, cols=1)

        df = pd.DataFrame(spreadsheet.get_worksheet(0).get_all_records())
        results_df = pd.DataFrame()

        for index, row in df.iterrows():
            query = f"site:{site} {row['keyword']} -inurl:{row['target_page']}"
            results = search(query, api_key, cse_id)
            link_list = [result.get('link', '') for result in results.get('items', [])]

            while len(link_list) < n:
                link_list.append('')

            results_df = pd.concat([results_df, pd.Series(link_list, name=index)], axis=1)

        results_df = results_df.transpose()
        results_df.columns = [f'link{i + 1}' for i in range(n)]
        df = pd.concat([df, results_df], axis=1)
        df = df.fillna('')

        worksheet.clear()
        data_records = df.to_dict(orient='records')
        header = df.columns.values.tolist()
        worksheet.append_rows(values=[header] + [list(record.values()) for record in data_records])

        st.success(f"Data has been updated in the new worksheet '{new_worksheet_title}' in Google Sheets.")

if __name__ == "__main__":
    main()
