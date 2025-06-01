from DynamicArray import DynamicArray

class Sort:
    @staticmethod
    def quick_sort(mảng, key=None, reverse=False):
        """
        Sắp xếp mảng sử dụng thuật toán Quick Sort
        :param mảng: DynamicArray cần sắp xếp
        :param key: Hàm để lấy giá trị so sánh
        :param reverse: True để sắp xếp giảm dần, False để sắp xếp tăng dần
        """
        def partition(start, end):
            pivot = mảng[end]
            pivot_value = key(pivot) if key else pivot
            i = start - 1
            
            for j in range(start, end):
                current_value = key(mảng[j]) if key else mảng[j]
                if (not reverse and current_value <= pivot_value) or \
                   (reverse and current_value >= pivot_value):
                    i += 1
                    mảng[i], mảng[j] = mảng[j], mảng[i]
            
            mảng[i + 1], mảng[end] = mảng[end], mảng[i + 1]
            return i + 1

        def quick_sort_helper(start, end):
            if start < end:
                pi = partition(start, end)
                quick_sort_helper(start, pi - 1)
                quick_sort_helper(pi + 1, end)

        quick_sort_helper(0, mảng.size - 1)
        return mảng

    @staticmethod
    def merge_sort(mảng, key=None, reverse=False):
        """
        Sắp xếp mảng sử dụng thuật toán Merge Sort
        :param mảng: DynamicArray cần sắp xếp
        :param key: Hàm để lấy giá trị so sánh
        :param reverse: True để sắp xếp giảm dần, False để sắp xếp tăng dần
        """
        if mảng.size <= 1:
            return mảng

        mid = mảng.size // 2
        left = DynamicArray()
        right = DynamicArray()

        for i in range(mid):
            left.append(mảng[i])
        for i in range(mid, mảng.size):
            right.append(mảng[i])

        Sort.merge_sort(left, key, reverse)
        Sort.merge_sort(right, key, reverse)

        i = j = k = 0

        while i < left.size and j < right.size:
            left_value = key(left[i]) if key else left[i]
            right_value = key(right[j]) if key else right[j]

            if (not reverse and left_value <= right_value) or \
               (reverse and left_value >= right_value):
                mảng[k] = left[i]
                i += 1
            else:
                mảng[k] = right[j]
                j += 1
            k += 1

        while i < left.size:
            mảng[k] = left[i]
            i += 1
            k += 1

        while j < right.size:
            mảng[k] = right[j]
            j += 1
            k += 1

        return mảng