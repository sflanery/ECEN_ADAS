import os
import pandas as pd
from PIL import Image


def create_yolo_annotations(csv_path, base_dir, output_dir, class_mapping):
    """
    Converts annotations from a CSV to YOLO-format text files.

    Parameters:
    - csv_path: path to the CSV file.
    - base_dir: directory where the images are located.
    - output_dir: directory where YOLO text files will be saved.
    - class_mapping: a dictionary mapping class names to class IDs.

    The CSV must contain columns:
    'Filename', 'Upper left corner X', 'Upper left corner Y',
    'Lower right corner X', 'Lower right corner Y', and 'Annotation tag'.
    """
    # Read the CSV file
    df = pd.read_csv(csv_path, delimiter=';')

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    for index, row in df.iterrows():
        filename = row['Filename']
        label_str = row['Annotation tag']
        class_id = class_mapping.get(label_str, -1)
        if class_id == -1:
            print(f"Warning: class {label_str} not in mapping. Skipping.")
            continue

        # Full path to image file
        img_path = os.path.join(base_dir, filename)
        try:
            img = Image.open(img_path)
            img_width, img_height = img.size
        except Exception as e:
            print(f"Error opening image {img_path}: {e}")
            continue

        try:
            xmin = int(row['Upper left corner X'])
            ymin = int(row['Upper left corner Y'])
            xmax = int(row['Lower right corner X'])
            ymax = int(row['Lower right corner Y'])
        except ValueError as ve:
            print(f"Error converting coordinates for {filename}: {ve}")
            continue

        # Normalize coordinates
        x_center = ((xmin + xmax) / 2) / img_width
        y_center = ((ymin + ymax) / 2) / img_height
        bbox_width = (xmax - xmin) / img_width
        bbox_height = (ymax - ymin) / img_height

        # Create annotation line in YOLO format
        annotation_line = f"{class_id} {x_center:.6f} {y_center:.6f} {bbox_width:.6f} {bbox_height:.6f}\n"

        # Write to corresponding text file (same name as image, but with .txt extension)
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(output_dir, txt_filename)

        # Ensure the directory for txt_path exists
        txt_dir = os.path.dirname(txt_path)
        os.makedirs(txt_dir, exist_ok=True)

        with open(txt_path, "a") as f:
            f.write(annotation_line)


# # Traffic Lights
# # csv_file_path = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/Annotations/Annotations/dayTrain/dayClip2/frameAnnotationsBOX.csv"
# # images_base_dir = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/dayTrain/dayTrain/dayClip2"
# # output_annotations_dir = "C:/Traffic_Sign_Light_Detection/Traffic_Lights_YOLO/dayTraining2"
# # class_mapping = {
# #     "go": 0,
# #     "stop": 1,
# #     "warning": 2,
# #     "goLeft": 3,
# #     "warningLeft": 4,
# #     "stopLeft": 5,
# # }
# #
# # create_yolo_annotations(csv_file_path, images_base_dir, output_annotations_dir, class_mapping)
#
# #traffic signs
# csv_file_path = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/omkarnadkarni/lisa-traffic-sign/versions/1/vid11/frameAnnotations-MVI_0123.MOV_annotations/frameAnnotations.csv"
# images_base_dir = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/omkarnadkarni/lisa-traffic-sign/versions/1/vid11/frameAnnotations-MVI_0123.MOV_annotations"
# output_annotations_dir ="C:/Traffic_Sign_Light_Detection/Traffic_Signs_YOLO/vid11"
# class_mapping = {
#     "addedLane": 0,
#     "curveRight": 1,
#     "dip": 2,
#     "intersection": 3,
#     "laneEnds": 4,
#     "merge": 5,
#     "pedestrianCrossing": 6,
#     "signalAhead": 7,
#     "slow": 8,
#     "stopAhead": 9,
#     "thruMergeLeft": 10,
#     "thruMergeRight": 11,
#     "turnLeft": 12,
#     "turnRight": 13,
#     "yieldAhead": 14,
#     "doNotPass": 15,
#     "keepRight": 16,
#     "rightLaneMustTurn": 17,
#     "speedLimit15": 18,
#     "speedLimit25": 19,
#     "speedLimit30": 20,
#     "speedLimit35": 21,
#     "speedLimit40": 22,
#     "speedLimit45": 23,
#     "speedLimit50": 24,
#     "speedLimit55": 25,
#     "speedLimit65": 26,
#     "truckSpeedLimit55": 27,
#     "speedLimitUrdbl": 28,
#     "yield": 29,
#     "noLeftTurn": 30,
#     "stop": 31,
#     "rampSpeedAdvisory45": 32,
#     "noRightTurn": 33,
#     "schoolSpeedLimit25": 34,
#     "school": 35,
#     "rampSpeedAdvisoryUrdbl": 36,
#     "rampSpeedAdvisory20": 37,
#     "zoneAhead45": 38,
#     "rampSpeedAdvisory50": 39
# }


#create_yolo_annotations(csv_file_path, images_base_dir, output_annotations_dir, class_mapping)


