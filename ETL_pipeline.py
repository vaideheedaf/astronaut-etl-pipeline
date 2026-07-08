import requests
import pandas as pd
import psycopg2
from datetime import datetime

# ---- EXTRACT ----
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
# ---- LOAD ----
def load(df):
    print("entered load()")
    conn = psycopg2.connect(
        host="localhost",
        database="de_practice",
        user="postgres",
        password="2502"
    )
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO astronauts (spacecraft, astronaut_name, extracted_at)
            VALUES (%s, %s, %s)
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