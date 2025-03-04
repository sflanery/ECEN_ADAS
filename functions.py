import os
import pandas as pd
from PIL import Image
import numpy as np
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow.python.keras.utils.np_utils import to_categorical
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from sklearn.preprocessing import LabelEncoder

#function for parsing
def parsing_box(path, base_dir, images, labels, X_UL, Y_UL, X_LR, Y_LR):
    data_df = pd.read_csv(path, delimiter=';')
    for index,row in data_df.iterrows():
        base_dir = base_dir
        img_path = os.path.join(base_dir, row['Filename'])
        label = row['Annotation tag']
        upper_left_x = row['Upper left corner X']
        upper_left_y = row['Upper left corner Y']
        lower_right_x = row['Lower right corner X']
        lower_right_y = row['Lower right corner Y']
        try:
            img = Image.open(img_path)  # open image
            img = img.resize((64, 64))  # resize
            # convert images to numpy array
            img_array = np.array(img) / 255.0
            images.append(img_array)
            labels.append(label)
            X_UL.append(upper_left_x)
            Y_UL.append(upper_left_y)
            X_LR.append(lower_right_x)
            Y_LR.append(lower_right_y)
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")

def parsing_bulb(path, base_dir, X_UL, Y_UL, X_LR, Y_LR):
    data_df = pd.read_csv(path, delimiter=';')
    for index,row in data_df.iterrows():
        base_dir = base_dir
        img_path = os.path.join(base_dir, row['Filename'])
        upper_left_x = row['Upper left corner X']
        upper_left_y = row['Upper left corner Y']
        lower_right_x = row['Lower right corner X']
        lower_right_y = row['Lower right corner Y']
        try:
            X_UL.append(upper_left_x)
            Y_UL.append(upper_left_y)
            X_LR.append(lower_right_x)
            Y_LR.append(lower_right_y)
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")

#for testing
def parsing_box1(path, base_dir, images, labels, X_UL, Y_UL, X_LR, Y_LR):
    data_df = pd.read_csv(path, delimiter=';')
    for index, row in data_df.head(2).iterrows():
        # process the row
        base_dir = base_dir
        img_path = os.path.join(base_dir, row['Filename'])
        label = row['Annotation tag']
        upper_left_x = row['Upper left corner X']
        upper_left_y = row['Upper left corner Y']
        lower_right_x = row['Lower right corner X']
        lower_right_y = row['Lower right corner Y']
        try:
            img = Image.open(img_path)  # open image
            img = img.resize((64, 64))  # resize
            # convert images to numpy array
            img_array = np.array(img) / 255.0
            images.append(img_array)
            labels.append(label)
            X_UL.append(upper_left_x)
            Y_UL.append(upper_left_y)
            X_LR.append(lower_right_x)
            Y_LR.append(lower_right_y)
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")

#for testing
def parsing_bulb1(path, base_dir, X_UL, Y_UL, X_LR, Y_LR):
    data_df = pd.read_csv(path, delimiter=';')
    for index, row in data_df.head(2).iterrows():
        # process the row
        base_dir = base_dir
        img_path = os.path.join(base_dir, row['Filename'])
        upper_left_x = row['Upper left corner X']
        upper_left_y = row['Upper left corner Y']
        lower_right_x = row['Lower right corner X']
        lower_right_y = row['Lower right corner Y']
        try:
            X_UL.append(upper_left_x)
            Y_UL.append(upper_left_y)
            X_LR.append(lower_right_x)
            Y_LR.append(lower_right_y)
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")