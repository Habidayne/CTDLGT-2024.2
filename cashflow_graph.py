import tkinter as tk
import math
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import mysql.connector  
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
#import networkx as nx
from tkcalendar import DateEntry
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime
import seaborn as sns

from DynamicArray import DynamicArray
from Graph import Graph
from Sort_al import Sort

sns.set_style("whitegrid")

def format_money(amount):
    """Định dạng số Decimal thành chuỗi tiền tệ với 2 chữ số thập phân, làm tròn ROUND_HALF_UP."""
    # Chuyển đổi amount sang Decimal nếu nó chưa phải là Decimal (để đảm bảo)
    # Sau đó quantize để làm tròn đến 2 chữ số thập phân theo quy tắc ROUND_HALF_UP (làm tròn đến số gần nhất, 0.5 làm tròn lên)
    return str(Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))




class Đồ_Thị:

    def __init__(self, conn=None, cursor=None):
        self.danh_sách_đỉnh = DynamicArray()  # thay vì []
        self.ma_trận_kề = DynamicArray()      # thay vì []
        self.số_đỉnh = 0
        self.conn = conn
        self.cursor = cursor

    def đồng_bộ_dữ_liệu(self):
        """Đồng bộ ma trận kề với dữ liệu trong MySQL"""
        if not self.conn or not self.cursor:
            return
            
        try:
            # Lấy tất cả khoản nợ và thanh toán
            self.cursor.execute("""
                SELECT d.from_person, d.to_person, d.amount,
                       COALESCE(SUM(p.amount), 0) as paid_amount
                FROM debts d
                LEFT JOIN payments p ON d.id = p.debt_id
                GROUP BY d.id
            """)
            
            # Reset ma trận kề
            self.ma_trận_kề = DynamicArray()
            for i in range(self.số_đỉnh):
                row = DynamicArray()
                for j in range(self.số_đỉnh):
                    row.append(Decimal('0.00'))
                self.ma_trận_kề.append(row)
            
            # Cập nhật ma trận kề
            for người_nợ, người_cho_vay, số_tiền, đã_trả in self.cursor.fetchall():
                if người_nợ in self.danh_sách_đỉnh and người_cho_vay in self.danh_sách_đỉnh:
                    i = self.danh_sách_đỉnh.index(người_nợ)
                    j = self.danh_sách_đỉnh.index(người_cho_vay)
                    số_tiền_còn_lại = Decimal(str(số_tiền)) - Decimal(str(đã_trả))
                    if số_tiền_còn_lại > Decimal('0'):
                        self.ma_trận_kề[i][j] = số_tiền_còn_lại
                        
        except mysql.connector.Error as err:
            print(f"Lỗi đồng bộ dữ liệu: {err}")
    
    def thêm_đỉnh(self, tên):
        # Kiểm tra tên có trong danh_sách_đỉnh
        if tên in self.danh_sách_đỉnh:  # Sử dụng __contains__
            return False
                
        # Thêm đỉnh mới
        self.danh_sách_đỉnh.append(tên)
        self.số_đỉnh += 1
        
        # Khởi tạo ma trận kề
        if self.số_đỉnh == 1:
            new_row = DynamicArray()
            new_row.append(Decimal('0.00'))
            self.ma_trận_kề.append(new_row)
        else:
            # Thêm cột 0 vào các hàng hiện có
            for i in range(self.số_đỉnh - 1):
                row = self.ma_trận_kề[i]
                row.append(Decimal('0.00'))
            
            # Thêm hàng mới
            new_row = DynamicArray()
            for i in range(self.số_đỉnh):
                new_row.append(Decimal('0.00'))
            self.ma_trận_kề.append(new_row)
            
        return True
    
    def thêm_cạnh(self, nguồn, đích, giá_trị, lưu_vào_db=True):
        # Tìm chỉ mục của nguồn và đích
        try:
            chỉ_mục_nguồn = self.danh_sách_đỉnh.index(nguồn)  # Sử dụng index
            chỉ_mục_đích = self.danh_sách_đỉnh.index(đích)    # Sử dụng index
        except ValueError:
            return False
                
        if chỉ_mục_nguồn == -1 or chỉ_mục_đích == -1:
            return False
            
        # Chuyển đổi giá_trị thành Decimal và cộng dồn
        giá_trị_decimal = Decimal(str(giá_trị))
        current_val = self.ma_trận_kề[chỉ_mục_nguồn][chỉ_mục_đích]
        self.ma_trận_kề[chỉ_mục_nguồn][chỉ_mục_đích] = current_val + giá_trị_decimal
        
        # Lưu vào database nếu cần
        if lưu_vào_db:
            self.cursor.execute(
                "INSERT INTO debts (from_person, to_person, amount) VALUES (%s, %s, %s)",
                (nguồn, đích, str(giá_trị_decimal))
            )
            self.conn.commit()
        return True
    
    def đọc_ma_trận_kề(self):
        return self.ma_trận_kề
    
    def tính_số_dư_ròng(self):
        số_dư = DynamicArray()
        for i in range(self.số_đỉnh):
            số_dư.append(Decimal('0.00'))
            
        for i in range(self.số_đỉnh):
            for j in range(self.số_đỉnh):
                số_dư[i] -= Decimal(str(self.ma_trận_kề[i][j]))
                số_dư[i] += Decimal(str(self.ma_trận_kề[j][i]))
        return số_dư
    
    def tính_tổng_nợ(self):
        tổng = Decimal('0.00')
        for i in range(self.số_đỉnh):
            for j in range(self.số_đỉnh):
                tổng += Decimal(str(self.ma_trận_kề[i][j]))
        return tổng
    
    def lấy_danh_sách_nợ(self):
            # Lấy từ MySQL thay vì ma trận kề
            self.cursor.execute("SELECT from_person, to_person, amount FROM debts")
            danh_sách_nợ = self.cursor.fetchall()
            return danh_sách_nợ
    
    def _tính_số_tiền_hiện_tại(self):
        """Tính số tiền hiện tại bao gồm lãi và phí phạt cho các khoản nợ"""
        hôm_nay = time.strftime("%Y-%m-%d")
        self.cursor.execute("""
            SELECT id, from_person, to_person, amount, transaction_date, due_date, interest_rate, late_fee_rate
            FROM debts
        """)
        khoản_nợ = self.cursor.fetchall()
        
        for nợ in khoản_nợ:
            nợ_id, người_nợ, người_cho_vay, số_tiền_gốc, ngày_giao_dịch, ngày_đến_hạn, lãi_suất, phí_phạt = nợ
            
            số_tiền_gốc = Decimal(str(số_tiền_gốc))
            lãi_suất = Decimal(str(lãi_suất or '0'))
            phí_phạt = Decimal(str(phí_phạt or '0'))

            # Tính số ngày từ ngày giao dịch
            ngày_giao_dịch_obj = time.strptime(str(ngày_giao_dịch), "%Y-%m-%d %H:%M:%S")
            ngày_giao_dịch_date = time.strftime("%Y-%m-%d", ngày_giao_dịch_obj)
            ngày_giao_dịch_datetime = time.strptime(ngày_giao_dịch_date, "%Y-%m-%d")
            ngày_hiện_tại_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
            số_ngày = Decimal(str(time.mktime(ngày_hiện_tại_datetime) - time.mktime(ngày_giao_dịch_datetime)) / (24 * 3600))
            
            # Tính lãi
            lãi_hàng_ngày = số_tiền_gốc * (lãi_suất / Decimal('100')) / Decimal('365')
            tiền_lãi = lãi_hàng_ngày * số_ngày
            
            # Tính phí phạt nếu quá hạn
            tiền_phạt = 0
            if ngày_đến_hạn:
                ngày_đến_hạn_datetime = time.strptime(str(ngày_đến_hạn), "%Y-%m-%d")
                if ngày_hiện_tại_datetime > ngày_đến_hạn_datetime:
                    số_ngày_quá_hạn = Decimal(str(time.mktime(ngày_hiện_tại_datetime) - time.mktime(ngày_đến_hạn_datetime)) / (24 * 3600))
                    tiền_phạt = (số_tiền_gốc * phí_phạt * số_ngày_quá_hạn) / (Decimal('100') * Decimal('30'))
            
            # Tổng số tiền hiện tại
            tổng_tiền = số_tiền_gốc + tiền_lãi + tiền_phạt
            
            # Cập nhật lại tổng tiền trong ma trận kề
            chỉ_mục_nguồn = self.danh_sách_đỉnh.index(người_nợ)
            chỉ_mục_đích = self.danh_sách_đỉnh.index(người_cho_vay) 
            self.ma_trận_kề[chỉ_mục_nguồn][chỉ_mục_đích] = tổng_tiền
        
        return khoản_nợ
    

