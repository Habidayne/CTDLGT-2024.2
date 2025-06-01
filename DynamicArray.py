class DynamicArray:
    def __init__(self, initial_capacity=4):  #số ô nhớ mặc định là 4
        self.size = 0 # Số lượng phần tử hiện tại trong mảng là 0
        self.capacity = initial_capacity # Dung lượng tối đa của mảng
        self.array = self._create_array(self.capacity) # Tạo mảng với dung lượng ban đầu
    
    def _create_array(self, capacity):
        """Tạo mảng mới với kích thước cho trước"""
        return [None] * capacity # Sử dụng list để mô phỏng mảng
    
    def __len__(self):
        """Trả về số phần tử trong mảng"""
        return self.size # Số lượng phần tử hiện tại trong mảng, không phải dung lượng tối đa
    
    def __getitem__(self, index):
        """Truy cập phần tử tại vị trí index"""
        if not 0 <= index < self.size:
            raise IndexError('Invalid index')
        return self.array[index] # Trả về giá trị tại vị trí index trong mảng, nếu không, nó sẽ ném ra lỗi IndexError
    
    def __setitem__(self, index, value):
        """Gán giá trị cho phần tử tại vị trí index"""
        if not 0 <= index < self.size:
            raise IndexError('Invalid index')
        self.array[index] = value # Gán giá trị cho phần tử tại vị trí index trong mảng, nếu không, nó sẽ ném ra lỗi IndexError
    
    def append(self, element):
        """Thêm phần tử vào cuối mảng"""
        if self.size == self.capacity:
            # Nếu mảng đầy, tăng gấp đôi dung lượng
            self._resize(2 * self.capacity) 
        
        self.array[self.size] = element #Gán phần tử mới vào vị trí trống đầu tiên ở cuối mảng
        self.size += 1 # Tăng kích thước mảng lên 1 sau khi thêm phần tử mới
    
    def _resize(self, new_capacity):
        """Thay đổi kích thước mảng"""
        new_array = self._create_array(new_capacity) # Tạo mảng mới với dung lượng mới
        
        # Sao chép dữ liệu sang mảng mới
        for i in range(self.size):
            new_array[i] = self.array[i]
        
        self.array = new_array # Cập nhật mảng hiện tại thành mảng mới
        self.capacity = new_capacity # Cập nhật dung lượng mảng mới
    
    def __str__(self):
        """Chuyển mảng thành chuỗi để in"""
        return str([self.array[i] for i in range(self.size)])

    def insert(self, index, element):
        """Chèn phần tử tại vị trí index"""
        if not 0 <= index <= self.size:
            raise IndexError('Invalid index') # Kiểm tra chỉ số hợp lệ, cho phép chèn vào cuối mảng
            
        if self.size == self.capacity:
            self._resize(2 * self.capacity) # Nếu mảng đầy, tăng gấp đôi dung lượng
            
        # Dời các phần tử để tạo chỗ trống
        for i in range(self.size, index, -1):
            self.array[i] = self.array[i-1] # Dời các phần tử từ cuối về trước để tạo chỗ trống tại vị trí index
            
        self.array[index] = element # Gán phần tử mới vào vị trí index
        self.size += 1 # Tăng kích thước mảng lên 1 sau khi chèn phần tử mới
    
    def remove(self, element):
        """
        Xóa phần tử đầu tiên có giá trị bằng element
        :param element: Phần tử cần xóa
        :raises ValueError: Nếu không tìm thấy phần tử
        """
        found = False
        for i in range(self.size):
            if self.array[i] == element:
                # Dời các phần tử về trước
                for j in range(i, self.size - 1):
                    self.array[j] = self.array[j+1]
                # Đặt phần tử cuối thành None
                self.array[self.size - 1] = None
                self.size -= 1
                found = True
                break # Nếu tìm thấy phần tử, dời các phần tử phía sau nó về trước và giảm kích thước mảng đi 1


        if not found:
            raise ValueError('Element not found') # Nếu không tìm thấy phần tử, ném ra lỗi ValueError


    def __contains__(self, item):
        """
        Kiểm tra xem một phần tử có tồn tại trong mảng không
        :param item: Phần tử cần kiểm tra
        :return: True nếu tồn tại, False nếu không
        """
        for i in range(self.size):
            if self.array[i] == item:
                return True
        return False # Nếu tìm thấy phần tử, trả về True, nếu không tìm thấy, trả về False

    def index(self, item):
        """
        Tìm vị trí đầu tiên của một phần tử trong mảng
        :param item: Phần tử cần tìm
        :return: Chỉ số của phần tử trong mảng
        :raises ValueError: Nếu không tìm thấy phần tử
        """
        for i in range(self.size):
            if self.array[i] == item: # Nếu tìm thấy phần tử, trả về chỉ số của nó
                return i 
        raise ValueError(f'Value {item} not found in array') # Nếu không tìm thấy phần tử, ném ra lỗi ValueError
    
    def __delitem__(self, index):
        """Xóa phần tử tại vị trí index"""
        if not 0 <= index < self.size:
            raise IndexError("index out of range")
            
        # Dịch chuyển các phần tử về trước một vị trí
        for i in range(index, self.size - 1):
            self.array[i] = self.array[i + 1]
        
        # Giảm kích thước và resize array nếu cần
        self.size -= 1
        if self.size < self.capacity // 4:
            self._resize(self.capacity // 2)