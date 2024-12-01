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
    if(resolution[0] > 4096 or resolution[1] > 4096): # https://ffmpeg.org/ffmpeg-utils.html#Expression-Evaluation
        resolutionFilter = f"-vf \"scale='if(gt(iw, ih), 4096, -1)':'if(gt(ih, iw), 4096, -1)':flags=lanczos\""


    process = subprocess.Popen(
        f"ffmpeg -hide_banner -loglevel error -i pipe: -an -frames:v 1 {resolutionFilter} -c:v libaom-av1 -cpu-used 5 -still-picture 1 -aom-params aq-mode=1:enable-chroma-deltaq=1 -map_metadata -1 -map 0:v -crf 30 -f avif {tempFile}", 
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

    if(resolution[0] != resolution[1]): # https://ffmpeg.org/ffmpeg-utils.html#Expression-Evaluation
        cropFilter = f" -vf \"crop='if(gt(iw, ih), ih, iw)':'if(gt(iw, ih), ih, iw)':'if(gt(iw, ih), round((iw - ih)/2))':'if(gt(ih, iw), round((ih - iw)/2))', scale='min(256,iw)':-2:flags=lanczos\""

    process = subprocess.Popen(
        f"ffmpeg -hide_banner -loglevel error -i pipe: -an -frames:v 1 {cropFilter} -c:v libaom-av1 -cpu-used 5 -still-picture 1 -aom-params aq-mode=1:enable-chroma-deltaq=1 -map_metadata -1 -map 0:v -crf 30 -f avif {tempFile}", 
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

    
def getImageResolution(file: bytes) -> tuple[int, int] | None:
    process = subprocess.Popen(
        f"ffmpeg -hide_banner -i pipe:", 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )

    stdout, stderr = process.communicate(input=file)

    pattern = r' (\d+)x(\d+)'

    lastMatch = list(re.finditer(pattern, stderr.decode().strip()))[-1]

    if lastMatch:
        width, height = lastMatch.groups()
        return (int(width), int(height))
    else:
        return None