import base64
import boto3
import json
import os
from botocore.exceptions import ClientError
from subprocess import call
import sqlite3

#
#
#
#
#
#
sql = sqlite3.connect('ohaifaces.db')

DEFAULT_BUCKET = 'ohaibucket'
DEFAULT_COLLECTION = "ohaicollection"
REALLY_DEFAULT_SNAP_FILE = "ohai.jpg"

BUCKET = os.getenv('BUCKET', DEFAULT_BUCKET)
FEATURES_BLACKLIST = ("Landmarks", "Emotions", "Pose", "Quality", "BoundingBox", "Confidence")
REGION = os.getenv("AWS_DEFAULT_REGION", 'us-west-2')
COLLECTION = os.getenv('COLLECTION', DEFAULT_COLLECTION)
DEFAULT_SNAP_FILE = os.getenv('DEFAULT_SNAP_FILE', REALLY_DEFAULT_SNAP_FILE)

rekognition = boto3.client("rekognition", REGION)

if os.uname()[0] == "Darwin":
    DEFAULT_CAMERA = "isight"
elif os.uname()[0] == "Linux":
    # DEFAULT_CAMERA = "pi"
    DEFAULT_CAMERA = "ps3"

try:
    rekognition.create_collection(CollectionId=COLLECTION)
except ClientError as e:
    if e.response['Error']['Code'] == "ResourceAlreadyExistsException":
        pass
    else:
        raise()

def take_snapshot(camera="isight"):
    if camera == "isight":
        returncode = call(["imagesnap", DEFAULT_SNAP_FILE])
    elif camera == 'pi':
        from picamera import PiCamera
        camera = PiCamera()
        camera.capture(DEFAULT_SNAP_FILE)
    elif camera == 'ps3':
        returncode = (call(['fswebcam', '-r', '640x480', '-S', '3', '--jpeg', '70',
            '--no-banner', '--save', DEFAULT_SNAP_FILE]))
    else:
        returncode = None
    return returncode

def upload_snapshot(path_to_snapshot, filename):
    client = boto3.client('s3')
    client.upload_file(path_to_snapshot, BUCKET, filename)

def detect_faces_from_s3(bucket, key, attributes=['ALL'], REGION=REGION):
    response = rekognition.detect_faces(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        Attributes=attributes,
    )
    return response['FaceDetails']

def detect_faces_from_bytes(file_bytes, attributes=['ALL']):
    response = rekognition.detect_faces(
        Image={
            "Bytes": file_bytes
        },
        Attributes=attributes,
    )
    return response['FaceDetails']

#take_snapshot("isight")
def get_snap_data(filename=DEFAULT_SNAP_FILE):
    with  open(filename, "r") as snap_file:
        return snap_file.read()

class TooManyFaces(Exception):
    def __init__(self):
        # type: () -> None
        self.err = err(401, "Too Many Faces")


class NoFaces(Exception):
    def __init__(self):
        # type: () -> None
        self.err = err(501, "No Faces Found")


def verify_snapshot(filename=DEFAULT_SNAP_FILE, snap_data=None):
    if not snap_data:
	with  open(filename, "r") as snap_file:
            snap_data = snap_file.read()
    faces_data = detect_faces_from_bytes(snap_data)
    if faces_data:
        #print(json.dumps(faces_data, indent=4, sort_keys=True))
        #print(len(faces_data))
        # if len(faces_data) == 1:
        print("Ohai")
        return faces_data
        #else:
        #    print("Too many people.. no more spoons!!!")
        #    raise TooManyFaces
    else:
        print("Beware the faceless man")
        return False
        #raise NoFaces

def index_faces(bucket, key, collection_id=COLLECTION, image_id=None, attributes=(), REGION=REGION):
    rekognition = boto3.client("rekognition", REGION)
    response = rekognition.index_faces(
        Image={
            "S3Object": {
                "Bucket": bucket,
                "Name": key,
            }
        },
        CollectionId=collection_id,
        ExternalImageId=image_id,
        DetectionAttributes=attributes,
    )
    return response['FaceRecords']

def index_face(filename=DEFAULT_SNAP_FILE, snap_data=None, collection_id=COLLECTION, image_id=None, attributes=(), REGION=REGION):
    with open(filename, "r") as snap_file:
        snap_data = snap_file.read()
    response = rekognition.index_faces(
        Image={
            "Bytes": snap_data
        },
        CollectionId=collection_id,
        #ExternalImageId=image_id,
        DetectionAttributes=attributes,
    )
    return response['FaceRecords']

def find_face(filename=DEFAULT_SNAP_FILE, snap_data=None):
    with open(filename, "r") as snap_file:
        snap_data = snap_file.read()
    response = rekognition.search_faces_by_image(
        CollectionId=COLLECTION,
        Image={
            "Bytes": snap_data
        }
    )
    return response['FaceMatches']

def import_new_face(camera=DEFAULT_CAMERA):
    take_snapshot(camera)
    faces_data = verify_snapshot()
    if faces_data:
        if len(faces_data) == 1:
            return index_face()
        else:
            raise TooManyFaces
    else:
        raise NoFaces

def find_new_face(camera=DEFAULT_CAMERA):
    # Take a snapshot, verify there's one face, then see if we find the face in
    # the aws recognition index

    take_snapshot(camera)

    # Do we see a face?
    data = verify_snapshot()
    if not data:
        return None

    # Do we know this face?
    found_face = find_face(snap_data=data)

    if found_face:
        #print(json.dumps(found_face, indent=4, sort_keys=True))
        print(found_face[0]['Face']['ImageId'])
        print(found_face[0]['Face']['FaceId'])
        print(found_face[0]['Similarity'])
        return found_face[0]

    else:
        print("No match found")
        return False

#for feature, data in face.iteritems():
#     if feature not in FEATURES_BLACKLIST:
#     print "  {feature}({data[Value]}) : {data[Confidence]}%".format(feature=feature, data=data)


def store_face_hash(name, facehash):
    #face.Objects.create(name, facehash)
    co = sql.cursor()
    try:
        co.execute('''CREATE TABLE faces
                         (facehash text, name text)''')
    except sqlite3.OperationalError as e:
        if 'table faces already exists' not in e.message:
            raise
        pass
    result = co.execute("INSERT INTO faces VALUES (?,?)", (facehash, name))
    print("written", result)
    # import ipdb; ipdb.set_trace()
    sql.commit()
    co.close()

def lookup_face_hash(facehash):
    c = sql.cursor()
    t = (facehash,)
    c.execute('SELECT * FROM faces WHERE facehash=?;', t)
    name = c.fetchone()
    c.close()
    if name:
        return name[1]
    return None


