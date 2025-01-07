import cv2

def has_cuda_gpu():
   return cv2.cuda.getCudaEnabledDeviceCount()

print(has_cuda_gpu())