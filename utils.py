import cv2

# Combine overlapping or adjacent intervals
def merge_intervals(intervals):
    if not intervals:
        return []
    
    intervals.sort(key=lambda x: (x[0], x[1]))
    merged = [intervals[0]]

    for current in intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def count_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    
    estimated_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = estimated_frames / fps
    
    print(f"Estimated frames: {estimated_frames}")
    print(f"FPS: {fps}")
    print(f"Duration: {duration:.2f} seconds")
    