import cv2
from PIL import Image
from collections import defaultdict
import torch


# # create an empty list to store images
# images = []

# # set the path to the folder containing the images
# path = "./captures"

# # loop over all the files in the folder
# for filename in os.listdir(path):
#     if filename.endswith(".jpg") or filename.endswith(".JPG"):
#         # open each image and append it to the list
#         image = Image.open(os.path.join(path, filename))
#         images.append(image)

# # get the dimensions of the first image
# width, height = images[0].size

# # create a new image to hold the stitched images
# result = Image.new("RGB", (width * len(images), height))

# # loop over the images and paste them into the new image
# for i, image in enumerate(images):
#     result.paste(image, (i * width, 0))

# # save the result to a file
# result.save("stitched_image.jpg")
# result = Image.open("stitched_image.jpg")
# result.open()


unique_results_above_confidence = defaultdict()
model = torch.hub.load(yolov5_path, 'custom', path= abs_weight_path, source='local')

def handle_stiching(k = 2):
    print('Handle stitching')
    results = []
    print(unique_results_above_confidence)
    for symbol, (confidence, filepath) in unique_results_above_confidence.items():
        results.append([symbol,confidence,filepath])

    # Sort by confidence
    results.sort(key=lambda x: x[1], reverse=True)

    print(f'Sorted results {results}')

    print('Drawing boundary boxes')
    for _,_,filepath in results[:k]:
        try:
            data = model(filepath).pandas().xyxy[0].to_dict(orient = 'records')
            draw_box(filepath, data)
        except Exception as e:
            print(e)
            print(f'an error occured while stitching filename: {filepath}')

    print('Stitching images')
    stitch_image()
    print('Stitching images completed')


def draw_box(filepath, rows):
    filename = os.path.basename(filepath)
    # read in the image
    print('filepath',filepath)
    image = cv2.imread(filepath)
    # extract bounding box coordinates from dataframe
    for box in rows:
        ymin = int(box['ymin'])
        xmax = int(box['xmax'])
        xmin = int(box['xmin'])
        ymax = int(box['ymax'])
        class_label = box['name']
        confidence = box['confidence']

        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        # Add the class label text
        cv2.putText(image, f"{class_label}: {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    # save the resulting image
    # cv2.imwrite(f'{result_path}/{filename}', image)
    print('os.path.join(result_path,filename) =',os.path.join(result_path,filename))
    cv2.imwrite(os.path.join(result_path,filename), image)
    print(f'result saved at {os.path.join(result_path,filename)}')


def stitch_image():
    # create an empty list to store images
    images = []

    # set the path to the folder containing the images
    # path = "./captures"
    path = os.path.join(os.getcwd(), 'captures')

    # loop over all the files in the folder
    for filename in os.listdir(path):
        if filename.endswith(".jpg") or filename.endswith(".JPG") or filename.endswith(".jpeg"):
            # open each image and append it to the list
            image = Image.open(os.path.join(path, filename))
            images.append(image)
    # get the dimensions of the first image
    width, height = images[0].size

    # create a new image to hold the stitched images
    result = Image.new("RGB", (width * len(images), height))

    # loop over the images and paste them into the new image
    for i, image in enumerate(images):
        result.paste(image, (i * width, 0))

    # save the result to a file
    result.save("stitched_image.jpg")


if __name__ == "__main__":
    handle_stiching()

