import os
import cv2
import time
from PIL import Image
import torch
from ultralytics import YOLO


result_path = os.path.join(os.getcwd(), 'results') # Stitched images are stored here 
stiched_path = os.path.join(os.getcwd(), 'stitch') # Stitched images are stored here 
abs_weight_path = os.path.join(os.getcwd(), 'best_theo.pt')
yolov5_path = os.path.join(os.getcwd(),'yolov5') 
confidence_threshold = 0.85
model = torch.hub.load(yolov5_path, 'custom', path= abs_weight_path, source='local')


def handle_detect(capture_filepath,unique_results_above_confidence):
    try:
        data = model(capture_filepath).pandas().xyxy[0].to_dict(orient = 'records')
        if len(data) == 0:
            return -1, unique_results_above_confidence
        
        # Multiple symbols can be detected in an image, to make things simple,
        # store the one with the highest confidence
        id, confidence, name = data[0]['class'], data[0]['confidence'], data[0]['name'].split('-')[1].strip()

        if confidence > confidence_threshold:
            if id in unique_results_above_confidence:
                # Always save images of the same symbol with higher confidence
                if confidence > unique_results_above_confidence[id][0]:
                    unique_results_above_confidence[name] = (confidence,capture_filepath)
                    return name, unique_results_above_confidence
        else:
            print(f'unclear image as confidence score: {confidence} is below threshold, requiring robot to move back')
            return -1, unique_results_above_confidence
        
        unique_results_above_confidence[name] = (confidence,capture_filepath)
        return name, unique_results_above_confidence
            
    except Exception as e:
        print(f'an error occured with filename: {capture_filepath}, {e}')
        return -1, unique_results_above_confidence

def handle_stiching(k,unique_results_above_confidence):
    results = []
    for name, (confidence, filepath) in unique_results_above_confidence.items():
        results.append([name,confidence,filepath])

    # Sort by confidence in descending order
    results.sort(key=lambda x: x[1], reverse=True)

    print('Drawing boundary boxes')
    for _,_,filepath in results[:k]:
        try:
            data = model(filepath).pandas().xyxy[0].to_dict(orient = 'records')
            draw_box(filepath,data)

        except Exception as e:
            print(f'an error occured while stitching filename: {filepath}, {e}')

    print('Stitching images')
    images = []
    for _,_,filepath in results[:k]:
        filename = os.path.basename(filepath)
        image = Image.open(os.path.join('results',filename))
        images.append(image)

    # get the dimensions of the first image
    width, height = images[0].size

    # create a new image to hold the stitched images
    result = Image.new("RGB", (width * len(images), height))

    # loop over the images and paste them into the new image
    for i, image in enumerate(images):
        result.paste(image, (i * width, 0))

    # save the result to a file
    result.save(os.path.join(stiched_path,f"stitched-image-{str(int(time.time()))}.jpg"))


def draw_box(filepath, rows):
    filename = os.path.basename(filepath)
    # read in the image
    image = cv2.imread(filepath)
    # extract bounding box coordinates from dataframe
    for box in rows:
        ymin = int(box['ymin'])
        xmax = int(box['xmax'])
        xmin = int(box['xmin'])
        ymax = int(box['ymax'])
        class_label = box['name']
        id = box['class']
        confidence = box['confidence']

        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        # Add the class label text
        cv2.putText(image, f"{id}/{class_label}: {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # save the resulting image
    cv2.imwrite(os.path.join(result_path,filename), image)
    print(f'result saved at {os.path.join(result_path,filename)}')


unique_results = {
    # 'V': (0.94,'/Users/kaikiat/school/server/captures/v3.jpeg'),
}


if __name__ == "__main__":
    start = time.time()
    # filename = os.path.join(os.getcwd(),'captures','bulleye.jpeg')
    # filename = os.path.join(os.getcwd(),'captures','v2.jpeg')
    # filename = os.path.join(os.getcwd(),'captures','5.jpeg')
    # filename = os.path.join(os.getcwd(),'captures','stop.jpeg')
    # filename = os.path.join(os.getcwd(),'captures','left.jpeg')
    filename = os.path.join(os.getcwd(),'captures','5.jpeg')
    result = handle_detect(filename,unique_results)
    # handle_stiching(len(unique_results),unique_results)
    end = time.time()
    # print(f"Result : {result}, Time taken: {end - start}")
    name ,confidence = result
    print(name)
    print(confidence)
    
    


