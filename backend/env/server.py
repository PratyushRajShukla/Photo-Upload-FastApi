import boto3
import pymongo
import base64
import bson
from bson.binary import Binary
import psycopg2
from typing import List
import uvicorn
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel

S3_BUCKET_NAME = "test-photos-123"



class PhotoModel(BaseModel):
    id: int
    photo_name: str
    photo_url:str
    is_deleted: bool

app = FastAPI(debug=True)

@app.get("/status")
async def check_status():
    return "hello world"

@app.get("/photos", response_model=List[PhotoModel])
async def get_all_photos():
    # DB Connection
    conn=psycopg2.connect(
        database="exampledb", user="docker", password ="docker", host="0.0.0.0"
    )
    cur = conn.cursor()
    cur.execute("SELECT * from photo order by id desc")
    rows = cur.fetchall()

    formatted_photos = []
    for row in rows:
        formatted_photos.append(
            PhotoModel(
                id=row[0], photo_name = row[1], photo_url=row[2], is_deleted=row[3]
            )
        )

    cur.close()
    conn.close()
    return formatted_photos

@app.post("/photos", status_code=201)
async def add_photos(file:UploadFile):
    print("Create endpoint hit!!")
    print(file.filename)
    print(file.content_type)

    # Upload file to AWS S3
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    bucket.upload_fileobj(file.file, file.filename, ExtraArgs={"ACL": "public-read"})

    uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"

    conn = psycopg2.connect(
        database="exampledb", user="docker", password="docker", host="0.0.0.0"
    )
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO photo (photo_name, photo_url) VALUES ('{file.filename}', '{uploaded_file_url}' )"
    )
    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
