import PIL.Image
from PIL import Image, ImageFont, ImageDraw, ImageEnhance
from functions import parsing_box1, parsing_bulb1

images = [] #empty lists for all images
labels = []
#box of the traffic light
X_UL = [] #upper left corner, X
X_LR = [] #lower right corner, X
Y_UL = [] #upper left corner, Y
Y_LR = [] #lower right corner, Y
#bulb of traffic light
BX_UL = [] #upper left corner, X
BX_LR = [] #lower right corner, X
BY_UL = [] #upper left corner, Y
BY_LR = [] #lower right corner, Y

path_box = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/Annotations/Annotations/dayTrain/dayClip1/frameAnnotationsBOX.csv"
path_bulb = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/Annotations/Annotations/dayTrain/dayClip1/frameAnnotationsBULB.csv"
base_dir = "C:/Traffic_Sign_Light_Detection/kagglehub/datasets/mbornoe/lisa-traffic-light-dataset/versions/2/dayTrain/dayTrain/dayClip1"

parsing_box1(path=path_box, base_dir=base_dir, images=images, labels=labels, X_UL=X_UL, Y_UL=Y_UL, X_LR=X_LR, Y_LR=Y_LR)
print("parsing_box finished")
parsing_bulb1(path=path_bulb, base_dir=base_dir, X_UL=BX_UL, Y_UL=BY_UL, X_LR=BX_LR, Y_LR=BY_LR)
print("parsing_bulb finished")

#coordinates for box
x_up = X_UL[0]
y_up = Y_UL[0]
x_down = X_LR[0]
y_down = Y_LR[0]

#coordinates for bulb
bx_up = BX_UL[0]
by_up = BY_UL[0]
bx_down = BX_LR[0]
by_down = BY_LR[0]


img = PIL.Image.open(r"C:\Traffic_Sign_Light_Detection\kagglehub\datasets\mbornoe\lisa-traffic-light-dataset\versions\2\dayTrain\dayTrain\dayClip1\dayTraining\dayClip1--00000.jpg")

draw = ImageDraw.Draw(img)
#drawing rectangle in box
draw.rectangle(((x_up,y_up), (x_down,y_down)), outline="red", fill=None)
#drawing rectangle in bulb
draw.rectangle(((bx_up,by_up), (bx_down,by_down)), outline="blue", fill=None)

img.show()

