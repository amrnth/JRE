import cv2

# Combine overlapping or adjacent intervals
def merge_intervals(intervals):
    if not intervals:
        return []
    
    # Sort intervals by start time
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for current in intervals[1:]:
        last = merged[-1]
        # Check for overlap or adjacency
        if current[0] <= last[1]:  # Overlapping or touching intervals
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def count_frames(video_path):
    cap = cv2.VideoCapture(video_path)
    
    # Method 1: Quick estimate using video properties
    estimated_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = estimated_frames / fps
    
    print(f"Estimated frames: {estimated_frames}")
    print(f"FPS: {fps}")
    print(f"Duration: {duration:.2f} seconds")
    