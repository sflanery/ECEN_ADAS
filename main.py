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
from functions import parsing_box, parsing_bulb

# #preparing data
images = [] #empty lists for all images
labels = []
#box
X_UL = [] #upper left corner, X
X_LR = [] #lower right corner, X
Y_UL = [] #upper left corner, Y
Y_LR = [] #lower right corner, Y
#bulb
BX_UL = [] #upper left corner, X
BX_LR = [] #lower right corner, X
BY_UL = [] #upper left corner, Y
BY_LR = [] #lower right corner, Y

path_box = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/Annotations/Annotations/dayTrain/dayClip1/frameAnnotationsBOX.csv"
path_bulb = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/Annotations/Annotations/dayTrain/dayClip1/frameAnnotationsBULB.csv"
base_dir = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/dayTrain/dayTrain/dayClip1"
parsing_box(path_box=path_box,base_dir=base_dir, images=images, labels=labels, X_UL=X_UL, Y_UL=Y_UL, X_LR=X_LR, Y_LR=Y_LR)
parsing_bulb(path=path_bulb,base_dir=base_dir, X_UL=BX_UL, Y_UL=BY_UL, X_LR=BX_LR, Y_LR=BY_LR)
print("dayClip1 completed")
import sys; sys.exit()
#add other files


images = np.array(images)
labels = np.array(labels)

#converting categorical labels into binary
le = LabelEncoder() #mapping each string into an integer
integer_labels = le.fit_transform(labels)

num_classes = len(np.unique(integer_labels))
labels = to_categorical(integer_labels, num_classes)

#splitting the data into training and validation sets
x_train, x_val, y_train, y_val = train_test_split(images, labels, test_size=0.2, random_state=42)

# model
model = Sequential()
model.add(Conv2D(32,(5,5), activation='relu', input_shape=(64,64,3)))
model.add(Conv2D(32,5, activation='relu'))
model.add(MaxPooling2D((2,2)))
model.add(Dropout(rate=0.25)) # this is to avoid over training
model.add(Conv2D(32,5, activation='relu'))
model.add(Conv2D(32,5, activation='relu'))
model.add(MaxPooling2D((2,2)))
model.add(Dropout(rate=0.25))
#flatten and dense
model.add(Flatten()) #converts 2D feature maps into a 1D vector
model.add(Dense(256,activation='relu'))
model.add(Dropout(rate=0.5))
model.add(Dense(43, activation='softmax'))

print(model.summary())
import sys; sys.exit() #this is to view everything before the training

#copiling
model.compile(loss = 'categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

#training
batch_size = 32
epochs = 15
anc = model.fit(x_train, y_train,epochs=epochs,batch_size=batch_size,validation_data=(x_val, y_val))
model.save("Traffic_Lights.h5")