class Tối_Ưu_Hóa_Dòng_Tiền:

    def __init__(self, đồ_thị):
        self.đồ_thị = đồ_thị
    
    def tối_ưu_hóa(self):
        số_dư = DynamicArray()  # Thay vì list
        for i in range(self.đồ_thị.số_đỉnh):
            số_dư.append(Decimal('0.00'))
        
        # Tính số dư
        for i in range(self.đồ_thị.số_đỉnh):
            for j in range(self.đồ_thị.số_đỉnh):
                số_dư[i] -= Decimal(str(self.đồ_thị.ma_trận_kề[i][j]))
                số_dư[i] += Decimal(str(self.đồ_thị.ma_trận_kề[j][i]))

        người_nhận = DynamicArray()
        người_trả = DynamicArray()
        
        # Phân loại người nhận/trả
        for i in range(len(số_dư)):
            if số_dư[i] > Decimal('0.00'):
                người_nhận.append((i, số_dư[i]))
            elif số_dư[i] < Decimal('0.00'):
                người_trả.append((i, số_dư[i]))

        # Sắp xếp (cần thay thế bằng thuật toán sort tự cài đặt)
        Sort.quick_sort(người_nhận, key=lambda x: x[1], reverse=True)
        Sort.quick_sort(người_trả, key=lambda x: x[1])

        giao_dịch_tối_ưu = DynamicArray()
        i, j = 0, 0
        
        while i < người_trả.size and j < người_nhận.size:
            người_trả_idx, số_tiền_trả = người_trả[i]
            người_nhận_idx, số_tiền_nhận = người_nhận[j]
            số_tiền_giao_dịch = min(abs(Decimal(str(số_tiền_trả))), Decimal(str(số_tiền_nhận)))
            
            giao_dịch_tối_ưu.append((
                self.đồ_thị.danh_sách_đỉnh[người_trả_idx],
                self.đồ_thị.danh_sách_đỉnh[người_nhận_idx],
                số_tiền_giao_dịch
            ))
            
            số_tiền_trả += số_tiền_giao_dịch
            số_tiền_nhận -= số_tiền_giao_dịch
            
            người_trả[i] = (người_trả_idx, số_tiền_trả)
            người_nhận[j] = (người_nhận_idx, số_tiền_nhận)
            
            if abs(số_tiền_trả) < Decimal('1e-6'):  # Thay vì < 1e-6
                i += 1
            if số_tiền_nhận < Decimal('1e-6'):  # Thay vì < 1e-6
                j += 1
        
        return giao_dịch_tối_ưu
    
    def đánh_giá_hiệu_năng(self, giao_dịch_tối_ưu):
        # Get initial debt list from adjacency matrix instead of MySQL
        danh_sách_nợ_ban_đầu = DynamicArray()
        for i in range(self.đồ_thị.số_đỉnh):
            for j in range(self.đồ_thị.số_đỉnh):
                if self.đồ_thị.ma_trận_kề[i][j] > Decimal('0'):
                    nguồn = self.đồ_thị.danh_sách_đỉnh[i]
                    đích = self.đồ_thị.danh_sách_đỉnh[j] 
                    giá_trị = self.đồ_thị.ma_trận_kề[i][j]
                    danh_sách_nợ_ban_đầu.append((nguồn, đích, giá_trị))
        
        số_giao_dịch_ban_đầu = danh_sách_nợ_ban_đầu.size
        số_giao_dịch_tối_ưu = giao_dịch_tối_ưu.size

        # Calculate total values
        tổng_giá_trị_ban_đầu = Decimal('0.00')
        for i in range(danh_sách_nợ_ban_đầu.size):
            tổng_giá_trị_ban_đầu += Decimal(str(danh_sách_nợ_ban_đầu[i][2]))

        tổng_giá_trị_tối_ưu = Decimal('0.00')
        for i in range(giao_dịch_tối_ưu.size):
            tổng_giá_trị_tối_ưu += Decimal(str(giao_dịch_tối_ưu[i][2]))

        giảm_số_giao_dịch = số_giao_dịch_ban_đầu - số_giao_dịch_tối_ưu
        tỷ_lệ_giảm = (Decimal(str(giảm_số_giao_dịch)) / 
                    Decimal(str(max(1, số_giao_dịch_ban_đầu)))) * Decimal('100')

        return {
            'số_giao_dịch_ban_đầu': số_giao_dịch_ban_đầu,
            'số_giao_dịch_tối_ưu': số_giao_dịch_tối_ưu,
            'tổng_giá_trị_ban_đầu': tổng_giá_trị_ban_đầu,
            'tổng_giá_trị_tối_ưu': tổng_giá_trị_tối_ưu,
            'giảm_số_giao_dịch': giảm_số_giao_dịch,
            'tỷ_lệ_giảm': tỷ_lệ_giảm
        }

