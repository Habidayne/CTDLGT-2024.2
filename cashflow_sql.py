import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
import mysql.connector  
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
from tkcalendar import DateEntry
from decimal import Decimal

class Đồ_Thị:

    def __init__(self, conn=None, cursor=None):
        self.danh_sách_đỉnh = []
        self.ma_trận_kề = []
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
            self.ma_trận_kề = [[0] * self.số_đỉnh for _ in range(self.số_đỉnh)]
            
            # Cập nhật ma trận kề
            for người_nợ, người_cho_vay, số_tiền, đã_trả in self.cursor.fetchall():
                if người_nợ in self.danh_sách_đỉnh and người_cho_vay in self.danh_sách_đỉnh:
                    i = self.danh_sách_đỉnh.index(người_nợ)
                    j = self.danh_sách_đỉnh.index(người_cho_vay)
                    số_tiền_còn_lại = float(số_tiền) - float(đã_trả)
                    if số_tiền_còn_lại > 0:
                        self.ma_trận_kề[i][j] = số_tiền_còn_lại
                        
        except mysql.connector.Error as err:
            print(f"Lỗi đồng bộ dữ liệu: {err}")
    
    def thêm_đỉnh(self, tên):
        if tên in self.danh_sách_đỉnh:
            return False
        self.danh_sách_đỉnh.append(tên)
        self.số_đỉnh += 1
        if self.số_đỉnh == 1:
            self.ma_trận_kề = [[0]]
        else:
            for i in range(self.số_đỉnh - 1):
                self.ma_trận_kề[i].append(0)
            self.ma_trận_kề.append([0] * self.số_đỉnh)
        return True
    
    def thêm_cạnh(self, nguồn, đích, giá_trị, lưu_vào_db=True):
        if nguồn not in self.danh_sách_đỉnh or đích not in self.danh_sách_đỉnh:
            return False
        chỉ_mục_nguồn = self.danh_sách_đỉnh.index(nguồn)
        chỉ_mục_đích = self.danh_sách_đỉnh.index(đích)
        self.ma_trận_kề[chỉ_mục_nguồn][chỉ_mục_đích] += giá_trị
    
        # Chỉ lưu vào MySQL khi cần thiết
        if lưu_vào_db:
            self.cursor.execute(
                "INSERT INTO debts (from_person, to_person, amount) VALUES (%s, %s, %s)",
                (nguồn, đích, giá_trị)
            )
            self.conn.commit()
        return True
    
    def đọc_ma_trận_kề(self):
        return self.ma_trận_kề
    
    def tính_số_dư_ròng(self):
        số_dư = [0] * self.số_đỉnh
        for i in range(self.số_đỉnh):
            for j in range(self.số_đỉnh):
                số_dư[i] -= self.ma_trận_kề[i][j]
                số_dư[i] += self.ma_trận_kề[j][i]
        return số_dư
    
    def tính_tổng_nợ(self):
        tổng = 0
        for i in range(self.số_đỉnh):
            for j in range(self.số_đỉnh):
                tổng += self.ma_trận_kề[i][j]
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
            
            # Tính số ngày từ ngày giao dịch
            ngày_giao_dịch_obj = time.strptime(str(ngày_giao_dịch), "%Y-%m-%d %H:%M:%S")
            ngày_giao_dịch_date = time.strftime("%Y-%m-%d", ngày_giao_dịch_obj)
            ngày_giao_dịch_datetime = time.strptime(ngày_giao_dịch_date, "%Y-%m-%d")
            ngày_hiện_tại_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
            số_ngày = (time.mktime(ngày_hiện_tại_datetime) - time.mktime(ngày_giao_dịch_datetime)) / (24 * 3600)
            
            # Tính lãi
            lãi_hàng_ngày = số_tiền_gốc * (lãi_suất / 100) / 365
            tiền_lãi = lãi_hàng_ngày * số_ngày
            
            # Tính phí phạt nếu quá hạn
            tiền_phạt = 0
            if ngày_đến_hạn:
                ngày_đến_hạn_datetime = time.strptime(str(ngày_đến_hạn), "%Y-%m-%d")
                if ngày_hiện_tại_datetime > ngày_đến_hạn_datetime:
                    số_ngày_quá_hạn = (time.mktime(ngày_hiện_tại_datetime) - time.mktime(ngày_đến_hạn_datetime)) / (24 * 3600)
                    tiền_phạt = số_tiền_gốc * (phí_phạt / 100) * số_ngày_quá_hạn / 30  # Phí phạt hàng tháng
            
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
        số_dư = self.đồ_thị.tính_số_dư_ròng()
        danh_sách_người_dùng = self.đồ_thị.danh_sách_đỉnh
        chỉ_mục_số_dư = [(i, số_dư[i]) for i in range(len(số_dư))]
        
        người_nhận = [(i, val) for i, val in chỉ_mục_số_dư if val > 0]
        người_trả = [(i, val) for i, val in chỉ_mục_số_dư if val < 0]
        
        người_nhận.sort(key=lambda x: x[1], reverse=True)
        người_trả.sort(key=lambda x: x[1])
        
        giao_dịch_tối_ưu = []
        i, j = 0, 0
        
        while i < len(người_trả) and j < len(người_nhận):
            người_trả_idx, số_tiền_trả = người_trả[i]
            người_nhận_idx, số_tiền_nhận = người_nhận[j]
            số_tiền_giao_dịch = min(abs(số_tiền_trả), số_tiền_nhận)
            giao_dịch_tối_ưu.append((
                danh_sách_người_dùng[người_trả_idx],
                danh_sách_người_dùng[người_nhận_idx],
                số_tiền_giao_dịch
            ))
            số_tiền_trả += số_tiền_giao_dịch
            số_tiền_nhận -= số_tiền_giao_dịch
            người_trả[i] = (người_trả_idx, số_tiền_trả)
            người_nhận[j] = (người_nhận_idx, số_tiền_nhận)
            if abs(số_tiền_trả) < 1e-6:
                i += 1
            if số_tiền_nhận < 1e-6:
                j += 1
        
        # Lưu giao dịch tối ưu vào MySQL
        self.đồ_thị.cursor.execute("DELETE FROM transactions")
        for from_p, to_p, amount in giao_dịch_tối_ưu:
            self.đồ_thị.cursor.execute(
                "INSERT INTO transactions (from_person, to_person, amount) VALUES (%s, %s, %s)",
                (from_p, to_p, amount)
            )
        self.đồ_thị.conn.commit()
        
        return giao_dịch_tối_ưu
    
    def đánh_giá_hiệu_năng(self, giao_dịch_tối_ưu):
        danh_sách_nợ_ban_đầu = self.đồ_thị.lấy_danh_sách_nợ()
        số_giao_dịch_ban_đầu = len(danh_sách_nợ_ban_đầu)
        số_giao_dịch_tối_ưu = len(giao_dịch_tối_ưu)
        tổng_giá_trị_ban_đầu = sum(nợ[2] for nợ in danh_sách_nợ_ban_đầu)
        tổng_giá_trị_tối_ưu = sum(gd[2] for gd in giao_dịch_tối_ưu)
        return {
            'số_giao_dịch_ban_đầu': số_giao_dịch_ban_đầu,
            'số_giao_dịch_tối_ưu': số_giao_dịch_tối_ưu,
            'tổng_giá_trị_ban_đầu': tổng_giá_trị_ban_đầu,
            'tổng_giá_trị_tối_ưu': tổng_giá_trị_tối_ưu,
            'giảm_số_giao_dịch': số_giao_dịch_ban_đầu - số_giao_dịch_tối_ưu,
            'tỷ_lệ_giảm': (số_giao_dịch_ban_đầu - số_giao_dịch_tối_ưu) / max(1, số_giao_dịch_ban_đầu) * 100
        }

