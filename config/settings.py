MACHINE_ID_LIST = list(range(1, 11))  # List of machine IDs from 1 to 10
MACHINE_LAYOUT = [
    [1, 2, 3, 4, 5],      # First floor
    [6, 7, 8, 9, 10],     # Second floor
    [11, 12, 13, 14, 15]  # Third floor
]
TIME_BUCKET_SIZE = 300 # 5 minute time buckets in seconds
BUFFER_SIZE = 3 # Set the time buffer between reservations to three time buckets (15 minutes)