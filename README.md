# Đồ án: Trình Tối Ưu Hóa Dòng Tiền

Đây là đồ án môn học Cấu Trúc Dữ Liệu và Giải Thuật, thực hiện ứng dụng "Trình Tối Ưu Hóa Dòng Tiền" bằng ngôn ngữ Python với giao diện đồ họa sử dụng Tkinter và có khả năng kết nối cơ sở dữ liệu MySQL.

## 1. Giới Thiệu Chung

Ứng dụng được thiết kế để giúp một nhóm các cá nhân quản lý và tối ưu hóa các khoản nợ lẫn nhau. Chương trình cho phép người dùng nhập thông tin về các khoản nợ, tính toán lãi suất, phí phạt (nếu có), và sau đó đề xuất một lịch trình thanh toán được tối ưu hóa nhằm giảm thiểu tổng số giao dịch cần thực hiện giữa các thành viên.

**Mục tiêu chính của đồ án:**
* Áp dụng kiến thức về cấu trúc dữ liệu (như mảng động tự cài đặt, đồ thị biểu diễn bằng ma trận kề) và giải thuật (sắp xếp tùy chỉnh, thuật toán tối ưu hóa dòng tiền dựa trên đồ thị, thuật toán layout đồ thị).
* Xây dựng ứng dụng hoàn chỉnh với giao diện người dùng thân thiện.
* Tuân thủ yêu cầu không sử dụng các cấu trúc dữ liệu và giải thuật nâng cao có sẵn trong thư viện chuẩn của Python.

## 2. Ngôn Ngữ và Công Nghệ Sử Dụng

* **Ngôn ngữ lập trình:** Python 3.x
* **Thư viện giao diện đồ họa (GUI):** Tkinter (module `tkinter.ttk`)
* **Thư viện hỗ trợ GUI:**
    * `tkcalendar`: Để chọn ngày tháng.
* **Thư viện đồ thị và tính toán:**
    * `matplotlib`: Để vẽ biểu đồ so sánh hiệu năng và đồ thị dòng tiền (tùy chỉnh).
* **Cơ sở dữ liệu:** MySQL (sử dụng thư viện `mysql.connector`).
* **Kiểu dữ liệu cho tính toán tài chính:** `Decimal` (từ module `decimal`) để đảm bảo độ chính xác.
* **Cấu trúc dữ liệu tự cài đặt:**
    * `DynamicArray`: Mảng động tùy chỉnh (thay thế cho `list` có sẵn ở những nơi cốt lõi).
    * `Đồ_Thị`: Biểu diễn đồ thị bằng ma trận kề, sử dụng `DynamicArray`.
    * `Graph`: Lớp hỗ trợ cho việc vẽ đồ thị tùy chỉnh (thay thế `networkx`).
* **Giải thuật tự cài đặt:**
    * `Sort.quick_sort`, `Sort.merge_sort`: Các thuật toán sắp xếp tùy chỉnh hoạt động trên `DynamicArray`.
    * Thuật toán tối ưu hóa dòng tiền: Dựa trên việc tính toán số dư ròng và thực hiện các giao dịch bù trừ.
    * `Graph.spring_layout`: Thuật toán layout đồ thị tùy chỉnh.

## 3. Chức Năng Chính

* **Quản lý Người Dùng:**
    * Thêm người dùng mới vào hệ thống.
    * Hiển thị danh sách người dùng.
* **Quản lý Khoản Nợ:**
    * Thêm mới khoản nợ giữa hai người dùng, bao gồm số tiền gốc, ngày giao dịch (mặc định là ngày hiện tại), ngày đến hạn, lãi suất (%/năm), phí phạt (%/tháng).
    * Hiển thị danh sách các khoản nợ gốc đã nhập.
* **Tối Ưu Hóa Dòng Tiền:**
    * Tính toán tổng số tiền phải trả cho mỗi khoản nợ (bao gồm gốc, lãi phát sinh, và phí phạt nếu quá hạn) dựa trên dữ liệu từ CSDL.
    * Áp dụng thuật toán tối ưu để giảm thiểu số lượng giao dịch cần thiết để tất toán các khoản nợ.
    * Hiển thị danh sách các giao dịch đã được tối ưu.
    * Đánh giá hiệu năng: So sánh số lượng và tổng giá trị giao dịch trước và sau khi tối ưu.
