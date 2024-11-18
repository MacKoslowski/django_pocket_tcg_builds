# management/commands/scrape_card_images.py
import os
import boto3
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
import time
from urllib.parse import urlparse

class Command(BaseCommand):
   help = 'Scrapes Pokemon card images and uploads to S3'

   def __init__(self):
       super().__init__()
       self.s3 = boto3.client('s3',
           aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
           aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
       )
       self.bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')

   def handle(self, *args, **options):
       sets = [
           ('A1', range(1, 288)),
           ('P-A', range(1, 25))
       ]

       for set_code, number_range in sets:
           for number in number_range:
               url = f"https://pocket.limitlesstcg.com/cards/{set_code}/{number}"
               try:
                   response = requests.get(url)
                   response.raise_for_status()
                   soup = BeautifulSoup(response.text, 'html.parser')
                   
                   # Find card image
                   img_tag = soup.select_one('.card-image img')
                   if img_tag and img_tag.get('src'):
                       img_url = img_tag['src']
                       
                       # Download image
                       img_response = requests.get(img_url)
                       if img_response.status_code == 200:
                           # Generate S3 key from URL
                           filename = os.path.basename(urlparse(img_url).path)
                           s3_key = f'card_images/{set_code}/{filename}'
                           
                           # Upload to S3
                           self.s3.put_object(
                               Bucket=self.bucket_name,
                               Key=s3_key,
                               Body=img_response.content,
                               ContentType='image/webp'
                           )
                           
                           self.stdout.write(
                               self.style.SUCCESS(
                                   f'Successfully uploaded {set_code}/{number} to {s3_key}'
                               )
                           )
                           
                       time.sleep(1)  # Be nice to the server
               
               except Exception as e:
                   self.stdout.write(
                       self.style.ERROR(f'Error with {set_code}/{number}: {str(e)}')
                   )
                   continue