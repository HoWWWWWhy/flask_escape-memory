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
    aws_secret_access_key=SECRET_KEY,
    config = Config(signature_version = 's3v4')
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
            http_response = requests.post(response['url'], data=response['fields'], files=files)

    except ClientError as e:
        print("error")


def get_from_aws_s3(keys):
    #s3_resource = boto3.resource('s3')
    #my_bucket = s3_resource.Bucket(S3_BUCKET)
    #summaries = my_bucket.objects.all()
    my_objects = []
    for key in keys:
        my_object = {}
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': S3_BUCKET,
                'Key': key
            },                                  
            ExpiresIn=60
        )
        my_object['key'] = key
        my_object['presigned_url'] = url
        my_objects.append(my_object)
        
    #bucket_policy = s3_client.get_bucket_policy(Bucket=S3_BUCKET)

    return my_objects

def get_all_s3_objects(folder_name):
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(S3_BUCKET)
    all_objects = my_bucket.objects.all()
    # folder_name 안의 object 목록만 가져오기
    object_list = [obj.key for obj in all_objects if obj.key.split('/')[0] == folder_name]

    return object_list

def delete_s3_objects(object_list):
    """Delete multiple objects from an Amazon S3 bucket

    :param object_list: list of strings
    :return: True if the referenced objects were deleted, otherwise False
    """

    # Convert list of object names to appropriate data format
    obj_list = [{'Key': obj} for obj in object_list]

    try:
        s3_client.delete_objects(
            Bucket = S3_BUCKET,
            Delete={'Objects': obj_list}
            )

    except ClientError as e:
        print("error")
        return False

    return True