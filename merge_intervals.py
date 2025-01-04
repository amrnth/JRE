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
    print("merged: ", merged)
    return merged