import os
import os.path as op
import secrets
import json, boto3, requests
from botocore.client import Config
from botocore.exceptions import ClientError
from my_app import app
# from PIL import Image

S3_BUCKET = app.config['S3_BUCKET']
ACCESS_KEY = app.config['S3_KEY']
SECRET_KEY = app.config['S3_SECRET']

s3_client = boto3.client('s3',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)

def generate_filename(image_file):
    _, f_ext = os.path.splitext(image_file.filename)
    random_hex = secrets.token_hex(8)
    image_filename = random_hex + f_ext
    return image_filename

def save_image(form_image, save_foldername, save_objectname):
    
    image_path = os.path.join(app.root_path, 'static/'+save_foldername, save_objectname)

    # output_size = (200, 200)
    # im = Image.open(form_image)
    # im.thumbnail(output_size)
    # im.save(image_path)

    form_image.save(image_path)

# upload to s3 (need to fix errors)
def post_to_aws_s3(image, save_foldername, save_objectname):
    fields = {
        "acl": "public-read",
        "Content-Type": image.content_type
    }
    conditions = [
        {"acl": "public-read"},
        {"Content-Type": image.content_type}
    ]
    try:
        response = s3_client.generate_presigned_post(
            Bucket=S3_BUCKET,
            Key=save_foldername+'/'+save_objectname,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=600
        )
        #print(response)  
        #print(response['url'])  
        #print(image.content_type)
        image_path = os.path.join(app.root_path, 'static/'+save_foldername, save_objectname)
        #print(image_path)
        with open(image_path, 'rb') as f:
            #files = {'file': ('abc.png', f)}
            files = {'file': (save_objectname, f)}

        #files = {'file': (save_objectname, image.read())}
            http_response = requests.post(response['url'], data=response['fields'], files=files)
        #print(image.read())
    except ClientError as e:
        print("error")