import imagezmq
import time
import os
import shutil
from collections import defaultdict
from PIL import Image
from run_detect import handle_detect, handle_stiching

# k = 6 # Change this on the actual day
# duration = 410 
image_hub = imagezmq.ImageHub()
capture_path = os.path.join(os.getcwd(), 'captures') 
result_path = os.path.join(os.getcwd(), 'results') 
stitch_path = os.path.join(os.getcwd(), 'stitch') 
current_time = time.time()
unique_results = defaultdict()
# symbol_to_letter = {
#     'one': '11',
#     'two': '12',
#     'three': '13',
#     'four': '14',
#     'five': '15',
#     'six': '16',
#     'seven': '17',
#     'eight': '18',
#     'nine': '19',
#     'A': '20',
#     'B': '21',
#     'C': '22',
#     'D': '23',
#     'E': '24',
#     'F': '25',
#     'G': '26',
#     'H': '27',
#     'S': '28',
#     'T': '29',
#     'U': '30',
#     'V': '31',
#     'W': '32',
#     'X': '33',
#     'Y': '34',
#     'Z': '35',
#     'left': '39',
#     'up': '36',
#     'right': '38',
#     'down': '37',
#     'circle': '40',
#     'bulleye': '0'
# }

symbol_to_letter = {
    'one': '11',
    'two': '12',
    'three': '13',
    'four': '14',
    'five': '15',
    'six': '16',
    'seven': '17',
    'eight': '18',
    'nine': '19',
    'A': '20',
    'B': '21',
    'C': '22',
    'D': '23',
    'E': '24',
    'F': '25',
    'G': '26',
    'H': '27',
    'S': '28',
    'T': '29',
    'U': '30',
    'V': '31',
    'W': '32',
    'X': '33',
    'Y': '34',
    'Z': '35',
    'Left': '39',
    'Up': '36',
    'Right': '38',
    'Down': '37',
    'Stop': '40',
    'Deadend': '0'
}



def run(unique_results):
    rpi_name, image = image_hub.recv_image()
    
    arrival_time = time.time()
    print(f'Received image : {rpi_name}, {str(time.time() - current_time)} seconds has elapsed.')
    print(f'Result length: {len(unique_results)}, Result : {dict(unique_results)}')

    image_memory = Image.fromarray(image)
    capture_filepath = os.path.join(os.getcwd(), 'captures',
                        f'{str(int(time.time()))}.jpeg')
    image_memory.save(capture_filepath)
    results, unique_results = handle_detect(capture_filepath,unique_results)

    try:
        handle_stiching(len(unique_results),unique_results)
    except Exception as e:
        print('An error occured while stitching image', e)

    print(f'Detected {results} for {str(capture_filepath)}, Time Taken (Inclusive of stitching) : {str(time.time() - arrival_time)}s')
    if isinstance(results,str):
        image_hub.send_reply(str.encode(symbol_to_letter[results]))
    else:
        print(f'Nothing detected for file: {str(capture_filepath)}')
        image_hub.send_reply(b'-1')


if __name__ == "__main__":
    
    # if os.path.exists(capture_path) and os.path.isdir(capture_path):
        # print(f'Removing folder {capture_path} + {result_path}')
        # shutil.rmtree(capture_path)
        # shutil.rmtree(result_path)
    if not os.path.exists(result_path):
        print(f'Creating folder {result_path}')
        os.makedirs(result_path)
    if not os.path.exists(capture_path):
        print(f'Creating folder {capture_path}')
        os.makedirs(capture_path)
    if not os.path.exists(stitch_path):
        print(f'Creating folder {stitch_path}')
        os.makedirs(stitch_path)
    print('Starting up server')
    while True:
        run(unique_results)
