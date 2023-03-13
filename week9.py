import torch
import cv2
import shutil
import os
import constants


class ObjectDetection:
    """
    Class implements Yolo5 model to make inferences on a youtube video using OpenCV.
    """
    
    def __init__(self):
        """
        Initializes the class with youtube url and output file.
        :param url: Has to be as youtube URL,on which prediction is made.
        :param out_file: A valid output file name.
        """
        self.model = self.load_model()
        self.mapping = constants.symbol_to_letter
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.unique_results = set()
        print("\n\nDevice Used:",self.device)



    def load_model(self):
        """
        Loads Yolo5 model from pytorch hub.
        :return: Trained Pytorch model.
        """
        model = torch.hub.load(constants.yolov5_path, "custom", path=constants.abs_weight_path, source="local")
        return model


    def score_frame(self, frame):
        """
        Takes a single frame as input, and scores the frame using yolo5 model.
        :param frame: input frame in numpy/list/tuple format.
        :return: Labels and Coordinates of objects detected by model in the frame.
        """
        self.model.to(self.device)
        frame = [frame]
        results = self.model(frame)
        results = results.pandas().xyxy[0].to_dict(orient = "records")
        return results[0] if results else []


    def class_to_label(self, x):
        """
        For a given label value, return corresponding string label.
        :param x: numeric label
        :return: corresponding string label
        """
        return self.mapping[int(x)]


    def save_image(self, results, frame):
        """
        Takes a frame and its results as input, and plots the bounding boxes and label on to the frame.
        :param results: contains labels and coordinates predicted by model on the given frame.
        :param frame: Frame which has been scored.
        :return: Frame with bounding boxes and labels ploted on it.
        """
        ymin = int(results["ymin"])
        xmax = int(results["xmax"])
        xmin = int(results["xmin"])
        ymax = int(results["ymax"])
        class_label = results["name"]
        _id = results["class"]
        confidence = results["confidence"]

        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        # Add the class label text
        cv2.putText(frame, f"{_id}/{class_label}: {confidence:.2f}", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        # save the resulting image
        cv2.imwrite(os.path.join(constants.result_path,f"{class_label}-{_id}.jpeg"), frame)
        print(f"result saved at {os.path.join(constants.result_path)}")
    
    
    def add_unique_result(self, class_name):
        self.unique_results.add(class_name)
    
    def check_unique_result(self, class_name):
        return class_name not in self.unique_results
    
    def __call__(self):
        """
        This function is called when class is executed, it runs the loop to read the video frame by frame,
        and write the output into a new file.
        :return: void
        """
        shutil.rmtree(constants.result_path)
        print(f"Creating folder {constants.result_path}")
        os.makedirs(constants.result_path)
        cap = cv2.VideoCapture(constants.video_capture_port)

        while cap.isOpened():
            
            ret, frame = cap.read()
            if not ret:
                break
            results = self.score_frame(frame)
            if not results:
                # Send back here
                print("Nothing detected")
                continue
            
            print(f"{results['class']}/{results['name']} was detected")
            if self.check_unique_result(results["class"]):
                self.add_unique_result(results["class"])
                self.save_image(results, frame)



# Create a new object and execute.
detection = ObjectDetection()
detection()