class Giao_Diện_Người_Dùng:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Trình tối ưu hóa dòng tiền")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Initialize database connection attributes
        self.conn = None 
        self.cursor = None

        # Create tabs
        self.tab_control = ttk.Notebook(root)
        self.tab_nhập_liệu = ttk.Frame(self.tab_control)
        self.tab_kết_quả = ttk.Frame(self.tab_control)
        self.tab_biểu_diễn = ttk.Frame(self.tab_control)
        self.tab_tình_trạng = ttk.Frame(self.tab_control)
        self.tab_đồ_thị = ttk.Frame(self.tab_control)
        
        # Add tabs
        self.tab_control.add(self.tab_nhập_liệu, text="Nhập liệu")
        self.tab_control.add(self.tab_kết_quả, text="Kết quả")
        self.tab_control.add(self.tab_đồ_thị, text="Biểu diễn đồ thị")
        self.tab_control.add(self.tab_tình_trạng, text="Tình trạng nợ")
        self.tab_control.pack(expand=1, fill="both")

        # Create frame for buttons
        frame_buttons = ttk.Frame(self.tab_nhập_liệu)
        frame_buttons.pack(pady=5)
        
        # MySQL connection button - always enabled
        self.nút_kết_nối_sql = ttk.Button(
            frame_buttons,
            text="Kết nối MySQL",
            command=self._cập_nhật_kết_nối_sql
        )
        self.nút_kết_nối_sql.pack(side='left', padx=5)

        # Load data button - disabled by default
        self.nút_tải_dữ_liệu = ttk.Button(
            frame_buttons, 
            text="Tải dữ liệu từ SQL", 
            command=self._tải_dữ_liệu_từ_mysql,
            state="disabled"
        )
        self.nút_tải_dữ_liệu.pack(side='left', padx=5)

        # Initialize graph
        self.đồ_thị = Đồ_Thị(self.conn, self.cursor)

        # Build tabs
        self._xây_dựng_tab_nhập_liệu()
        self._xây_dựng_tab_kết_quả() 
        self._xây_dựng_tab_đồ_thị()
        self._xây_dựng_tab_tình_trạng()

        # Ask for MySQL connection
        if messagebox.askyesno("Kết nối SQL", "Bạn có muốn kết nối với cơ sở dữ liệu MySQL không?"):
            self._cập_nhật_kết_nối_sql()


    def _xây_dựng_tab_nhập_liệu(self):
        # Tạo Canvas và Scrollbar
        canvas = tk.Canvas(self.tab_nhập_liệu)
        scrollbar = ttk.Scrollbar(self.tab_nhập_liệu, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Đặt Canvas và Scrollbar vào tab
        canvas.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        # Tạo frame chính để chứa nội dung
        frame_nhập_liệu = ttk.LabelFrame(canvas, text="Thêm người dùng và khoản nợ")
        frame_nhập_liệu.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Gắn frame_nhập_liệu vào Canvas
        canvas.create_window((0, 0), window=frame_nhập_liệu, anchor="nw")
        
        # Cấu hình vùng cuộn khi nội dung thay đổi kích thước
        def _configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame_nhập_liệu.bind("<Configure>", _configure_canvas)

        def _on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mouse_wheel)
        
        # Frame nhập người dùng
        frame_người_dùng = ttk.Frame(frame_nhập_liệu)
        frame_người_dùng.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame_người_dùng, text="Tên người dùng:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_tên_người_dùng = ttk.Entry(frame_người_dùng, width=20)
        self.entry_tên_người_dùng.grid(row=0, column=1, padx=5, pady=5)
        btn_thêm_người_dùng = ttk.Button(frame_người_dùng, text="Thêm người dùng", command=self._thêm_người_dùng)
        btn_thêm_người_dùng.grid(row=0, column=2, padx=5, pady=5)
        # Thêm nút xóa người dùng
        btn_xóa_người_dùng = ttk.Button(frame_người_dùng, text="Xóa người dùng", command=self._xóa_người_dùng)
        btn_xóa_người_dùng.grid(row=0, column=3, padx=5, pady=5)
        
        # Frame nhập khoản nợ
        frame_nợ = ttk.Frame(frame_nhập_liệu)
        frame_nợ.pack(fill="x", padx=10, pady=10)
        ttk.Label(frame_nợ, text="Người nợ:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.combo_người_nợ = ttk.Combobox(frame_nợ, width=15, state="readonly")
        self.combo_người_nợ.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_nợ, text="Người cho vay:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.combo_người_cho_vay = ttk.Combobox(frame_nợ, width=15, state="readonly")
        self.combo_người_cho_vay.grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(frame_nợ, text="Số tiền:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.entry_số_tiền = ttk.Entry(frame_nợ, width=15)
        self.entry_số_tiền.grid(row=0, column=5, padx=5, pady=5)
        btn_thêm_nợ = ttk.Button(frame_nợ, text="Thêm khoản nợ", command=self._thêm_khoản_nợ)
        btn_thêm_nợ.grid(row=0, column=6, padx=5, pady=5)
        btn_xóa_nợ = ttk.Button(frame_nợ, text="Xóa khoản nợ", command=self._xóa_khoản_nợ)
        btn_xóa_nợ.grid(row=0, column=7, padx=5, pady=5)
        
        # Các trường bổ sung (ngày đến hạn, lãi suất, phí phạt)
        ttk.Label(frame_nợ, text="Ngày đến hạn:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.date_due = DateEntry(frame_nợ, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_due.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame_nợ, text="Lãi suất (%):").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.entry_lãi_suất = ttk.Entry(frame_nợ, width=15)
        self.entry_lãi_suất.insert(0, "0.0")
        self.entry_lãi_suất.grid(row=1, column=3, padx=5, pady=5)
        ttk.Label(frame_nợ, text="Phí phạt (%):").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.entry_phí_phạt = ttk.Entry(frame_nợ, width=15)
        self.entry_phí_phạt.insert(0, "0.0")
        self.entry_phí_phạt.grid(row=1, column=5, padx=5, pady=5)
        
        # Frame danh sách người dùng
        frame_ds_người_dùng = ttk.LabelFrame(frame_nhập_liệu, text="Danh sách người dùng")
        frame_ds_người_dùng.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_người_dùng = ttk.Treeview(frame_ds_người_dùng, columns=("id",), show="headings")
        self.tree_người_dùng.heading("id", text="Tên người dùng")
        self.tree_người_dùng.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame danh sách khoản nợ
        frame_ds_nợ = ttk.LabelFrame(frame_nhập_liệu, text="Danh sách khoản nợ")
        frame_ds_nợ.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_nợ = ttk.Treeview(frame_ds_nợ, columns=("người_nợ", "người_cho_vay", "số_tiền", "ngày_đến_hạn", "lãi_suất", "phí_phạt"), show="headings")
        self.tree_nợ.heading("người_nợ", text="Người nợ")
        self.tree_nợ.heading("người_cho_vay", text="Người cho vay")
        self.tree_nợ.heading("số_tiền", text="Số tiền")
        self.tree_nợ.heading("ngày_đến_hạn", text="Ngày đến hạn")
        self.tree_nợ.heading("lãi_suất", text="Lãi suất")
        self.tree_nợ.heading("phí_phạt", text="Phí phạt")
        self.tree_nợ.column("người_nợ", width=120)
        self.tree_nợ.column("người_cho_vay", width=120)
        self.tree_nợ.column("số_tiền", width=80)
        self.tree_nợ.column("ngày_đến_hạn", width=100)
        self.tree_nợ.column("lãi_suất", width=80)
        self.tree_nợ.column("phí_phạt", width=80)
        self.tree_nợ.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Các nút điều khiển
        btn_tối_ưu = ttk.Button(frame_nhập_liệu, text="Tối ưu hóa dòng tiền", command=self._tối_ưu_hóa_dòng_tiền)
        btn_tối_ưu.pack(pady=10)
        btn_xóa = ttk.Button(frame_nhập_liệu, text="Xóa tất cả dữ liệu", command=self._xóa_dữ_liệu)
        btn_xóa.pack(pady=5)
        btn_mẫu = ttk.Button(frame_nhập_liệu, text="Tạo dữ liệu mẫu", command=self._tạo_dữ_liệu_mẫu)
        btn_mẫu.pack(pady=5)

    
    def _cập_nhật_kết_nối_sql(self):
        """Mở cửa sổ đăng nhập SQL và cập nhật kết nối"""
        try:
            login = SQL_Login()
            login.wait_window()
            
            if login.result:
                self.conn, self.cursor = login.result
                self.đồ_thị.conn = self.conn
                self.đồ_thị.cursor = self.cursor
                self.nút_tải_dữ_liệu["state"] = "normal"
                messagebox.showinfo("Thành công", "Đã kết nối thành công với MySQL!")
                self._tải_dữ_liệu_từ_mysql()
            else:
                self.conn = None
                self.cursor = None
                self.đồ_thị.conn = None 
                self.đồ_thị.cursor = None
                self.nút_tải_dữ_liệu["state"] = "disabled"
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi kết nối: {str(e)}")
            self.conn = None
            self.cursor = None
            self.đồ_thị.conn = None
            self.đồ_thị.cursor = None
            self.nút_tải_dữ_liệu["state"] = "disabled"

        

    def _xây_dựng_tab_kết_quả(self):
        # Tạo Canvas và Scrollbar
        canvas = tk.Canvas(self.tab_kết_quả)
        scrollbar = ttk.Scrollbar(self.tab_kết_quả, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        frame_kết_quả = ttk.LabelFrame(canvas, text="Kết quả tối ưu hóa dòng tiền")
        canvas.create_window((0, 0), window=frame_kết_quả, anchor="nw")

        def _configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        frame_kết_quả.bind("<Configure>", _configure_canvas)

        def _on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mouse_wheel)

        # Frame giao dịch
        frame_giao_dịch = ttk.LabelFrame(frame_kết_quả, text="Danh sách giao dịch tối ưu")
        frame_giao_dịch.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_giao_dịch = ttk.Treeview(frame_giao_dịch, columns=("người_trả", "người_nhận", "tổng_giá_trị"), show="headings")
        self.tree_giao_dịch.heading("người_trả", text="Người trả")
        self.tree_giao_dịch.heading("người_nhận", text="Người nhận")
        self.tree_giao_dịch.heading("tổng_giá_trị", text="Tổng giá trị (gốc + lãi + phạt)")
        self.tree_giao_dịch.column("người_trả", width=150)
        self.tree_giao_dịch.column("người_nhận", width=150)
        self.tree_giao_dịch.column("tổng_giá_trị", width=200)  # Tăng chiều rộng để hiển thị tiêu đề dài hơn
        self.tree_giao_dịch.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame thống kê
        frame_thống_kê = ttk.LabelFrame(frame_kết_quả, text="Thống kê hiệu quả")
        frame_thống_kê.pack(fill="both", expand=True, padx=10, pady=10)
        self.text_thống_kê = scrolledtext.ScrolledText(frame_thống_kê, wrap=tk.WORD, width=40, height=10)
        self.text_thống_kê.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame biểu đồ
        self.frame_biểu_đồ = ttk.LabelFrame(frame_kết_quả, text="Biểu đồ so sánh")
        self.frame_biểu_đồ.pack(fill="both", expand=True, padx=10, pady=10)

    def _xây_dựng_tab_đồ_thị(self):
        frame_đồ_thị = ttk.LabelFrame(self.tab_đồ_thị, text="Biểu diễn đồ thị dòng tiền")
        frame_đồ_thị.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.frame_đồ_thị_ban_đầu = ttk.LabelFrame(frame_đồ_thị, text="Đồ thị dòng tiền ban đầu")
        self.frame_đồ_thị_ban_đầu.pack(side=tk.LEFT, fill="both", expand=True, padx=10, pady=10)
        self.frame_đồ_thị_tối_ưu = ttk.LabelFrame(frame_đồ_thị, text="Đồ thị dòng tiền tối ưu")
        self.frame_đồ_thị_tối_ưu.pack(side=tk.RIGHT, fill="both", expand=True, padx=10, pady=10)

    def _thêm_người_dùng(self):
        """Thêm người dùng mới vào hệ thống"""
        tên = self.entry_tên_người_dùng.get().strip()
        
        if not tên:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên người dùng!")
            return
            
        if tên in self.đồ_thị.danh_sách_đỉnh:
            messagebox.showerror("Lỗi", "Tên người dùng đã tồn tại!")
            return
        
        try:
            # Thêm vào đồ thị
            self.đồ_thị.thêm_đỉnh(tên)
            
            # Thêm vào treeview
            self.tree_người_dùng.insert("", "end", values=(tên,))
            
            # Xóa nội dung entry
            self.entry_tên_người_dùng.delete(0, tk.END)
            
            # Cập nhật combobox
            self._cập_nhật_combobox()
            
            messagebox.showinfo("Thành công", f"Đã thêm người dùng: {tên}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm người dùng: {str(e)}")

    def _xóa_người_dùng(self):
        """Xóa người dùng được chọn khỏi hệ thống"""
        selected_items = self.tree_người_dùng.selection()
        if not selected_items:
            messagebox.showerror("Lỗi", "Vui lòng chọn người dùng cần xóa!")
            return

        tên = self.tree_người_dùng.item(selected_items[0])['values'][0]

        try:
            # Kiểm tra khoản nợ
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM debts 
                WHERE from_person = %s OR to_person = %s
            """, (str(tên), str(tên)))
            số_khoản_nợ = self.cursor.fetchone()[0]

            if số_khoản_nợ > 0:
                messagebox.showerror(
                    "Lỗi",
                    f"Không thể xóa người dùng {tên} vì còn {số_khoản_nợ} khoản nợ liên quan!"
                )
                return

            # Xác nhận xóa
            if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa người dùng {tên}?"):
                return

            # Xóa người dùng khỏi đồ thị
            chỉ_mục = self.đồ_thị.danh_sách_đỉnh.index(tên)
            if chỉ_mục >= 0:
                # Tạo ma trận kề mới với kích thước nhỏ hơn
                ma_trận_mới = DynamicArray()
                for i in range(self.đồ_thị.số_đỉnh - 1):
                    hàng_mới = DynamicArray()
                    for j in range(self.đồ_thị.số_đỉnh - 1):
                        if i < chỉ_mục and j < chỉ_mục:
                            hàng_mới.append(self.đồ_thị.ma_trận_kề[i][j])
                        elif i < chỉ_mục and j >= chỉ_mục:
                            hàng_mới.append(self.đồ_thị.ma_trận_kề[i][j+1])
                        elif i >= chỉ_mục and j < chỉ_mục:
                            hàng_mới.append(self.đồ_thị.ma_trận_kề[i+1][j])
                        else:
                            hàng_mới.append(self.đồ_thị.ma_trận_kề[i+1][j+1])
                    ma_trận_mới.append(hàng_mới)
                
                # Cập nhật ma trận kề và danh sách đỉnh
                del self.đồ_thị.danh_sách_đỉnh[chỉ_mục]
                self.đồ_thị.ma_trận_kề = ma_trận_mới
                self.đồ_thị.số_đỉnh -= 1

                # Xóa khỏi treeview
                self.tree_người_dùng.delete(selected_items[0])
                
                # Cập nhật combobox
                self._cập_nhật_combobox()
                
                messagebox.showinfo("Thành công", f"Đã xóa người dùng: {tên}")

        except mysql.connector.Error as err:
            messagebox.showerror("Lỗi", f"Không thể xóa người dùng: {err}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {str(e)}")

    def _xây_dựng_tab_tình_trạng(self):
        # Frame chính
        frame_tình_trạng = ttk.LabelFrame(self.tab_tình_trạng, text="Tình trạng các khoản nợ")
        frame_tình_trạng.pack(fill="both", expand=True, padx=20, pady=20)

        # Frame chứa các nút điều khiển
        frame_buttons = ttk.Frame(frame_tình_trạng)
        frame_buttons.pack(fill='x', padx=5, pady=5)
        
        # Các nút điều khiển
        btn_cập_nhật = ttk.Button(
            frame_buttons, 
            text="Cập nhật tình trạng nợ",
            command=self._cập_nhật_tình_trạng_nợ
        )
        btn_cập_nhật.pack(side='left', padx=5)
        
        btn_thanh_toán = ttk.Button(
            frame_buttons, 
            text="Thanh toán",
            command=self._ghi_nhận_thanh_toán
        )
        btn_thanh_toán.pack(side='left', padx=5)

        # Frame cho bảng với scrollbars
        frame_table = ttk.Frame(frame_tình_trạng)
        frame_table.pack(fill='both', expand=True, padx=5, pady=5)

        # Tạo và cấu hình scrollbars
        vsb = ttk.Scrollbar(frame_table, orient="vertical")
        hsb = ttk.Scrollbar(frame_table, orient="horizontal")

        # Định nghĩa các cột với thuộc tính chi tiết
        column_defs = {
            "người_nợ": {
                "heading": "Người nợ",
                "width": 120,
                "anchor": "w",
                "stretch": False,
                "is_numeric": False
            },
            "người_cho_vay": {
                "heading": "Người cho vay", 
                "width": 120,
                "anchor": "w",
                "stretch": False,
                "is_numeric": False
            },
            "số_tiền_gốc": {
                "heading": "Số tiền gốc",
                "width": 150,
                "anchor": "e",
                "stretch": False,
                "is_numeric": True
            },
            "ngày_giao_dịch": {
                "heading": "Ngày giao dịch",
                "width": 120,
                "anchor": "center",
                "stretch": False,
                "is_numeric": False
            },
            "ngày_đến_hạn": {
                "heading": "Ngày đến hạn",
                "width": 120,
                "anchor": "center",
                "stretch": False,
                "is_numeric": False
            },
            "lãi_suất": {
                "heading": "Lãi suất (%)",
                "width": 100,
                "anchor": "e",
                "stretch": False,
                "is_numeric": True
            },
            "phí_phạt": {
                "heading": "Phí phạt (%)",
                "width": 100,
                "anchor": "e",
                "stretch": False,
                "is_numeric": True
            },
            "số_ngày_quá_hạn": {
                "heading": "Số ngày quá hạn",
                "width": 120,
                "anchor": "e",
                "stretch": False,
                "is_numeric": True
            },
            "tiền_lãi": {           
            "heading": "Tiền lãi",
            "width": 150,
            "anchor": "e",
            "stretch": False,
            "is_numeric": True
            },
            "tổng_phí_phạt": {
                "heading": "Tổng phí phạt",
                "width": 150,
                "anchor": "e",
                "stretch": False,
                "is_numeric": True
            },
            "tổng_tiền": {
                "heading": "Tổng tiền",
                "width": 150,
                "anchor": "e",
                "stretch": False,
                "is_numeric": True
            }
        }

        # Tạo Treeview với các cột đã định nghĩa
        self.tree_tình_trạng = ttk.Treeview(
            frame_table,
            columns=tuple(column_defs.keys()),
            show="headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        # Thiết lập scrollbars
        vsb.config(command=self.tree_tình_trạng.yview)
        hsb.config(command=self.tree_tình_trạng.xview)

        # Grid layout cho tree và scrollbars
        self.tree_tình_trạng.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        # Cấu hình grid weights
        frame_table.grid_rowconfigure(0, weight=1)
        frame_table.grid_columnconfigure(0, weight=1)

        # Cấu hình các cột
        for col, props in column_defs.items():
            self.tree_tình_trạng.heading(
                col,
                text=props["heading"],
                command=lambda c=col, n=props["is_numeric"]: 
                    self._sắp_xếp_treeview(self.tree_tình_trạng, c, n)
            )
            self.tree_tình_trạng.column(
                col,
                width=props["width"],
                minwidth=props["width"]-20,
                anchor=props["anchor"],
                stretch=props["stretch"]
            )

        # Style cho alternating rows
        style = ttk.Style()
        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            fieldbackground="white"
        )
        style.map(
            "Treeview",
            background=[("selected", "#0078D7")],
            foreground=[("selected", "white")]
        )

        # Biến theo dõi trạng thái sắp xếp
        self.sort_states = {}

        # Binding cho việc chọn dòng
        self.tree_tình_trạng.bind('<<TreeviewSelect>>', self._on_tình_trạng_select)

        # Tạo context menu
        self.context_menu = tk.Menu(self.tree_tình_trạng, tearoff=0)
        self.context_menu.add_command(
            label="Thanh toán",
            command=self._ghi_nhận_thanh_toán
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="Cập nhật",
            command=self._cập_nhật_tình_trạng_nợ
        )

        # Binding cho right-click
        self.tree_tình_trạng.bind(
            "<Button-3>",
            lambda e: self._show_context_menu(e)
        )

    def _show_context_menu(self, event):
        """Hiển thị context menu khi right-click"""
        if self.tree_tình_trạng.selection():  # Chỉ hiển thị khi có dòng được chọn
            self.context_menu.tk_popup(event.x_root, event.y_root)

    def _on_tình_trạng_select(self, event):
        """Xử lý sự kiện khi chọn một dòng trong bảng tình trạng"""
        selection = self.tree_tình_trạng.selection()
        if selection:
            # Enable nút thanh toán nếu có dòng được chọn
            for child in self.tree_tình_trạng.get_children():
                if child in selection:
                    values = self.tree_tình_trạng.item(child)['values']
                    # Có thể thêm logic xử lý khi chọn dòng ở đây

    def _sắp_xếp_treeview(self, tree, col, is_numeric=False):
        
        
        # Định nghĩa hàm chuyển đổi ngày rõ ràng
        def convert_date(date_str):
            if not date_str or date_str.strip() == '':
                return datetime.min
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, AttributeError):
                print(f"Lỗi chuyển đổi ngày: '{date_str}'")
                return datetime.min
        
        # Lấy tất cả các mục từ tree và chuyển vào DynamicArray
        items = DynamicArray()
        for item in tree.get_children(''):
            items.append((tree.set(item, col), item))
        
        # Khởi tạo trạng thái sắp xếp nếu chưa có
        if col not in self.sort_states:
            self.sort_states[col] = False  # False = tăng dần
        
        # Đảo ngược trạng thái sắp xếp hiện tại
        self.sort_states[col] = not self.sort_states[col]
        
        # Xác định key function dựa trên loại dữ liệu
        if col in ["ngày_giao_dịch", "ngày_đến_hạn"]:
            Sort.quick_sort(items, 
                        key=lambda x: convert_date(x[0]), 
                        reverse=self.sort_states[col])
        elif is_numeric:
            Sort.quick_sort(items, 
                key=lambda x: (Decimal(str(x[0]).replace(',', '').replace('%', '')) 
                            if x[0] and x[0].strip() 
                            else Decimal('-Infinity')),
                reverse=self.sort_states[col])
        else:
            Sort.quick_sort(items, 
                        key=lambda x: x[0].lower() if x[0] else "", 
                        reverse=self.sort_states[col])
        
        # Xóa các mục hiện tại và thêm lại theo thứ tự đã sắp xếp
        for index in range(items.size):
            val, id = items[index]
            tree.move(id, '', index)
        
        # Lưu trữ tiêu đề gốc khi khởi tạo
        if not hasattr(self, 'original_headings'):
            self.original_headings = {}
            for c in tree['columns']:
                self.original_headings[c] = tree.heading(c)['text']
        
        # Cập nhật tiêu đề để hiển thị hướng sắp xếp
        original_text = self.original_headings[col]
        if " ↓" in original_text:
            original_text = original_text.replace(" ↓", "")
        if " ↑" in original_text:
            original_text = original_text.replace(" ↑", "")
        
        arrow = " ↓" if self.sort_states[col] else " ↑"
        tree.heading(col, text=original_text + arrow)
        
        # Đặt lại tiêu đề của các cột khác
        for c in tree['columns']:
            if c != col:
                original_text = self.original_headings[c]
                if " ↓" in original_text:
                    original_text = original_text.replace(" ↓", "")
                if " ↑" in original_text:
                    original_text = original_text.replace(" ↑", "")
                tree.heading(c, text=original_text)

    def _tính_tiền_lãi(self, số_tiền_gốc, lãi_suất, ngày_giao_dịch, ngày_kết_thúc):
        """Tính tiền lãi dựa trên số tiền gốc và thời gian"""
        if not ngày_giao_dịch:
            return Decimal('0')
        
        try:
            if isinstance(ngày_giao_dịch, str):
                ngày_giao_dịch_datetime = time.strptime(ngày_giao_dịch, "%Y-%m-%d")
            else:
                ngày_giao_dịch_datetime = ngày_giao_dịch

            # Đặt thời gian là 7 ngày trước ngày kết thúc để demo
            ngày_bắt_đầu = time.localtime(time.time() - 7*24*3600)
            
            # Tính số ngày 
            số_ngày = Decimal(str(
                (time.mktime(ngày_kết_thúc) - time.mktime(ngày_bắt_đầu)) / (24 * 3600)
            ))
            
            # Tính tiền lãi
            tiền_lãi = (số_tiền_gốc * 
                    (Decimal(str(lãi_suất)) / Decimal('100')) * 
                    số_ngày) / Decimal('365')
            
            return max(Decimal('0'), tiền_lãi)
            
        except Exception as e:
            print(f"Lỗi tính lãi: {str(e)}")
            return Decimal('0')

    def _tính_phí_phạt(self, số_tiền_gốc, phí_phạt, ngày_đến_hạn, ngày_kết_thúc):
        """Tính phí phạt nếu quá hạn"""
        if not ngày_đến_hạn or not phí_phạt:
            return Decimal('0'), 0
            
        ngày_đến_hạn_datetime = time.strptime(str(ngày_đến_hạn), "%Y-%m-%d")
        
        # Chỉ tính phí phạt nếu đã quá hạn
        if ngày_kết_thúc <= ngày_đến_hạn_datetime:
            return Decimal('0'), 0
            
        số_ngày_quá_hạn = int((time.mktime(ngày_kết_thúc) - 
                            time.mktime(ngày_đến_hạn_datetime)) / (24 * 3600))
        
        tiền_phạt = (số_tiền_gốc * 
                    Decimal(str(phí_phạt)) / Decimal('100') * 
                    Decimal(str(số_ngày_quá_hạn))) / Decimal('30')
                    
        return tiền_phạt, số_ngày_quá_hạn

    def _cập_nhật_tình_trạng_nợ(self, show_message=True):
        """Cập nhật tình trạng nợ từ ma trận kề"""
        try:
            # Xóa dữ liệu cũ
            for item in self.tree_tình_trạng.get_children():
                self.tree_tình_trạng.delete(item)

            # Lấy ngày hiện tại và ngày bắt đầu (7 ngày trước để demo)
            hôm_nay = time.strftime("%Y-%m-%d")
            hôm_nay_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
            ngày_bắt_đầu = time.strftime("%Y-%m-%d", time.localtime(time.time() - 7*24*3600))

            # Mảng lưu thông tin thanh toán
            đã_trả_gốc = DynamicArray()
            đã_trả_lãi = DynamicArray()
            đã_trả_phí = DynamicArray()
                
            # Lấy thông tin thanh toán từ MySQL nếu có kết nối
            if self.conn and self.cursor:
                self.cursor.execute("""
                    SELECT d.from_person, d.to_person,
                        COALESCE(SUM(p.principal_amount), 0) as paid_principal,
                        COALESCE(SUM(p.interest_amount), 0) as paid_interest,
                        COALESCE(SUM(p.fee_amount), 0) as paid_fee
                    FROM debts d
                    LEFT JOIN payments p ON d.id = p.debt_id
                    GROUP BY d.from_person, d.to_person
                """)
                for row in self.cursor.fetchall():
                    đã_trả_gốc.append((row[0], row[1], Decimal(str(row[2]))))
                    đã_trả_lãi.append((row[0], row[1], Decimal(str(row[3]))))
                    đã_trả_phí.append((row[0], row[1], Decimal(str(row[4]))))

            # Duyệt qua ma_trận_kề để cập nhật tình trạng nợ
            for i in range(self.đồ_thị.số_đỉnh):
                for j in range(self.đồ_thị.số_đỉnh):
                    số_tiền_gốc = self.đồ_thị.ma_trận_kề[i][j]
                    if số_tiền_gốc > Decimal('0'):
                        người_nợ = self.đồ_thị.danh_sách_đỉnh[i]
                        người_cho_vay = self.đồ_thị.danh_sách_đỉnh[j]

                        # Tìm thông tin từ tree_nợ
                        ngày_đến_hạn = 'N/A'
                        lãi_suất = Decimal('0')
                        phí_phạt = Decimal('0')
                        
                        # Duyệt tree_nợ để lấy thông tin chi tiết
                        for item in self.tree_nợ.get_children():
                            values = self.tree_nợ.item(item)['values']
                            if values[0] == người_nợ and values[1] == người_cho_vay:
                                ngày_đến_hạn = values[3]
                                lãi_suất = Decimal(str(values[4]).replace("%", ""))
                                phí_phạt = Decimal(str(values[5]).replace("%", ""))
                                break

                        # Tính tiền lãi
                        tiền_lãi = self._tính_tiền_lãi(
                            số_tiền_gốc,
                            lãi_suất,
                            ngày_bắt_đầu,
                            hôm_nay_datetime
                        )

                        # Tính phí phạt nếu có ngày đến hạn
                        tiền_phạt = Decimal('0')
                        số_ngày_quá_hạn = 0
                        if ngày_đến_hạn != 'N/A':
                            tiền_phạt, số_ngày_quá_hạn = self._tính_phí_phạt(
                                số_tiền_gốc,
                                phí_phạt,
                                ngày_đến_hạn,
                                hôm_nay_datetime
                            )

                        # Tính tổng tiền phải trả
                        tổng_tiền = số_tiền_gốc + tiền_lãi + tiền_phạt

                        # Thêm vào treeview
                        self.tree_tình_trạng.insert("", "end", 
                            values=(
                                người_nợ,
                                người_cho_vay,
                                format_money(số_tiền_gốc),
                                ngày_bắt_đầu,
                                ngày_đến_hạn,
                                f"{lãi_suất}%",
                                f"{phí_phạt}%",
                                số_ngày_quá_hạn,
                                format_money(tiền_lãi),
                                format_money(tiền_phạt),
                                format_money(tổng_tiền)
                            ),
                            tags=(str(i*self.đồ_thị.số_đỉnh + j),)
                        )

            if show_message:
                messagebox.showinfo("Thành công", "Đã cập nhật tình trạng nợ!")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {str(e)}")

    def _thêm_khoản_nợ(self):
        người_nợ = self.combo_người_nợ.get()
        người_cho_vay = self.combo_người_cho_vay.get()

        try:
            # Xử lý định dạng số tiền: loại bỏ dấu phẩy và khoảng trắng
            số_tiền_str = self.entry_số_tiền.get().strip().replace(',', '')
            if not số_tiền_str:
                raise ValueError("Vui lòng nhập số tiền")
            
            try:
                số_tiền = Decimal(số_tiền_str)
            except InvalidOperation:
                raise ValueError("Số tiền không hợp lệ. Vui lòng chỉ nhập số")

            if số_tiền <= Decimal('0'):
                raise ValueError("Số tiền phải lớn hơn 0")
                    
            # Parse new fields
            ngày_đến_hạn = self.date_due.get()
            
            # Xử lý lãi suất
            try:
                lãi_suất = Decimal(self.entry_lãi_suất.get().strip() or '0')
            except InvalidOperation:
                raise ValueError("Lãi suất không hợp lệ. Vui lòng chỉ nhập số")

            # Xử lý phí phạt
            try:
                phí_phạt = Decimal(self.entry_phí_phạt.get().strip() or '0')
            except InvalidOperation:
                raise ValueError("Phí phạt không hợp lệ. Vui lòng chỉ nhập số")
            
            # Kiểm tra lãi suất <= 20%
            if lãi_suất > 20:
                raise ValueError("Lãi suất hàng năm không được vượt quá 20%")
            
            # Validate date format
            if ngày_đến_hạn:
                try:
                    # Convert to proper date format
                    ngày_đến_hạn = time.strptime(ngày_đến_hạn, "%d/%m/%Y")
                    ngày_đến_hạn = time.strftime("%Y-%m-%d", ngày_đến_hạn)
                except ValueError:
                    raise ValueError("Định dạng ngày không hợp lệ. Vui lòng sử dụng DD/MM/YYYY")
            else:
                ngày_đến_hạn = None
                    
        except ValueError as e:
            messagebox.showerror("Lỗi", f"Dữ liệu không hợp lệ: {str(e)}")
            return
            
        if người_nợ == người_cho_vay:
            messagebox.showerror("Lỗi", "Người nợ và người cho vay không thể là cùng một người!")
            return
                
        if not người_nợ or not người_cho_vay:
            messagebox.showerror("Lỗi", "Vui lòng chọn người nợ và người cho vay!")
            return
                
        # Update the database insertion
        self.cursor.execute(
            "INSERT INTO debts (from_person, to_person, amount, due_date, interest_rate, late_fee_rate) VALUES (%s, %s, %s, %s, %s, %s)",
            (người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, lãi_suất, phí_phạt)
        )
        self.đồ_thị.conn.commit()
            
        # Update the matrix
        self.đồ_thị.thêm_cạnh(người_nợ, người_cho_vay, số_tiền, lưu_vào_db=False)
            
        # Update the tree view with new loan information
        self.tree_nợ.insert("", "end", values=(
            người_nợ, 
            người_cho_vay, 
            format_money(số_tiền),
            ngày_đến_hạn, 
            f"{lãi_suất}%", 
            f"{phí_phạt}%"
        ))
            
        # Clear entry fields
        self.entry_số_tiền.delete(0, tk.END)
        self.date_due.delete(0, tk.END)
        self.entry_lãi_suất.delete(0, tk.END)
        self.entry_phí_phạt.delete(0, tk.END)
            
        # Set default values
        self.entry_lãi_suất.insert(0, "0.0")
        self.entry_phí_phạt.insert(0, "0.0")
            
        messagebox.showinfo("Thành công", f"Đã thêm khoản nợ: {người_nợ} nợ {người_cho_vay} {số_tiền}")


    
    def _xóa_khoản_nợ(self):
        """Xóa khoản nợ được chọn từ tree_nợ"""
        selected_items = self.tree_nợ.selection()
        if not selected_items:
            messagebox.showerror("Lỗi", "Vui lòng chọn khoản nợ cần xóa!")
            return

        # Lấy thông tin khoản nợ được chọn
        values = self.tree_nợ.item(selected_items[0])['values']
        người_nợ = values[0]
        người_cho_vay = values[1] 
        số_tiền = Decimal(str(values[2]).replace(",", ""))

        # Xác nhận xóa
        if not messagebox.askyesno("Xác nhận", 
            f"Bạn có chắc muốn xóa khoản nợ:\n{người_nợ} nợ {người_cho_vay} {format_money(số_tiền)}?"):
            return

        try:
            # Tìm debt_id của khoản nợ cụ thể này, không cần JOIN với payments
            self.cursor.execute("""
                SELECT id FROM debts 
                WHERE from_person = %s 
                AND to_person = %s 
                AND amount = %s
            """, (người_nợ, người_cho_vay, str(số_tiền)))

            result = self.cursor.fetchone()
            if not result:
                raise ValueError(f"Không tìm thấy khoản nợ của {người_nợ} cho {người_cho_vay} với số tiền {format_money(số_tiền)}")
                
            debt_id = result[0]

            # Xóa các payment liên quan trước
            self.cursor.execute("DELETE FROM payments WHERE debt_id = %s", (debt_id,))
            
            # Sau đó xóa khoản nợ
            self.cursor.execute("DELETE FROM debts WHERE id = %s", (debt_id,))

            self.conn.commit()

            # Cập nhật ma_trận_kề
            i = self.đồ_thị.danh_sách_đỉnh.index(người_nợ)
            j = self.đồ_thị.danh_sách_đỉnh.index(người_cho_vay)
            self.đồ_thị.ma_trận_kề[i][j] = max(Decimal('0'), 
                self.đồ_thị.ma_trận_kề[i][j] - số_tiền)

            # Xóa khỏi treeview và cập nhật giao diện
            self.tree_nợ.delete(selected_items[0])
            self._tải_dữ_liệu_từ_mysql()
            self._cập_nhật_tình_trạng_nợ()
            
            messagebox.showinfo("Thành công", "Đã xóa khoản nợ!")

        except mysql.connector.Error as err:
            self.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể xóa khoản nợ: {err}")
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            self.conn.rollback()
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {str(e)}")


    def _cập_nhật_combobox(self):
        danh_sách = DynamicArray()
        for i in range(self.đồ_thị.danh_sách_đỉnh.size):
            danh_sách.append(self.đồ_thị.danh_sách_đỉnh[i])
        self.combo_người_nợ['values'] = tuple(danh_sách)  # Chuyển về tuple cho combobox
        self.combo_người_cho_vay['values'] = tuple(danh_sách)


    def _tối_ưu_hóa_dòng_tiền(self):
        if self.đồ_thị.số_đỉnh < 2:
            messagebox.showerror("Lỗi", "Cần ít nhất 2 người dùng để tối ưu hóa dòng tiền!")
            return

        # Lấy danh sách nợ từ đồ thị thay vì từ MySQL
        danh_sách_nợ = DynamicArray()
        
        # Duyệt qua ma_trận_kề để lấy các khoản nợ
        for i in range(self.đồ_thị.số_đỉnh):
            for j in range(self.đồ_thị.số_đỉnh):
                if self.đồ_thị.ma_trận_kề[i][j] > Decimal('0'):
                    người_nợ = self.đồ_thị.danh_sách_đỉnh[i]
                    người_cho_vay = self.đồ_thị.danh_sách_đỉnh[j]
                    số_tiền = self.đồ_thị.ma_trận_kề[i][j]
                    danh_sách_nợ.append((người_nợ, người_cho_vay, số_tiền))

        if not danh_sách_nợ.size:
            messagebox.showerror("Lỗi", "Không có khoản nợ nào để tối ưu hóa!")
            return

        # Thực hiện tối ưu hóa
        bắt_đầu = time.time()
        đồ_thị_tạm = Đồ_Thị()
        for tên in self.đồ_thị.danh_sách_đỉnh:
            đồ_thị_tạm.thêm_đỉnh(tên)
        
        for nguồn, đích, giá_trị in danh_sách_nợ:
            đồ_thị_tạm.thêm_cạnh(nguồn, đích, giá_trị, lưu_vào_db=False)
        
        tối_ưu = Tối_Ưu_Hóa_Dòng_Tiền(đồ_thị_tạm)
        giao_dịch_tối_ưu = tối_ưu.tối_ưu_hóa()
        kết_thúc = time.time()
        thời_gian = (kết_thúc - bắt_đầu) * 1000

        # Hiển thị kết quả
        self._hiển_thị_kết_quả(giao_dịch_tối_ưu, tối_ưu.đánh_giá_hiệu_năng(giao_dịch_tối_ưu), thời_gian)
        self._vẽ_đồ_thị(danh_sách_nợ, giao_dịch_tối_ưu)
        self.tab_control.select(1)

    def _hiển_thị_kết_quả(self, giao_dịch_tối_ưu, đánh_giá, thời_gian):
        for item in self.tree_giao_dịch.get_children():
            self.tree_giao_dịch.delete(item)
        for gd in giao_dịch_tối_ưu:
            người_trả, người_nhận, số_tiền = gd
            self.tree_giao_dịch.insert("", "end", values=(
    người_trả, 
    người_nhận, 
    format_money(Decimal(str(số_tiền)))
))
        self.text_thống_kê.delete(1.0, tk.END)
        self.text_thống_kê.insert(tk.END, f"Thời gian thực thi: {Decimal(str(thời_gian)):.2f} ms\n\n")
        self.text_thống_kê.insert(tk.END, f"Số giao dịch ban đầu: {đánh_giá['số_giao_dịch_ban_đầu']}\n")
        self.text_thống_kê.insert(tk.END, f"Số giao dịch sau tối ưu: {đánh_giá['số_giao_dịch_tối_ưu']}\n")
        self.text_thống_kê.insert(tk.END, f"Giảm: {đánh_giá['giảm_số_giao_dịch']} giao dịch ({đánh_giá['tỷ_lệ_giảm']:.2f}%)\n\n")
        self.text_thống_kê.insert(tk.END, f"Tổng giá trị giao dịch ban đầu: {đánh_giá['tổng_giá_trị_ban_đầu']:.2f}\n")
        self.text_thống_kê.insert(tk.END, f"Tổng giá trị giao dịch sau tối ưu: {đánh_giá['tổng_giá_trị_tối_ưu']:.2f}\n")
        self.text_thống_kê.insert(tk.END, f"Lưu ý: Giá trị đã bao gồm tiền gốc, lãi và phí phạt quá hạn\n")
        self._vẽ_biểu_đồ_so_sánh(đánh_giá)
        

    

    def _vẽ_biểu_đồ_so_sánh(self, đánh_giá):
        for widget in self.frame_biểu_đồ.winfo_children():
            widget.destroy()
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        labels = ['Trước tối ưu', 'Sau tối ưu']
        số_giao_dịch = [đánh_giá['số_giao_dịch_ban_đầu'], đánh_giá['số_giao_dịch_tối_ưu']]
        ax1.bar(labels, số_giao_dịch, color=['#FF9999', '#66B2FF'])
        ax1.set_ylabel('Số lượng giao dịch')
        ax1.set_title('So sánh số lượng giao dịch')
        for i, v in enumerate(số_giao_dịch):
            ax1.text(i, v + 0.1, str(v), ha='center')
        giá_trị = [đánh_giá['tổng_giá_trị_ban_đầu'], đánh_giá['tổng_giá_trị_tối_ưu']]
        ax2.bar(labels, giá_trị, color=['#FF9999', '#66B2FF'])
        ax2.set_ylabel('Tổng giá trị')
        ax2.set_title('So sánh tổng giá trị giao dịch')
        for i, v in enumerate(giá_trị):
            ax2.text(i, float(v) + 0.1, f"{float(v):.2f}", ha='center')
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.frame_biểu_đồ)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _vẽ_đồ_thị(self, danh_sách_nợ_ban_đầu, giao_dịch_tối_ưu):
        """Vẽ hai đồ thị: đồ thị ban đầu và đồ thị sau tối ưu"""
        # Xóa đồ thị cũ
        for widget in self.frame_đồ_thị_ban_đầu.winfo_children():
            widget.destroy()
        for widget in self.frame_đồ_thị_tối_ưu.winfo_children():
            widget.destroy()

        # 1. Vẽ đồ thị ban đầu
        fig1, ax1 = plt.subplots(figsize=(8, 6))
        G_ban_đầu = Graph()

        # Điều chỉnh node_size và font
        circle_radius = Decimal('0.05')  # Tăng từ 0.03 lên 0.05
        font_size = 12  # Tăng font size
        
        # Thêm các đỉnh và cạnh
        for i in range(self.đồ_thị.danh_sách_đỉnh.size):
            G_ban_đầu.add_node(self.đồ_thị.danh_sách_đỉnh[i])
        for nguồn, đích, giá_trị in danh_sách_nợ_ban_đầu:
            G_ban_đầu.add_edge(nguồn, đích, Decimal(str(giá_trị)))
        
        # Tính vị trí các đỉnh
        pos_ban_đầu = G_ban_đầu.spring_layout(k=Decimal('2'), iterations=100, seed=42)
        
        # Vẽ các đỉnh
        for node in G_ban_đầu.nodes:
            x, y = pos_ban_đầu[node]
            circle = plt.Circle((float(x), float(y)), Decimal('0.03'), color='lightblue', zorder=2)
            ax1.add_artist(circle)

            ax1.text(float(x), float(y), node,
                horizontalalignment='center',
                verticalalignment='center', 
                fontsize=font_size,
                fontweight='bold',
                color='darkblue',
                bbox=dict(
                    facecolor='white',
                    edgecolor='blue',
                    alpha=0.7,
                    pad=3
                ))

        # Vẽ các cạnh có hướng và nhãn
        for source, target, weight in G_ban_đầu.edges:
            x1, y1 = float(pos_ban_đầu[source][0]), float(pos_ban_đầu[source][1])
            x2, y2 = float(pos_ban_đầu[target][0]), float(pos_ban_đầu[target][1])
            
            # Kiểm tra xem có cạnh ngược chiều không
            has_reverse = any(e for e in G_ban_đầu.edges if e[0] == target and e[1] == source)
            
            # Điều chỉnh độ cong và offset cho cạnh có hướng ngược
            if has_reverse:
                # Cạnh thứ nhất cong về một bên
                rad = Decimal('0.3')  # Độ cong lớn hơn
                label_offset = Decimal('0.8')  # Offset lớn hơn
            else:
                # Cạnh đơn cong ít hơn
                rad = Decimal('0.1')
                label_offset = Decimal('0.5')  

            middle_x = (Decimal(str(x1)) + Decimal(str(x2))) / Decimal('2') - (Decimal(str(y2 - y1)) * rad * label_offset)
            middle_y = (Decimal(str(y1)) + Decimal(str(y2))) / Decimal('2') + (Decimal(str(x2 - x1)) * rad * label_offset)
            
            ax1.annotate("",
                xy=(x2, y2), 
                xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="->",
                    connectionstyle=f"arc3,rad={float(rad)}",
                    color='navy',
                    lw=1.0,
                    alpha=0.7
                ))
            
            ax1.text(float(middle_x), float(middle_y),
        format_money(Decimal(str(weight))),
        horizontalalignment='center',
        verticalalignment='center',
        bbox=dict(
            facecolor='white',  # Đặt màu nền trắng 
            edgecolor='lightgray',  # Viền xám nhạt
            alpha=0.8,  # Tăng độ đục
            pad=2 # Thêm padding
        ))
        
        ax1.set_title("Đồ thị dòng tiền ban đầu", pad=20, fontsize=14, fontweight='bold', color='navy')
        ax1.axis('off')
        ax1.set_xlim(-Decimal('0.2'), Decimal('1.2'))
        ax1.set_ylim(-Decimal('0.2'), Decimal('1.2'))
        plt.tight_layout()
        
        # Hiển thị đồ thị ban đầu
        canvas1 = FigureCanvasTkAgg(fig1, master=self.frame_đồ_thị_ban_đầu)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 2. Vẽ đồ thị tối ưu
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        G_tối_ưu = Graph()

        
        plt.tight_layout(pad=3.0)
        
        # Thêm các đỉnh và cạnh
        for i in range(self.đồ_thị.danh_sách_đỉnh.size):
            G_tối_ưu.add_node(self.đồ_thị.danh_sách_đỉnh[i])
        for nguồn, đích, giá_trị in giao_dịch_tối_ưu:
            G_tối_ưu.add_edge(nguồn, đích, Decimal(str(giá_trị)))
        
        # Tính vị trí các đỉnh (sử dụng cùng seed để có layout tương tự)
        pos_tối_ưu = G_tối_ưu.spring_layout(k=Decimal('2'), iterations=100, seed=42)
        
        # Vẽ các đỉnh
        for node in G_tối_ưu.nodes:
            x, y = pos_tối_ưu[node]
            circle = plt.Circle((float(x), float(y)), float(circle_radius), color='lightgreen', ec='blue', lw = 2, alpha = 0.8, zorder=2)
            ax2.add_artist(circle)
            ax2.text(float(x), float(y), node,
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=10,
                    fontweight='bold',
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

        # Vẽ các cạnh có hướng và nhãn
        for source, target, weight in G_tối_ưu.edges:
            x1, y1 = float(pos_tối_ưu[source][0]), float(pos_tối_ưu[source][1])
            x2, y2 = float(pos_tối_ưu[target][0]), float(pos_tối_ưu[target][1])
            
            rad = Decimal('0.2')
            middle_x = (Decimal(str(x1)) + Decimal(str(x2))) / Decimal('2') - (Decimal(str(y2 - y1)) * rad)
            middle_y = (Decimal(str(y1)) + Decimal(str(y2))) / Decimal('2') + (Decimal(str(x2 - x1)) * rad)
            
            ax2.annotate("",
                xy=(x2, y2), xycoords='data',
                xytext=(x1, y1), textcoords='data',
                arrowprops=dict(
                    arrowstyle="->",
                    connectionstyle=f"arc3,rad={float(rad)}",
                    color='red',
                    alpha=0.6,
                    linewidth=1.5
                )
            )
            
            ax2.text(float(middle_x), float(middle_y),
                    format_money(Decimal(str(weight))),
                    horizontalalignment='center',
                    verticalalignment='center',
                    bbox=dict(facecolor='none', edgecolor='none', alpha=0.7))

        ax2.set_title("Đồ thị dòng tiền tối ưu", pad=20, fontsize=12, fontweight='bold')
        ax2.axis('off')
        ax2.set_xlim(-0.1, 1.1)
        ax2.set_ylim(-0.1, 1.1)
        plt.tight_layout()
        
        # Hiển thị đồ thị tối ưu
        canvas2 = FigureCanvasTkAgg(fig2, master=self.frame_đồ_thị_tối_ưu)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Chuyển đến tab đồ thị
        self.tab_control.select(2)
    

    def _tạo_dữ_liệu_mẫu(self):
        if not messagebox.askyesno("Xác nhận", "Bạn có muốn tạo dữ liệu mẫu để thử nghiệm?"):
            return
            

        
        try:
            # Xóa dữ liệu cũ và đồng bộ kết nối
            self._xóa_dữ_liệu()
            
            # Danh sách người dùng mẫu
            người_dùng_mẫu = ["An", "Bình", "Cường", "Dung", "Hùng"]
            for tên in người_dùng_mẫu:
                self.đồ_thị.thêm_đỉnh(tên)
                self.tree_người_dùng.insert("", "end", values=(tên,))
            
            # Dữ liệu khoản nợ mẫu với đầy đủ thông tin
                khoản_nợ_mẫu = [
                ("An", "Bình", 5000000.00, "2025-03-20", "2025-04-05", 5.0, 1.0),
                ("Bình", "Cường", 3500000.00, "2025-03-25", "2025-04-10", 4.5, 1.5),
                ("Cường", "Dung", 4200000.00, "2025-03-28", "2025-04-15", 5.5, 1.0),
                ("Dung", "An", 2800000.00, "2025-03-29", "2025-04-20", 3.5, 0.5),
                ("An", "Hùng", 6500000.00, "2025-03-30", "2025-04-25", 6.0, 2.0),
                ("Hùng", "Bình", 1500000.00, "2025-03-27", "2025-04-07", 4.0, 1.0),
                ("Cường", "An", 2500000.00, "2025-03-26", "2025-05-01", 5.0, 1.5),
                ("Dung", "Hùng", 3800000.00, "2025-03-28", "2025-04-18", 4.8, 1.2),
                ("Bình", "An", 4500000.00, "2025-03-22", "2025-04-12", 5.2, 1.8),
                ("Hùng", "Cường", 5200000.00, "2025-03-24", "2025-04-14", 4.7, 1.3)
            ]
            
            # Chèn dữ liệu vào MySQL và cập nhật giao diện
            for nguồn, đích, giá_trị, ngày_gd, hạn, lãi, phí in khoản_nợ_mẫu:
                # Thêm vào đồ thị
                self.đồ_thị.thêm_cạnh(nguồn, đích, giá_trị, lưu_vào_db=False)
                
                # Thêm vào giao diện
                self.tree_nợ.insert("", "end", values=(
                    nguồn, đích, f"{giá_trị:.2f}", 
                    hạn, f"{lãi}%", f"{phí}%"
                ))

                # Nếu có kết nối MySQL thì lưu vào database
                if self.conn and self.cursor:
                    self.cursor.execute(
                        """
                        INSERT INTO debts (from_person, to_person, amount, 
                                        transaction_date, due_date, 
                                        interest_rate, late_fee_rate)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (nguồn, đích, giá_trị, ngày_gd, hạn, lãi, phí)
                    )
                    self.conn.commit()

            # Cập nhật combobox và giao diện
            self._cập_nhật_combobox()
            if self.conn and self.cursor:
                self._cập_nhật_tình_trạng_nợ()
                
            messagebox.showinfo("Thành công", "Đã tạo dữ liệu mẫu!")

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            messagebox.showerror("Lỗi", f"Lỗi tạo dữ liệu mẫu: {str(e)}")

    def _kiểm_tra_thông_báo(self):
        """Hiển thị thông báo về các khoản nợ sắp đến hạn và các khoản nợ đã quá hạn"""
        hôm_nay = time.strftime("%Y-%m-%d")
        hôm_nay_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
        
        # Lấy tất cả các khoản nợ có ngày đến hạn
        self.cursor.execute("""
            SELECT from_person, to_person, amount, due_date, late_fee_rate 
            FROM debts 
            WHERE due_date IS NOT NULL
        """)
        danh_sách_nợ = self.cursor.fetchall()
        
        # Danh sách các khoản nợ sắp đến hạn và đã quá hạn
        khoản_nợ_sắp_đến_hạn = []
        khoản_nợ_quá_hạn = []
        
        for người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, phí_phạt in danh_sách_nợ:
            ngày_đến_hạn_datetime = time.strptime(str(ngày_đến_hạn), "%Y-%m-%d")
            chênh_lệch = (time.mktime(ngày_đến_hạn_datetime) - time.mktime(hôm_nay_datetime)) / (24 * 3600)
            
            # Kiểm tra khoản nợ sắp đến hạn (trong vòng 7 ngày)
            if 0 <= chênh_lệch <= 7:
                khoản_nợ_sắp_đến_hạn.append((người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, int(chênh_lệch)))
            
            # Kiểm tra khoản nợ đã quá hạn
            elif chênh_lệch < 0:
                số_ngày_quá_hạn = abs(int(chênh_lệch))
                # Tính phí phạt: (số tiền gốc * phí phạt % * số ngày quá hạn) / 30
                tiền_phạt = (số_tiền * (phí_phạt / 100) * số_ngày_quá_hạn) / 30
                khoản_nợ_quá_hạn.append((người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, số_ngày_quá_hạn, tiền_phạt))
        
        # Hiển thị thông báo
        thông_báo = ""
        
        # Thông báo các khoản nợ sắp đến hạn
        if khoản_nợ_sắp_đến_hạn:
            thông_báo += "Các khoản nợ sắp đến hạn:\n\n"
            for người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, ngày_còn_lại in khoản_nợ_sắp_đến_hạn:
                thông_báo += f"- {người_nợ} nợ {người_cho_vay} {số_tiền:.2f} (Hạn: {ngày_đến_hạn}, còn {ngày_còn_lại} ngày)\n"
        
        # Thông báo các khoản nợ đã quá hạn
        if khoản_nợ_quá_hạn:
            if thông_báo:
                thông_báo += "\n"  # Thêm khoảng cách nếu đã có thông báo trước đó
            thông_báo += "Các khoản nợ đã quá hạn:\n\n"
            for người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, số_ngày_quá_hạn, tiền_phạt in khoản_nợ_quá_hạn:
                thông_báo += f"- {người_nợ} nợ {người_cho_vay} {số_tiền:.2f} (Hạn: {ngày_đến_hạn}, quá hạn {số_ngày_quá_hạn} ngày, phí phạt: {tiền_phạt:.2f})\n"
        
        # Hiển thị thông báo nếu có nội dung
        if thông_báo:
            messagebox.showwarning("Thông báo", thông_báo)

    def _tải_dữ_liệu_từ_mysql(self):
        try:
            # Xóa dữ liệu hiện tại
            self.đồ_thị.danh_sách_đỉnh = DynamicArray()
            self.đồ_thị.ma_trận_kề = DynamicArray()
            self.đồ_thị.số_đỉnh = 0
            
            # Xóa dữ liệu trên giao diện
            for item in self.tree_người_dùng.get_children():
                self.tree_người_dùng.delete(item)
            for item in self.tree_nợ.get_children():
                self.tree_nợ.delete(item)
            for item in self.tree_tình_trạng.get_children():
                self.tree_tình_trạng.delete(item)
            
            # Tải lại danh sách người dùng
            self.cursor.execute("SELECT DISTINCT from_person FROM debts UNION SELECT DISTINCT to_person FROM debts")
            người_dùng = self.cursor.fetchall()
            for (tên,) in người_dùng:
                if tên and tên not in self.đồ_thị.danh_sách_đỉnh:
                    self.đồ_thị.thêm_đỉnh(tên)
                    self.tree_người_dùng.insert("", "end", values=(tên,))
            
            # Tải lại danh sách nợ
            self.cursor.execute("""
                SELECT d.id, d.from_person, d.to_person, d.amount,
                    d.transaction_date, d.due_date, d.interest_rate, d.late_fee_rate,
                    COALESCE(SUM(p.amount), 0) as paid_amount
                FROM debts d
                LEFT JOIN payments p ON d.id = p.debt_id
                GROUP BY d.id
                ORDER BY d.due_date ASC
            """)
            
            khoản_nợ = self.cursor.fetchall()
            for (id, người_nợ, người_cho_vay, số_tiền, ngày_gd, ngày_đến_hạn, lãi_suất, phí_phạt, đã_trả) in khoản_nợ:
                số_tiền_còn_lại = Decimal(str(số_tiền)) - Decimal(str(đã_trả))
                if số_tiền_còn_lại > Decimal('0'):  # Thay vì > 0
                    self.đồ_thị.thêm_cạnh(người_nợ, người_cho_vay, số_tiền_còn_lại, lưu_vào_db=False)
                    self.tree_nợ.insert("", "end", values=(
                        người_nợ, người_cho_vay, f"{số_tiền_còn_lại:.2f}",
                        ngày_đến_hạn, f"{lãi_suất}%", f"{phí_phạt}%"
                    ))
            
            # Cập nhật combobox và tình trạng nợ
            self._cập_nhật_combobox()
            self._cập_nhật_tình_trạng_nợ()
            
            messagebox.showinfo("Thành công", "Đã tải lại dữ liệu từ MySQL!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Lỗi", f"Không thể tải dữ liệu: {err}")

    def _ghi_nhận_thanh_toán(self):
        """Ghi nhận thanh toán cho khoản nợ được chọn"""
        selected_item = self.tree_tình_trạng.selection()
        if not selected_item:
            messagebox.showerror("Lỗi", "Vui lòng chọn một khoản nợ để thanh toán!")
            return

        try:
            # Lấy thông tin khoản nợ được chọn
            values = self.tree_tình_trạng.item(selected_item, 'values')
            người_nợ = values[0]
            người_cho_vay = values[1]
            số_tiền_gốc = Decimal(str(values[2]).replace(",", ""))
            ngày_giao_dịch = values[3]
            ngày_đến_hạn = values[4]
            lãi_suất = Decimal(str(values[5]).replace("%", ""))
            phí_phạt = Decimal(str(values[6]).replace("%", ""))
            tiền_lãi = Decimal(str(values[8]).replace(",", ""))
            tiền_phạt = Decimal(str(values[9]).replace(",", ""))
            tổng_tiền = Decimal(str(values[10]).replace(",", ""))

            # Nhập số tiền thanh toán
            số_tiền_thanh_toán_str = simpledialog.askstring(
                "Thanh toán", 
                f"Nhập số tiền thanh toán (tối đa {format_money(tổng_tiền)}):"
            )
            if số_tiền_thanh_toán_str is None:
                return

            số_tiền_thanh_toán = Decimal(số_tiền_thanh_toán_str.replace(",", ""))
            if số_tiền_thanh_toán <= Decimal('0'):
                raise ValueError("Số tiền phải lớn hơn 0")
            if số_tiền_thanh_toán > tổng_tiền:
                raise ValueError(f"Số tiền không được vượt quá {format_money(tổng_tiền)}")

            # Phân bổ thanh toán theo thứ tự: phí phạt -> lãi -> gốc
            số_tiền_còn_lại = số_tiền_thanh_toán
            số_tiền_trừ_phí_phạt = Decimal('0')
            số_tiền_trừ_lãi = Decimal('0') 
            số_tiền_trừ_gốc = Decimal('0')

            # 1. Trừ phí phạt trước
            if tiền_phạt > Decimal('0'):
                số_tiền_trừ_phí_phạt = min(số_tiền_còn_lại, tiền_phạt)
                số_tiền_còn_lại -= số_tiền_trừ_phí_phạt

            # 2. Trừ tiền lãi 
            if tiền_lãi > Decimal('0') and số_tiền_còn_lại > Decimal('0'):
                số_tiền_trừ_lãi = min(số_tiền_còn_lại, tiền_lãi)
                số_tiền_còn_lại -= số_tiền_trừ_lãi

            # 3. Trừ tiền gốc
            if số_tiền_còn_lại > Decimal('0'):
                số_tiền_trừ_gốc = min(số_tiền_còn_lại, số_tiền_gốc)

            # Cập nhật cơ sở dữ liệu nếu có kết nối
            if self.conn and self.cursor:
                self.cursor.execute("""
                    SELECT id FROM debts 
                    WHERE from_person = %s AND to_person = %s
                    AND amount >= %s
                    ORDER BY transaction_date DESC 
                    LIMIT 1
                """, (người_nợ, người_cho_vay, số_tiền_gốc))
                
                result = self.cursor.fetchone()
                if not result:
                    raise ValueError("Không tìm thấy khoản nợ trong cơ sở dữ liệu")
                debt_id = result[0]

                # Ghi nhận thanh toán
                self.cursor.execute("""
                    INSERT INTO payments 
                    (debt_id, amount, payment_date, fee_amount, interest_amount, principal_amount)
                    VALUES (%s, %s, NOW(), %s, %s, %s)
                """, (
                    debt_id,
                    str(số_tiền_thanh_toán),
                    str(số_tiền_trừ_phí_phạt),
                    str(số_tiền_trừ_lãi),
                    str(số_tiền_trừ_gốc)
                ))
                self.conn.commit()

            # Cập nhật ma trận kề
            i = self.đồ_thị.danh_sách_đỉnh.index(người_nợ)
            j = self.đồ_thị.danh_sách_đỉnh.index(người_cho_vay)
            số_tiền_gốc_mới = max(Decimal('0'), số_tiền_gốc - số_tiền_trừ_gốc)
            tiền_lãi_mới = max(Decimal('0'), tiền_lãi - số_tiền_trừ_lãi)
            tiền_phạt_mới = max(Decimal('0'), tiền_phạt - số_tiền_trừ_phí_phạt)
            
            # Kiểm tra nếu đã thanh toán hết
            if (số_tiền_gốc_mới == Decimal('0') and 
                tiền_lãi_mới == Decimal('0') and 
                tiền_phạt_mới == Decimal('0')):
                
                # Xóa khỏi ma trận kề
                self.đồ_thị.ma_trận_kề[i][j] = Decimal('0')
                
                # Xóa khỏi tree_tình_trạng
                self.tree_tình_trạng.delete(selected_item[0])
                
                # Xóa khỏi tree_nợ
                for item in self.tree_nợ.get_children():
                    values = self.tree_nợ.item(item)['values']
                    if values[0] == người_nợ and values[1] == người_cho_vay:
                        self.tree_nợ.delete(item)
                        break
                
                messagebox.showinfo("Thành công", 
                    f"Đã thanh toán hết khoản nợ!\n"
                    f"Chi tiết thanh toán cuối cùng:\n"
                    f"- Phí phạt: {format_money(số_tiền_trừ_phí_phạt)}\n"
                    f"- Lãi: {format_money(số_tiền_trừ_lãi)}\n"
                    f"- Gốc: {format_money(số_tiền_trừ_gốc)}"
                )
            else:
                # Cập nhật ma trận kề với số tiền gốc mới
                self.đồ_thị.ma_trận_kề[i][j] = số_tiền_gốc_mới

                # Update displays
                self.tree_tình_trạng.set(selected_item[0], column=2, value=format_money(số_tiền_gốc_mới))
                self.tree_tình_trạng.set(selected_item[0], column=8, value=format_money(tiền_lãi_mới))
                self.tree_tình_trạng.set(selected_item[0], column=9, value=format_money(tiền_phạt_mới))
                self.tree_tình_trạng.set(selected_item[0], column=10, 
                    value=format_money(số_tiền_gốc_mới + tiền_lãi_mới + tiền_phạt_mới))

                # Cập nhật tree_nợ
                for item in self.tree_nợ.get_children():
                    values = self.tree_nợ.item(item)['values']  
                    if values[0] == người_nợ and values[1] == người_cho_vay:
                        self.tree_nợ.set(item, column=2, value=format_money(số_tiền_gốc_mới))
                        break

                messagebox.showinfo("Thành công", 
                    f"Đã ghi nhận thanh toán {format_money(số_tiền_thanh_toán)}!\n"
                    f"Chi tiết:\n"
                    f"- Phí phạt: {format_money(số_tiền_trừ_phí_phạt)} ({format_money(tiền_phạt_mới)} còn lại)\n"
                    f"- Lãi: {format_money(số_tiền_trừ_lãi)} ({format_money(tiền_lãi_mới)} còn lại)\n"
                    f"- Gốc: {format_money(số_tiền_trừ_gốc)} ({format_money(số_tiền_gốc_mới)} còn lại)"
                )

        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except mysql.connector.Error as err:
            if self.conn:
                self.conn.rollback()
            messagebox.showerror("Lỗi MySQL", f"Lỗi cập nhật cơ sở dữ liệu: {err}")
        except Exception as e:
            if self.conn:
                self.conn.rollback()
            messagebox.showerror("Lỗi", f"Lỗi không xác định: {str(e)}")

    def _xóa_dữ_liệu(self):
            """Xóa toàn bộ dữ liệu trong chương trình và cơ sở dữ liệu"""
            if not messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa tất cả dữ liệu?"):
                return
                
            try:
                # Xóa dữ liệu trong MySQL nếu có kết nối
                if self.conn and self.cursor:
                    # Xóa theo thứ tự để tránh lỗi khóa ngoại
                    self.cursor.execute("DELETE FROM payments")
                    self.cursor.execute("DELETE FROM debts")
                    self.conn.commit()
                
                # Reset đồ thị
                self.đồ_thị.danh_sách_đỉnh = DynamicArray()
                self.đồ_thị.ma_trận_kề = DynamicArray()
                self.đồ_thị.số_đỉnh = 0
                
                # Xóa dữ liệu trên giao diện
                for item in self.tree_người_dùng.get_children():
                    self.tree_người_dùng.delete(item)
                for item in self.tree_nợ.get_children():
                    self.tree_nợ.delete(item)
                for item in self.tree_giao_dịch.get_children():
                    self.tree_giao_dịch.delete(item)
                for item in self.tree_tình_trạng.get_children():
                    self.tree_tình_trạng.delete(item)
                    
                # Xóa nội dung text và combobox
                self.text_thống_kê.delete(1.0, tk.END)
                self.combo_người_nợ.set('')
                self.combo_người_cho_vay.set('')
                self.combo_người_nợ['values'] = []
                self.combo_người_cho_vay['values'] = []
                
                # Xóa đồ thị
                for widget in self.frame_đồ_thị_ban_đầu.winfo_children():
                    widget.destroy()
                for widget in self.frame_đồ_thị_tối_ưu.winfo_children():
                    widget.destroy()
                
                messagebox.showinfo("Thành công", "Đã xóa tất cả dữ liệu!")
                
            except mysql.connector.Error as err:
                messagebox.showerror("Lỗi", f"Không thể xóa dữ liệu: {err}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi không xác định: {str(e)}")

class SQL_Login(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Kết nối MySQL Server")
        self.geometry("400x300")

        self.center_window()

        # Make window modal
        self.transient(self.master)
        self.grab_set()
        
        # Cấu hình mặc định
        self.config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'cashflow_db'
        }
        
        # GUI elements
        ttk.Label(self, text="MySQL Server Configuration", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(self)
        frame.pack(padx=20, pady=10, fill='x')
        
        # Host
        ttk.Label(frame, text="Host:").grid(row=0, column=0, sticky='w', pady=5)
        self.host_entry = ttk.Entry(frame)
        self.host_entry.insert(0, self.config['host'])
        self.host_entry.grid(row=0, column=1, sticky='ew', pady=5)
        
        # Port
        ttk.Label(frame, text="Port:").grid(row=1, column=0, sticky='w', pady=5)
        self.port_entry = ttk.Entry(frame)
        self.port_entry.insert(0, str(self.config['port']))
        self.port_entry.grid(row=1, column=1, sticky='ew', pady=5)
        
        # Username
        ttk.Label(frame, text="Username:").grid(row=2, column=0, sticky='w', pady=5)
        self.user_entry = ttk.Entry(frame)
        self.user_entry.insert(0, self.config['user'])
        self.user_entry.grid(row=2, column=1, sticky='ew', pady=5)
        
        # Password
        ttk.Label(frame, text="Password:").grid(row=3, column=0, sticky='w', pady=5)
        self.pass_entry = ttk.Entry(frame, show='*')
        self.pass_entry.insert(0, self.config['password'])  # Thêm dòng này
        self.pass_entry.grid(row=3, column=1, sticky='ew', pady=5)
        
        # Database
        ttk.Label(frame, text="Database:").grid(row=4, column=0, sticky='w', pady=5)
        self.db_entry = ttk.Entry(frame)
        self.db_entry.insert(0, self.config['database'])
        self.db_entry.grid(row=4, column=1, sticky='ew', pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Kết nối", command=self.connect).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Hủy", command=self.cancel).pack(side='left')
        
        self.result = None
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Bind Enter key to connect
        self.bind('<Return>', lambda event: self.connect())
        
        # Set initial focus to password field
        self.pass_entry.focus()

    def center_window(self):
        """Center the window on the screen"""
        # Update window size
        self.update_idletasks()
        
        # Get screen width and height
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calculate position x, y
        size = tuple(int(_) for _ in self.geometry().split('+')[0].split('x'))
        x = screen_width//2 - size[0]//2
        y = screen_height//2 - size[1]//2
        
        # Set the position
        self.geometry(f"+{x}+{y}")
        
    def connect(self):
        try:
            self.config.update({
                'host': self.host_entry.get(),
                'port': int(self.port_entry.get()),
                'user': self.user_entry.get(),
                'password': self.pass_entry.get(),
                'database': self.db_entry.get()
            })
            # Tạo kết nối và cursor
            conn = mysql.connector.connect(**self.config)
            cursor = conn.cursor()
            
            # Tạo các bảng nếu chưa tồn tại
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                from_person VARCHAR(50),
                to_person VARCHAR(50),
                amount DECIMAL(15, 2),  # Increased precision
                transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date DATE,
                interest_rate DECIMAL(5, 2) DEFAULT 0.0,
                late_fee_rate DECIMAL(5, 2) DEFAULT 0.0
            )
            """)
            
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                debt_id INT,
                amount DECIMAL(15, 2),
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                fee_amount DECIMAL(15,2) DEFAULT 0,
                interest_amount DECIMAL(15,2) DEFAULT 0, 
                principal_amount DECIMAL(15,2) DEFAULT 0,
                FOREIGN KEY (debt_id) REFERENCES debts(id)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                from_person VARCHAR(50),
                to_person VARCHAR(50),
                amount DECIMAL(10, 2)
            )
            """)
            
            conn.commit()
            self.result = (conn, cursor)
            self.destroy()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Lỗi", f"Không thể kết nối: {err}")
            self.result = None
            
    def cancel(self):
        self.result = None
        self.destroy()
        
def main():
    app = None  # Khởi tạo app là None trước khi try
    try:
        root = tk.Tk()
        app = Giao_Diện_Người_Dùng(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi không mong muốn: {str(e)}")
    finally:
        # Kiểm tra app và kết nối trước khi đóng
        if app and hasattr(app, 'conn') and app.conn:
            try:
                app.conn.close()
            except:
                pass  # Bỏ qua lỗi khi đóng kết nối

if __name__ == "__main__":
    main()