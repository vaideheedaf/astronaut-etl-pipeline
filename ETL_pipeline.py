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
    print("entered load()")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        cursor.execute("""
 INSERT INTO astronauts (spacecraft, astronaut_name, extracted_at)
    VALUES (%s, %s, %s)
    ON CONFLICT (astronaut_name)
    DO UPDATE SET
        spacecraft = EXCLUDED.spacecraft,
        extracted_at = EXCLUDED.extracted_at
""", (row['spacecraft'], row['astronaut_name'], row['extracted_at']))
    conn.commit()
    cursor.close()
    conn.close()
    print(" Load successful")
data = extract()
df = transform(data)

print("Before load")
load(df)
print("After load")
