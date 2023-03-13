import os

symbol_to_letter = {
    '1': '11',
    '2': '12',
    '3': '13',
    '4': '14',
    '5': '15',
    '6': '16',
    '7': '17',
    '8': '18',
    '9': '19',
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
result_path = os.path.join(os.getcwd(), 'results') # Stitched images are stored here 
stiched_path = os.path.join(os.getcwd(), 'stitch') # Stitched images are stored here 
abs_weight_path = os.path.join(os.getcwd(), 'best_theo.pt')
yolov5_path = os.path.join(os.getcwd(),'yolov5') 
confidence_threshold = 0.85
video_capture_port = "rtsp://192.168.1.108:1935"