import time


def swap(a, b):
    # Swap the values of a and b
    temp = a
    a = b
    b = temp
    return a, b

def bubbleSort(arr, n):
    n = len(arr)
    # Traverse through all array elements
    for i in range(n-1, -1, -1):
        # Last i elements are already sorted
        for j in range(i):
            # Traverse the array from 0 to n-i-1
            # Swap if the element found is greater than the next element
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = swap(arr[j], arr[j+1])
    return arr

def inSertionSort(arr, n):
    # Traverse through 1 to len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i-1
        # Move elements of arr[0..i-1], that are greater than key,
        # to one position ahead of their current position
        while j >= 0 and key < arr[j]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr

arr = [64, 34, 25, 12, 22, 11, 90]
n = len(arr)

#bubbleSort(arr, n)

inSertionSort(arr, n)
print("Sorted array is:", arr)
# Test with the same array for both algorithms
arr1 = [64, 34, 25, 12, 22, 11, 90]
arr2 = arr1.copy()

# Measure bubble sort time
start_time = time.time()
bubbleSort(arr1, len(arr1))
bubble_time = time.time() - start_time

# Measure insertion sort time
start_time = time.time()
inSertionSort(arr2, len(arr2))
insertion_time = time.time() - start_time

print(f"Bubble Sort time: {bubble_time:.6f} seconds")
print(f"Insertion Sort time: {insertion_time:.6f} seconds")