* **Hiển Thị Trực Quan (Tùy Chỉnh):**
    * Vẽ biểu đồ cột so sánh hiệu năng tối ưu hóa bằng `matplotlib`.
    * Vẽ đồ thị trực quan (tùy chỉnh bằng `matplotlib` và thuật toán `spring_layout` tự cài đặt) để minh họa dòng tiền trước và sau khi tối ưu.
* **Theo Dõi Tình Trạng Nợ:**
    * Hiển thị chi tiết từng khoản nợ từ CSDL, bao gồm số tiền gốc, đã trả, lãi, phạt và tổng còn nợ (tính đến ngày hiện tại).
    * Cho phép sắp xếp bảng tình trạng nợ theo các cột khác nhau.
    * Chức năng ghi nhận thanh toán cho một khoản nợ cụ thể.
* **Kết Nối Cơ Sở Dữ Liệu:**
    * Giao diện đăng nhập để kết nối tới máy chủ MySQL.
    * Tự động tạo các bảng cần thiết (`debts`, `payments`, `transactions`) nếu chưa tồn tại.
    * Lưu trữ và truy xuất dữ liệu người dùng, khoản nợ, thanh toán, giao dịch tối ưu.
* **Tiện Ích Khác:**
    * Tải/Làm mới dữ liệu từ CSDL.
    * Tạo dữ liệu mẫu (có xóa dữ liệu cũ trong CSDL).
    * Xóa dữ liệu trên giao diện (không ảnh hưởng CSDL) hoặc xóa toàn bộ dữ liệu (bao gồm cả trong CSDL).
    * Thông báo nhắc nhở các khoản nợ sắp đến hạn hoặc đã quá hạn.

## 4. Cấu Trúc Mã Nguồn (Các Lớp Chính)

* **`DynamicArray`:** Cài đặt cấu trúc mảng động với các thao tác cơ bản (append, get, set, remove, insert, __contains__, index, ...).
* **`Sort`:** Chứa các phương thức tĩnh cho thuật toán sắp xếp (Quick Sort, Merge Sort) hoạt động trên `DynamicArray`.
* **`Graph` (cho việc vẽ):** Lớp hỗ trợ lưu trữ thông tin nút, cạnh và cài đặt thuật toán `spring_layout` để phục vụ việc vẽ đồ thị tùy chỉnh bằng `matplotlib`.
* **`Đồ_Thị` (logic nghiệp vụ):**
    * Quản lý danh sách các đỉnh (người dùng) và ma trận kề biểu diễn các khoản nợ gốc giữa họ (sử dụng `DynamicArray`).
    * Các phương thức: `thêm_đỉnh`, `thêm_cạnh`, `tính_số_dư_ròng`, `đồng_bộ_dữ_liệu` (từ CSDL vào ma trận kề), `_tính_số_tiền_hiện_tại` (bao gồm lãi/phạt, cập nhật ma trận kề - *cần rà soát kỹ logic này*).
* **`Tối_Ưu_Hóa_Dòng_Tiền`:**
    * Chứa thuật toán chính để tối ưu hóa các giao dịch dựa trên số dư ròng tính từ `Đồ_Thị`.
    * Sử dụng `DynamicArray` và thuật toán sắp xếp tùy chỉnh.
* **`Giao_Diện_Người_Dùng`:**
    * Xây dựng toàn bộ giao diện đồ họa bằng Tkinter.
    * Xử lý sự kiện từ người dùng.
    * Tương tác với các lớp logic (`Đồ_Thị`, `Tối_Ưu_Hóa_Dòng_Tiền`) và CSDL.
    * Hiển thị dữ liệu, kết quả, biểu đồ.
* **`SQL_Login`:**
    * Cửa sổ Toplevel để người dùng nhập thông tin và kết nối CSDL MySQL.
    * Tự động tạo bảng nếu chưa có.

## 5. Hướng Dẫn Cài Đặt và Sử Dụng

### Yêu Cầu Hệ Thống
* Python 3.7+
* MySQL Server
* Các thư viện Python (cài đặt qua pip):
    * `mysql-connector-python`
    * `matplotlib`
    * `tkcalendar`

### Cài Đặt Thư Viện
```bash
pip install mysql-connector-python matplotlib tkcalendar
