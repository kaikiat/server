import imagezmq
import time
import os
import shutil
import socket
from collections import defaultdict
from PIL import Image
from run_detect import handle_detect, handle_stiching

image_hub = imagezmq.ImageHub()
capture_path = os.path.join(os.getcwd(), 'captures') 
result_path = os.path.join(os.getcwd(), 'results') 
stitch_path = os.path.join(os.getcwd(), 'stitch') 
current_time = time.time()
k = 4 # Change this on the actual day
duration = 350 # 
unique_results = defaultdict()
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
    'left': '39',
    'up': '36',
    'right': '38',
    'down': '37',
    'circle': '40',
    'bulleye': '0'
}


def run(unique_results):
    rpi_name, image = image_hub.recv_image()
    
    print(f'Received image : {rpi_name}, Results length: {len(unique_results)} ')
    if len(unique_results) >= k or \
        time.time() >= current_time + duration:
        if time.time() >= current_time + duration:
            print('Exceeded allowed time to complete maze')
        handle_stiching(k,unique_results)
        image_hub.close()
    elif time.time() < current_time + duration:    
        image_memory = Image.fromarray(image)
        capture_filepath = os.path.join(os.getcwd(), 'captures',
                            f'{str(int(time.time()))}.jpeg')
        image_memory.save(capture_filepath)
        results, unique_results = handle_detect(capture_filepath,unique_results)
        print(f'Results {results} for file: {str(capture_filepath)}, Time Taken : {str(time.time() - current_time)}s')
        if isinstance(results,str):
            image_hub.send_reply(str.encode(symbol_to_letter[results]))
        else:
            print(f'Nothing detected for file: {str(capture_filepath)}')
            image_hub.send_reply(b'-1')

if __name__ == "__main__":
    
    if os.path.exists(capture_path) and os.path.isdir(capture_path):
        print(f'Removing folder {capture_path} + {result_path}')
        shutil.rmtree(capture_path)
        shutil.rmtree(result_path)
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
