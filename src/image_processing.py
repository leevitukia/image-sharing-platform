import subprocess
import random
import string
import os
import re


def process_image(image: bytes) -> bytes | None: # encodes an image to the AVIF format using the reference AV1 encoder through FFmpeg
    temp_file = f"{''.join(random.choices(string.ascii_uppercase, k=40))}.avif"
    resolution = get_image_resolution(image)
    if resolution is None or resolution[0] > 8192 or resolution[1] > 8192:
        return None

    resolution_filter: str = ""
    if resolution[0] > 4096 or resolution[1] > 4096: # https://ffmpeg.org/ffmpeg-utils.html#Expression-Evaluation
        resolution_filter = "-vf \"scale='if(gt(iw, ih), 4096, -1)':'if(gt(ih, iw), 4096, -1)':flags=lanczos\""


    with subprocess.Popen(
        (f"ffmpeg -hide_banner -loglevel error -i pipe: -an -frames:v 1 {resolution_filter} "
        f"-c:v libaom-av1 -cpu-used 5 -still-picture 1 -aom-params aq-mode=1:enable-chroma-deltaq=1 "
        f"-map_metadata -1 -map 0:v -crf 30 -f avif {temp_file}"), 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    ) as process:
        stderr = process.communicate(input=image)[1]

    if len(stderr.decode().strip()) != 0:
        print(stderr.decode().strip())
        os.remove(temp_file)
        return None
    with open(temp_file, 'rb') as file:
        file_data = file.read()

    os.remove(temp_file)

    return file_data

def create_thumbnail(image: bytes) -> bytes | None:
    temp_file = f"{''.join(random.choices(string.ascii_uppercase, k=40))}.avif"
    resolution = get_image_resolution(image)
    if resolution is None or resolution[0] > 8192 or resolution[1] > 8192:
        return None

    filters: str = ""

    if resolution[0] != resolution[1]: # https://ffmpeg.org/ffmpeg-utils.html#Expression-Evaluation
        filters = (" -vf \"crop='if(gt(iw, ih), ih, iw)':'if(gt(iw, ih), ih, iw)':'if(gt(iw, ih), "
                   "round((iw - ih)/2))':'if(gt(ih, iw), round((ih - iw)/2))', scale='min(256,iw)':-1:flags=lanczos\"")
    else:
        filters = " -vf \"scale='min(256,iw)':-1:flags=lanczos\""

    with subprocess.Popen(
        (f"ffmpeg -hide_banner -loglevel error -i pipe: -an -frames:v 1 {filters} "
            f"-c:v libaom-av1 -cpu-used 5 -still-picture 1 -aom-params aq-mode=1:enable-chroma-deltaq=1 "
            f"-map_metadata -1 -map 0:v -crf 30 -f avif {temp_file}"), 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    ) as process:
        stderr = process.communicate(input=image)[1]

    if len(stderr.decode().strip()) != 0:
        print(stderr.decode().strip())
        os.remove(temp_file)
        return None
    with open(temp_file, 'rb') as file:
        file_data = file.read()

    os.remove(temp_file)
    return file_data

def get_image_resolution(file: bytes) -> tuple[int, int] | None:
    with subprocess.Popen(
        "ffmpeg -hide_banner -i pipe:", 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    ) as process:
        stderr = process.communicate(input=file)[1]

    pattern = r' (\d+)x(\d+)'

    last_match = list(re.finditer(pattern, stderr.decode().strip()))[-1]

    if last_match:
        width, height = last_match.groups()
        return (int(width), int(height))
    return None
