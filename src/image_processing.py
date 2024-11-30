from werkzeug.datastructures.file_storage import FileStorage
import subprocess
import random
import string
import os
import re


def processImage(image: bytes) -> bytes | None: # encodes an image to the AVIF format using the reference AV1 encoder through FFmpeg
    tempFile = f"{''.join(random.choices(string.ascii_uppercase, k=40))}.avif"
    resolution = getImageResolution(image)
    if(resolution == None or resolution[0] > 8192 or resolution[1] > 8192):
        return None
    
    resolutionFilter: str = ""
    if(resolution[0] > 4096 or resolution[1] > 4096):
        if(resolution[0] > resolution[1]):
            resolutionFilter = f"-vf scale=4096:-2:flags=lanczos"
        else:
            resolutionFilter = f"-vf scale=-2:4096:flags=lanczos"

    process = subprocess.Popen(
        f"ffmpeg -hide_banner -loglevel error -i pipe: -an -frames:v 1 {resolutionFilter} -c:v libaom-av1 -cpu-used 5 -still-picture 1 -aom-params aq-mode=1:enable-chroma-deltaq=1 -crf 30 -f avif {tempFile}", 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    stdout, stderr = process.communicate(input=image)

    if(len(stderr.decode().strip()) != 0):
        print(stderr.decode().strip())
        os.remove(tempFile)
        return None
    with open(tempFile, 'rb') as file:
        file_data = file.read()

    os.remove(tempFile)

    return file_data

def createThumbnail(image: bytes) -> bytes | None:
    tempFile = f"{''.join(random.choices(string.ascii_uppercase, k=40))}.avif"
    resolution = getImageResolution(image)
    if(resolution == None or resolution[0] > 8192 or resolution[1] > 8192):
        return None
    
    cropFilter: str = ""

    if(resolution[0] > resolution[1]):
        cropFilter = f" -vf \"crop=ih:ih:{(resolution[0] - resolution[1]) / 2}:0, scale='min(256,iw)':-2:flags=lanczos\""
    elif(resolution[1] > resolution[0]):
        cropFilter = f" -vf \"crop=iw:iw:0:{(resolution[1] - resolution[0]) / 2}, scale='min(256,iw)':-2:flags=lanczos\""    

    process = subprocess.Popen(
        f"ffmpeg -hide_banner -loglevel error -i pipe: -an -frames:v 1 {cropFilter} -c:v libaom-av1 -cpu-used 5 -still-picture 1 -aom-params aq-mode=1:enable-chroma-deltaq=1 -crf 30 -f avif {tempFile}", 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    stdout, stderr = process.communicate(input=image)

    if(len(stderr.decode().strip()) != 0):
        print(stderr.decode().strip())
        os.remove(tempFile)
        return None
    with open(tempFile, 'rb') as file:
        file_data = file.read()

    os.remove(tempFile)
    return file_data

    
def getImageResolution(file: bytes) -> tuple[int, int] | None: # I know there's much easier ways to do this but I wanna support extracting the first frame of a video 
    process = subprocess.Popen(
        f"ffmpeg -hide_banner -i pipe:", 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )
    stdout, stderr = process.communicate(input=file)

    pattern = r'(\d+)x(\d+)'
    match = re.search(pattern, stderr.decode().strip())

    if match:
        width, height = match.groups()
        return (int(width), int(height))
    else:
        return None