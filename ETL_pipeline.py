from dotenv import load_dotenv
import os
load_dotenv()
print(os.getenv("DB_PASSWORD"))
import requests
import pandas as pd
import psycopg2
from datetime import datetime
print("THIS IS THE NEW FILE")
# EXTRACT
def extract():
    url = "http://api.open-notify.org/astros.json"
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print(" Extract successful")
        return response.json()
    else:
        raise Exception(f" Extract failed: {response.status_code}")

def transform(data):
    df=pd.DataFrame(data['people'])
    df.columns=['spacecraft','astronaut_name']
    df['extracted_at']=datetime.now()
    print("Transform successful")
    print(df)
    return df
#  LOAD 
def load(df):
    
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    conn.autocommit = False
    cursor = conn.cursor()
    
    extracted_at = df['extracted_at'][0]

    # Step 1 - Load dim_date
    cursor.execute("""
        INSERT INTO dim_date (full_timestamp, day, month, year, hour)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING date_id
    """, (extracted_at, extracted_at.day, extracted_at.month, 
          extracted_at.year, extracted_at.hour))
    date_id = cursor.fetchone()[0]

    # Step 2 - Load dim_astronaut and dim_spacecraft, then fact
    total = len(df)
    print(f"Total rows: {len(df)}")
    for _, row in df.iterrows():
        print(f"Processing: {row['astronaut_name']}")

        # Insert astronaut
        cursor.execute("""
            INSERT INTO dim_astronaut (astronaut_name)
            VALUES (%s)
            ON CONFLICT (astronaut_name) DO NOTHING
            RETURNING astronaut_id
        """, (row['astronaut_name'],))
        result = cursor.fetchone()
        if result:
            astronaut_id = result[0]
        else:
            cursor.execute("SELECT astronaut_id FROM dim_astronaut WHERE astronaut_name = %s", 
                         (row['astronaut_name'],))
            astronaut_id = cursor.fetchone()[0]

        # Insert spacecraft
        cursor.execute("""
            INSERT INTO dim_spacecraft (spacecraft_name)
            VALUES (%s)
            ON CONFLICT (spacecraft_name) DO NOTHING
            RETURNING spacecraft_id
        """, (row['spacecraft'],))
        result = cursor.fetchone()
        if result:
            spacecraft_id = result[0]
        else:
            cursor.execute("SELECT spacecraft_id FROM dim_spacecraft WHERE spacecraft_name = %s", 
                         (row['spacecraft'],))
            spacecraft_id = cursor.fetchone()[0]
        print(f"Inserted: {row['astronaut_name']}")
        # Insert into fact table
        cursor.execute("""
            INSERT INTO fact_sightings (astronaut_id, spacecraft_id, date_id, astronauts_in_space)
            VALUES (%s, %s, %s, %s)
        """, (astronaut_id, spacecraft_id, date_id, total))

    conn.commit()
    cursor.close()
    conn.close()
    print(" Load successful")

data = extract()
df = transform(data)
print("Before load")
load(df)
print("After load")