class Giao_Diện_Người_Dùng:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Trình tối ưu hóa dòng tiền")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Hỏi người dùng có muốn kết nối SQL không
        if messagebox.askyesno("Kết nối SQL", "Bạn có muốn kết nối với cơ sở dữ liệu MySQL không?"):
            # Login SQL nếu người dùng chọn Yes
            login = SQL_Login()
            login.wait_window()
            
            if login.result:
                self.conn, self.cursor = login.result
            else:
                # Nếu không kết nối được, vẫn tiếp tục với None
                self.conn = None
                self.cursor = None
        else:
            # Nếu người dùng chọn No, khởi tạo None
            self.conn = None
            self.cursor = None

        self.đồ_thị = Đồ_Thị(self.conn, self.cursor)

        # Tạo tabs
        self.tab_control = ttk.Notebook(root)
        self.tab_nhập_liệu = ttk.Frame(self.tab_control)
        self.tab_kết_quả = ttk.Frame(self.tab_control)
        self.tab_biểu_diễn = ttk.Frame(self.tab_control)
        self.tab_tình_trạng = ttk.Frame(self.tab_control)
        self.tab_đồ_thị = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_nhập_liệu, text="Nhập liệu")
        self.tab_control.add(self.tab_kết_quả, text="Kết quả")
        self.tab_control.add(self.tab_đồ_thị, text="Biểu diễn đồ thị")
        self.tab_control.add(self.tab_tình_trạng, text="Tình trạng nợ")
        self.tab_control.pack(expand=1, fill="both")
        
        self._xây_dựng_tab_nhập_liệu()
        self._xây_dựng_tab_kết_quả()
        self._xây_dựng_tab_đồ_thị()
        self._xây_dựng_tab_tình_trạng()
        
        # Chỉ tải dữ liệu từ MySQL nếu có kết nối
        if self.conn and self.cursor:
            self._tải_dữ_liệu_từ_mysql()
            self._kiểm_tra_thông_báo()

        # Chỉ hiện nút tải dữ liệu nếu có kết nối SQL
        if self.conn and self.cursor:
            self.nút_tải_dữ_liệu = ttk.Button(self.tab_nhập_liệu, text="Tải dữ liệu từ SQL", command=self._tải_dữ_liệu_từ_mysql)
            self.nút_tải_dữ_liệu.pack(pady=10)

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

        ttk.Label(frame_nợ, text="Ngày đến hạn:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.date_due = DateEntry(frame_nợ, width=12, background='darkblue',
                         foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
        self.date_due.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame_nợ, text="Lãi suất (%):").grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.entry_lãi_suất = ttk.Entry(frame_nợ, width=15)
        self.entry_lãi_suất.insert(0, "0.0")
        self.entry_lãi_suất.grid(row=1, column=3, padx=5, pady=5)
        ttk.Label(frame_nợ, text="Phí phạt (%):").grid(row=1, column=4, padx=5, pady=5, sticky="w")
        self.entry_phí_phạt = ttk.Entry(frame_nợ, width=15)
        self.entry_phí_phạt.insert(0, "0.0")
        self.entry_phí_phạt.grid(row=1, column=5, padx=5, pady=5)
        

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

    def _xây_dựng_tab_tình_trạng(self):
        frame_tình_trạng = ttk.LabelFrame(self.tab_tình_trạng, text="Tình trạng các khoản nợ")
        frame_tình_trạng.pack(fill="both", expand=True, padx=20, pady=20)
        
        btn_cập_nhật = ttk.Button(frame_tình_trạng, text="Cập nhật tình trạng nợ", command=self._cập_nhật_tình_trạng_nợ)
        btn_cập_nhật.pack(pady=10)
        
        btn_thanh_toán = ttk.Button(frame_tình_trạng, text="Thanh toán", command=self._ghi_nhận_thanh_toán)
        btn_thanh_toán.pack(pady=10)
        
        self.tree_tình_trạng = ttk.Treeview(frame_tình_trạng, columns=(
            "người_nợ", "người_cho_vay", "số_tiền_gốc", "ngày_giao_dịch", "ngày_đến_hạn", 
            "lãi_suất", "phí_phạt", "số_ngày_quá_hạn", "tổng_phí_phạt", "tổng_tiền"
        ), show="headings")
        self.tree_tình_trạng.heading("người_nợ", text="Người nợ", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "người_nợ", False))
        self.tree_tình_trạng.heading("người_cho_vay", text="Người cho vay", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "người_cho_vay", False))
        self.tree_tình_trạng.heading("số_tiền_gốc", text="Số tiền gốc", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "số_tiền_gốc", True))
        self.tree_tình_trạng.heading("ngày_giao_dịch", text="Ngày giao dịch", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "ngày_giao_dịch", False))
        self.tree_tình_trạng.heading("ngày_đến_hạn", text="Ngày đến hạn", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "ngày_đến_hạn", False))
        self.tree_tình_trạng.heading("lãi_suất", text="Lãi suất", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "lãi_suất", True))
        self.tree_tình_trạng.heading("phí_phạt", text="Phí phạt", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "phí_phạt", True))
        self.tree_tình_trạng.heading("số_ngày_quá_hạn", text="Số ngày quá hạn", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "số_ngày_quá_hạn", True))
        self.tree_tình_trạng.heading("tổng_phí_phạt", text="Tổng phí phạt", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "tổng_phí_phạt", True))
        self.tree_tình_trạng.heading("tổng_tiền", text="Tổng tiền", command=lambda: self._sắp_xếp_treeview(self.tree_tình_trạng, "tổng_tiền", True))
        self.tree_tình_trạng.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Biến để theo dõi trạng thái sắp xếp
        self.sort_states = {}

    def _sắp_xếp_treeview(self, tree, col, is_numeric=False):
        from datetime import datetime
        
        # Lấy tất cả các mục từ tree
        items = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        # Khởi tạo trạng thái sắp xếp nếu chưa có
        if col not in self.sort_states:
            self.sort_states[col] = False  # False = tăng dần
        
        # Đảo ngược trạng thái sắp xếp hiện tại
        self.sort_states[col] = not self.sort_states[col]
        
        # Định nghĩa hàm chuyển đổi ngày rõ ràng
        def convert_date(date_str):
            if not date_str or date_str.strip() == '':
                return datetime.min
            try:
                # Chuyển đổi chuỗi yyyy-mm-dd thành đối tượng datetime
                return datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, AttributeError):
                print(f"Lỗi chuyển đổi ngày: '{date_str}'")
                return datetime.min
        
        # Sắp xếp các mục dựa trên loại dữ liệu và hướng sắp xếp
        if col in ["ngày_giao_dịch", "ngày_đến_hạn"]:
            # Sắp xếp theo ngày
            items.sort(key=lambda x: convert_date(x[0]), reverse=self.sort_states[col])
        elif is_numeric:
            # Chuyển đổi sang số để sắp xếp đúng
            items.sort(key=lambda x: float(x[0].replace(',', '').replace('%', '')) if x[0] and x[0].strip() else 0, 
                    reverse=self.sort_states[col])
        else:
            # Sắp xếp theo chuỗi
            items.sort(key=lambda x: x[0].lower() if x[0] else "", reverse=self.sort_states[col])
        
        # Xóa các mục hiện tại và thêm lại theo thứ tự đã sắp xếp
        for index, (val, id) in enumerate(items):
            tree.move(id, '', index)
        
        # Lưu trữ tiêu đề gốc khi khởi tạo
        if not hasattr(self, 'original_headings'):
            self.original_headings = {}
            for c in tree['columns']:
                self.original_headings[c] = tree.heading(c)['text']
        
        # Cập nhật tiêu đề để hiển thị hướng sắp xếp, giữ nguyên tên đầy đủ
        original_text = self.original_headings[col]
        # Loại bỏ mũi tên cũ nếu có
        if " ↓" in original_text:
            original_text = original_text.replace(" ↓", "")
        if " ↑" in original_text:
            original_text = original_text.replace(" ↑", "")
        
        arrow = " ↓" if self.sort_states[col] else " ↑"
        tree.heading(col, text=original_text + arrow)
        
        # Đặt lại tiêu đề của các cột khác (giữ nguyên tên đầy đủ)
        for c in tree['columns']:
            if c != col:
                original_text = self.original_headings[c]
                if " ↓" in original_text:
                    original_text = original_text.replace(" ↓", "")
                if " ↑" in original_text:
                    original_text = original_text.replace(" ↑", "")
                tree.heading(c, text=original_text)
        
    def _cập_nhật_tình_trạng_nợ(self):
        try:
            # Xóa dữ liệu cũ
            for item in self.tree_tình_trạng.get_children():
                self.tree_tình_trạng.delete(item)
                
            # Nếu không có người dùng, thoát
            if not self.đồ_thị.danh_sách_đỉnh:
                return
                
            hôm_nay = time.strftime("%Y-%m-%d")
            hôm_nay_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
            
            # Chỉ hiển thị các khoản nợ từ ma trận kề
            for i in range(self.đồ_thị.số_đỉnh):
                for j in range(self.đồ_thị.số_đỉnh):
                    số_tiền_gốc = self.đồ_thị.ma_trận_kề[i][j]
                    if số_tiền_gốc > 0.01:  # Chỉ xử lý các khoản nợ còn lại
                        người_nợ = self.đồ_thị.danh_sách_đỉnh[i]
                        người_cho_vay = self.đồ_thị.danh_sách_đỉnh[j]
                        
                        # Lấy thông tin từ database
                        self.cursor.execute("""
                            SELECT transaction_date, due_date, interest_rate, late_fee_rate
                            FROM debts 
                            WHERE from_person = %s AND to_person = %s
                            ORDER BY transaction_date DESC LIMIT 1
                        """, (người_nợ, người_cho_vay))
                        
                        result = self.cursor.fetchone()
                        if result:
                            ngày_gd, ngày_đến_hạn, lãi_suất, phí_phạt = result
                        else:
                            ngày_gd = time.strftime("%Y-%m-%d")
                            ngày_đến_hạn = None
                            lãi_suất = 0
                            phí_phạt = 0
                        
                        # Tính tiền lãi
                        tiền_lãi = 0
                        if ngày_gd:
                            ngày_gd_obj = time.strptime(str(ngày_gd), "%Y-%m-%d %H:%M:%S")
                            ngày_gd_date = time.strftime("%Y-%m-%d", ngày_gd_obj)
                            ngày_gd_datetime = time.strptime(ngày_gd_date, "%Y-%m-%d")
                            số_ngày = (time.mktime(hôm_nay_datetime) - time.mktime(ngày_gd_datetime)) / (24 * 3600)
                            tiền_lãi = (số_tiền_gốc * (float(lãi_suất) / 100) * số_ngày) / 365
                        
                        # Tính phí phạt
                        tiền_phạt = 0
                        số_ngày_quá_hạn = 0
                        if ngày_đến_hạn:
                            ngày_đến_hạn_datetime = time.strptime(str(ngày_đến_hạn), "%Y-%m-%d")
                            if hôm_nay_datetime > ngày_đến_hạn_datetime:
                                số_ngày_quá_hạn = (time.mktime(hôm_nay_datetime) - time.mktime(ngày_đến_hạn_datetime)) / (24 * 3600)
                                tiền_phạt = số_tiền_gốc * (float(phí_phạt) / 100) * số_ngày_quá_hạn / 30
                        
                        # Tổng tiền
                        tổng_tiền = số_tiền_gốc + tiền_lãi + tiền_phạt
                        
                        # Thêm vào treeview
                        self.tree_tình_trạng.insert("", "end", values=(
                            người_nợ,
                            người_cho_vay,
                            f"{số_tiền_gốc:.2f}",  # Hiển thị số tiền gốc
                            ngày_gd,
                            ngày_đến_hạn or "Không có",
                            f"{lãi_suất}%",
                            f"{phí_phạt}%",
                            int(số_ngày_quá_hạn),
                            f"{tiền_phạt:.2f}",
                            f"{tổng_tiền:.2f}"  # Hiển thị tổng tiền bao gồm lãi và phạt
                        ))
                        
        except mysql.connector.Error as err:
            messagebox.showerror("Lỗi", f"Không thể cập nhật tình trạng nợ: {err}")

    def _thêm_khoản_nợ(self):
        người_nợ = self.combo_người_nợ.get()
        người_cho_vay = self.combo_người_cho_vay.get()
        try:
            số_tiền = float(self.entry_số_tiền.get())
            if số_tiền <= 0:
                raise ValueError("Số tiền phải lớn hơn 0")
                    
            # Parse new fields
            ngày_đến_hạn = self.date_due.get()
            lãi_suất = float(self.entry_lãi_suất.get() or 0.0)
            phí_phạt = float(self.entry_phí_phạt.get() or 0.0)
            
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
        self.tree_nợ.insert("", "end", values=(người_nợ, người_cho_vay, số_tiền, ngày_đến_hạn, f"{lãi_suất}%", f"{phí_phạt}%"))
            
        # Clear entry fields
        self.entry_số_tiền.delete(0, tk.END)
        self.date_due.delete(0, tk.END)
        self.entry_lãi_suất.delete(0, tk.END)
        self.entry_phí_phạt.delete(0, tk.END)
            
        # Set default values
        self.entry_lãi_suất.insert(0, "0.0")
        self.entry_phí_phạt.insert(0, "0.0")
            
        messagebox.showinfo("Thành công", f"Đã thêm khoản nợ: {người_nợ} nợ {người_cho_vay} {số_tiền}")

    def _cập_nhật_combobox(self):
        danh_sách = self.đồ_thị.danh_sách_đỉnh
        self.combo_người_nợ['values'] = danh_sách
        self.combo_người_cho_vay['values'] = danh_sách


    def _tối_ưu_hóa_dòng_tiền(self):
        if self.đồ_thị.số_đỉnh < 2:
            messagebox.showerror("Lỗi", "Cần ít nhất 2 người dùng để tối ưu hóa dòng tiền!")
            return

        # Lấy danh sách nợ từ CSDL với thông tin về lãi và phí phạt
        self.cursor.execute("""
            SELECT from_person, to_person, amount, transaction_date, due_date, 
                interest_rate, late_fee_rate 
            FROM debts
        """)
        danh_sách_nợ_gốc = self.cursor.fetchall()

        if not danh_sách_nợ_gốc:
            messagebox.showerror("Lỗi", "Không có khoản nợ nào để tối ưu hóa!")
            return

        # Tính toán tổng số tiền (gốc + lãi + phạt) cho mỗi khoản nợ
        danh_sách_nợ = []
        hôm_nay = time.strftime("%Y-%m-%d")
        hôm_nay_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
        
        for người_nợ, người_cho_vay, số_tiền_gốc, ngày_giao_dịch, ngày_đến_hạn, lãi_suất, phí_phạt in danh_sách_nợ_gốc:
            # Chuyển đổi các giá trị Decimal thành float
            số_tiền_gốc = float(số_tiền_gốc)
            lãi_suất = float(lãi_suất) if lãi_suất else 0.0
            phí_phạt = float(phí_phạt) if phí_phạt else 0.0
            
            tổng_tiền = số_tiền_gốc

            
            
            # Tính lãi (nếu có)
            if ngày_giao_dịch and lãi_suất:
                # Chuẩn hóa định dạng ngày tháng (loại bỏ phần thời gian)
                ngày_giao_dịch_str = str(ngày_giao_dịch).split()[0]
                ngày_giao_dịch_datetime = time.strptime(ngày_giao_dịch_str, "%Y-%m-%d")
                số_ngày = max(0, (time.mktime(hôm_nay_datetime) - time.mktime(ngày_giao_dịch_datetime)) / (24 * 3600))
                tiền_lãi = (số_tiền_gốc * (lãi_suất / 100) * số_ngày) / 365
                tổng_tiền += tiền_lãi
            
            # Tính phí phạt nếu quá hạn
            if ngày_đến_hạn and phí_phạt:
                # Chuẩn hóa định dạng ngày tháng (loại bỏ phần thời gian)
                ngày_đến_hạn_str = str(ngày_đến_hạn).split()[0]
                ngày_đến_hạn_datetime = time.strptime(ngày_đến_hạn_str, "%Y-%m-%d")
                chênh_lệch = (time.mktime(ngày_đến_hạn_datetime) - time.mktime(hôm_nay_datetime)) / (24 * 3600)
                
                if chênh_lệch < 0:  # Quá hạn
                    số_ngày_quá_hạn = abs(int(chênh_lệch))
                    tiền_phạt = (số_tiền_gốc * (phí_phạt / 100) * số_ngày_quá_hạn) / 30
                    tổng_tiền += tiền_phạt
            
            # Thêm khoản nợ với tổng số tiền đã tính vào danh sách
            danh_sách_nợ.append((người_nợ, người_cho_vay, tổng_tiền))
        
        # Phần còn lại của hàm giữ nguyên
        đồ_thị_tạm = Đồ_Thị(self.conn, self.cursor)
        for tên in self.đồ_thị.danh_sách_đỉnh:
            đồ_thị_tạm.thêm_đỉnh(tên)
        
        for nguồn, đích, giá_trị in danh_sách_nợ:
            đồ_thị_tạm.thêm_cạnh(nguồn, đích, giá_trị, lưu_vào_db=False)
        
        # Bắt đầu tối ưu hóa
        bắt_đầu = time.time()
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
            self.tree_giao_dịch.insert("", "end", values=(người_trả, người_nhận, f"{số_tiền:.2f}"))
        self.text_thống_kê.delete(1.0, tk.END)
        self.text_thống_kê.insert(tk.END, f"Thời gian thực thi: {thời_gian:.2f} ms\n\n")
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
        for widget in self.frame_đồ_thị_ban_đầu.winfo_children():
            widget.destroy()
        for widget in self.frame_đồ_thị_tối_ưu.winfo_children():
            widget.destroy()
        
        G_ban_đầu = nx.DiGraph()
        for tên in self.đồ_thị.danh_sách_đỉnh:
            G_ban_đầu.add_node(tên)
        for nguồn, đích, giá_trị in danh_sách_nợ_ban_đầu:
            G_ban_đầu.add_edge(nguồn, đích, weight=giá_trị)
        
        G_tối_ưu = nx.DiGraph()
        for tên in self.đồ_thị.danh_sách_đỉnh:
            G_tối_ưu.add_node(tên)
        for nguồn, đích, giá_trị in giao_dịch_tối_ưu:
            G_tối_ưu.add_edge(nguồn, đích, weight=giá_trị)
        
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        pos = nx.spring_layout(G_ban_đầu, seed=42)
        nx.draw_networkx_nodes(G_ban_đầu, pos, node_color='lightblue', node_size=500, ax=ax1)
        edge_labels = {(u, v): f"{d['weight']:.1f}" for u, v, d in G_ban_đầu.edges(data=True)}
        nx.draw_networkx_edges(G_ban_đầu, pos, width=1.5, alpha=0.7, edge_color='gray', ax=ax1)
        nx.draw_networkx_edge_labels(G_ban_đầu, pos, edge_labels=edge_labels, font_size=8, ax=ax1)
        nx.draw_networkx_labels(G_ban_đầu, pos, font_size=10, font_weight='bold', ax=ax1)
        ax1.set_title("Đồ thị dòng tiền ban đầu")
        ax1.axis('off')
        plt.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=self.frame_đồ_thị_ban_đầu)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        nx.draw_networkx_nodes(G_tối_ưu, pos, node_color='lightgreen', node_size=500, ax=ax2)
        edge_labels = {(u, v): f"{d['weight']:.1f}" for u, v, d in G_tối_ưu.edges(data=True)}
        nx.draw_networkx_edges(G_tối_ưu, pos, width=1.5, alpha=0.7, edge_color='red', ax=ax2)
        nx.draw_networkx_edge_labels(G_tối_ưu, pos, edge_labels=edge_labels, font_size=8, ax=ax2)
        nx.draw_networkx_labels(G_tối_ưu, pos, font_size=10, font_weight='bold', ax=ax2)
        ax2.set_title("Đồ thị dòng tiền tối ưu")
        ax2.axis('off')
        plt.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=self.frame_đồ_thị_tối_ưu)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.tab_control.select(2)

    def _xóa_dữ_liệu(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa tất cả dữ liệu trên giao diện?"):
            try:
                # Reset đồ thị (chỉ xóa dữ liệu local)
                self.đồ_thị.danh_sách_đỉnh = []
                self.đồ_thị.ma_trận_kề = []
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
                
                # Xóa thống kê
                self.text_thống_kê.delete(1.0, tk.END)
                
                # Reset combobox
                self._cập_nhật_combobox()
                
                # Thêm nút để tải lại dữ liệu từ SQL nếu cần
                if self.conn and self.cursor:  # Chỉ hiện thông báo nếu có kết nối SQL
                    if messagebox.askyesno("Tải lại dữ liệu", "Bạn có muốn tải lại dữ liệu từ MySQL không?"):
                        self._tải_dữ_liệu_từ_mysql()
                else:  # Nếu chưa có kết nối SQL
                    if messagebox.askyesno("Kết nối SQL", "Bạn có muốn kết nối với cơ sở dữ liệu MySQL không?"):
                        login = SQL_Login()
                        login.wait_window()
                        
                        if login.result:
                            self.conn, self.cursor = login.result
                            self._tải_dữ_liệu_từ_mysql()
                    else:
                        messagebox.showinfo("Thành công", "Đã xóa dữ liệu trên giao diện!")
                        
            except Exception as err:
                messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {err}")
    

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
                ("An", "Bình", 500.00, "2025-03-20", "2025-04-05", 5.0, 1.0),  # Đã quá hạn nếu hôm nay là 31/03/2025
                ("Bình", "Cường", 300.00, "2025-03-25", "2025-04-10", 4.5, 1.5),  # Sắp đến hạn
                ("Cường", "Dung", 400.00, "2025-03-28", "2025-04-15", 5.5, 1.0),
                ("Dung", "An", 200.00, "2025-03-29", "2025-04-20", 3.5, 0.5),
                ("An", "Hùng", 600.00, "2025-03-30", "2025-04-25", 6.0, 2.0),
                ("Hùng", "Bình", 100.00, "2025-03-27", "2025-04-07", 4.0, 1.0),  # Sắp đến hạn
                ("Cường", "An", 250.00, "2025-03-26", "2025-05-01", 5.0, 1.5),
            ]
            
            # Chèn dữ liệu vào MySQL và cập nhật giao diện
            for nguồn, đích, giá_trị, ngày_giao_dịch, hạn, lãi, phí in khoản_nợ_mẫu:
                self.cursor.execute(
                    """
                    INSERT INTO debts (from_person, to_person, amount, transaction_date, due_date, interest_rate, late_fee_rate)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (nguồn, đích, giá_trị, ngày_giao_dịch, hạn, lãi, phí)
                )
                self.conn.commit()
                self.đồ_thị.thêm_cạnh(nguồn, đích, giá_trị, lưu_vào_db=False)
                self.tree_nợ.insert("", "end", values=(nguồn, đích, f"{giá_trị:.2f}", hạn, f"{lãi}%", f"{phí}%"))
            
            # Cập nhật combobox và thông báo
            self._cập_nhật_combobox()
            messagebox.showinfo("Thành công", "Đã tạo dữ liệu mẫu đầy đủ!")
        
        except mysql.connector.Error as err:
            messagebox.showerror("Lỗi", f"Không thể tạo dữ liệu mẫu: {err}")

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
            self.đồ_thị.danh_sách_đỉnh = []
            self.đồ_thị.ma_trận_kề = []
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
                số_tiền_còn_lại = float(số_tiền) - float(đã_trả)
                if số_tiền_còn_lại > 0:
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
        selected_item = self.tree_tình_trạng.selection()
        if not selected_item:
            messagebox.showerror("Lỗi", "Vui lòng chọn một khoản nợ để thanh toán!")
            return

        values = self.tree_tình_trạng.item(selected_item, 'values')
        người_nợ = values[0]
        người_cho_vay = values[1]
        số_tiền_gốc = Decimal(values[2])  # Tổng số tiền gốc từ giao diện
        tổng_tiền = Decimal(values[9])    # Tổng tiền (gốc + lãi + phạt) từ giao diện

        số_tiền_thanh_toán = simpledialog.askfloat(
            "Thanh toán",
            f"Nhập số tiền thanh toán (tối đa {float(tổng_tiền):.2f}):",
            minvalue=0.01,
            maxvalue=float(tổng_tiền)
        )
        
        if số_tiền_thanh_toán is None:
            return

        try:
            # Đồng bộ dữ liệu trước khi truy vấn
            self.đồ_thị.đồng_bộ_dữ_liệu()

            # Truy vấn tất cả các khoản nợ chưa thanh toán hết
            self.cursor.execute("""
                SELECT d.id, d.amount, COALESCE(SUM(p.amount), 0) as paid,
                    d.transaction_date, d.due_date, d.interest_rate, d.late_fee_rate
                FROM debts d
                LEFT JOIN payments p ON d.id = p.debt_id
                WHERE d.from_person = %s 
                AND d.to_person = %s
                GROUP BY d.id, d.amount, d.transaction_date, d.due_date, d.interest_rate, d.late_fee_rate
                HAVING (d.amount - COALESCE(SUM(p.amount), 0)) > 0
                ORDER BY d.transaction_date ASC
            """, (người_nợ, người_cho_vay))
                    
            danh_sách_nợ = self.cursor.fetchall()
            if not danh_sách_nợ:
                messagebox.showerror("Lỗi", "Không tìm thấy khoản nợ hoặc đã được thanh toán hết!")
                return

            # Tính tổng số tiền thực tế từ tất cả các khoản nợ
            hôm_nay = time.strftime("%Y-%m-%d")
            hôm_nay_datetime = time.strptime(hôm_nay, "%Y-%m-%d")
            tổng_số_tiền_thực_tế = 0
            danh_sách_tiền_nợ = []

            for debt_id, amount, paid, ngày_giao_dịch, ngày_đến_hạn, lãi_suất, phí_phạt in danh_sách_nợ:
                số_tiền_gốc_còn_lại = float(amount) - float(paid or 0)

                # Tính lãi
                tiền_lãi = 0
                if ngày_giao_dịch:
                    ngày_gd_str = str(ngày_giao_dịch).split()[0]
                    ngày_gd_datetime = time.strptime(ngày_gd_str, "%Y-%m-%d")
                    số_ngày = max(0, (time.mktime(hôm_nay_datetime) - time.mktime(ngày_gd_datetime)) / (24 * 3600))
                    tiền_lãi = (số_tiền_gốc_còn_lại * (float(lãi_suất or 0) / 100) * số_ngày) / 365

                # Tính phí phạt
                tiền_phạt = 0
                if ngày_đến_hạn:
                    ngày_đến_hạn_datetime = time.strptime(str(ngày_đến_hạn), "%Y-%m-%d")
                    if hôm_nay_datetime > ngày_đến_hạn_datetime:
                        số_ngày_quá_hạn = (time.mktime(hôm_nay_datetime) - time.mktime(ngày_đến_hạn_datetime)) / (24 * 3600)
                        tiền_phạt = (số_tiền_gốc_còn_lại * (float(phí_phạt or 0) / 100) * số_ngày_quá_hạn) / 30

                tổng_tiền_nợ = số_tiền_gốc_còn_lại + tiền_lãi + tiền_phạt
                tổng_số_tiền_thực_tế += tổng_tiền_nợ
                danh_sách_tiền_nợ.append((debt_id, số_tiền_gốc_còn_lại, tổng_tiền_nợ))

            # Kiểm tra số tiền thanh toán
            if float(số_tiền_thanh_toán) > tổng_số_tiền_thực_tế:
                messagebox.showerror("Lỗi", f"Số tiền thanh toán không được vượt quá tổng số tiền thực tế ({tổng_số_tiền_thực_tế:.2f})")
                return

            # Phân bổ số tiền thanh toán cho từng khoản nợ
            số_tiền_còn_lại = float(số_tiền_thanh_toán)
            for debt_id, số_tiền_gốc_còn_lại, tổng_tiền_nợ in danh_sách_tiền_nợ:
                if số_tiền_còn_lại <= 0:
                    break

                # Số tiền thanh toán cho khoản nợ này
                số_tiền_cho_khoản_nợ = min(số_tiền_còn_lại, tổng_tiền_nợ)
                số_tiền_còn_lại -= số_tiền_cho_khoản_nợ

                # Ghi nhận thanh toán
                self.cursor.execute("""
                    INSERT INTO payments (debt_id, amount, payment_date) 
                    VALUES (%s, %s, NOW())
                """, (debt_id, số_tiền_cho_khoản_nợ))

            # Cập nhật ma trận kề
            i = self.đồ_thị.danh_sách_đỉnh.index(người_nợ)
            j = self.đồ_thị.danh_sách_đỉnh.index(người_cho_vay)
            self.đồ_thị.ma_trận_kề[i][j] = max(0, tổng_số_tiền_thực_tế - float(số_tiền_thanh_toán))

            self.conn.commit()

            # Cập nhật giao diện
            self._cập_nhật_tình_trạng_nợ()
            messagebox.showinfo("Thành công", f"Đã ghi nhận thanh toán {float(số_tiền_thanh_toán):.2f}!")

        except mysql.connector.Error as err:
            self.conn.rollback()
            messagebox.showerror("Lỗi", f"Không thể ghi nhận thanh toán: {err}")

class SQL_Login(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Kết nối MySQL Server")
        self.geometry("400x300")
        
        # Cấu hình mặc định
        self.config = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': ''
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
                amount DECIMAL(10, 2),
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
                amount DECIMAL(10, 2),
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
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