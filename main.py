import imagezmq
import time
import os
import shutil
from collections import defaultdict
from PIL import Image
from run_detect import handle_detect, handle_stiching

k = 4 # Change this on the actual day
image_hub = imagezmq.ImageHub('tcp://*:5556')
capture_path = os.path.join(os.getcwd(), 'captures') 
result_path = os.path.join(os.getcwd(), 'results') 
stitch_path = os.path.join(os.getcwd(), 'stitch') 
current_time = time.time()
is_stitched = False
duration = 360 # in seconds
unique_results_above_confidence = defaultdict()
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


def run():
    rpi_name, image = image_hub.recv_image()
    
    print(f'Received image : {rpi_name}')
    if not is_stitched and len(unique_results_above_confidence) >= k or \
        time.time() >= current_time + duration:
        handle_stiching(k,unique_results_above_confidence)
        image_hub.close()
    elif time.time() < current_time + duration:    
        image_memory = Image.fromarray(image)
        capture_filepath = os.path.join(os.getcwd(), 'captures',
                            f'{str(int(time.time()))}.jpeg')
        image_memory.save(capture_filepath)
        results = handle_detect(capture_filepath,unique_results_above_confidence)
        print(f'Results {results}')
        if isinstance(results,str):
            # image_hub.send_reply(str.encode(results))
            image_hub.send_reply(str.encode(symbol_to_letter[results]))
        else:
            print('Nothing detected')
            image_hub.send_reply(b'-1')
    else:
        image_hub.send_reply(b'Time limit ...')

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
        run()
    
    # finally:
        # image_hub.close()
        # handle_stiching()

