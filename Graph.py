from DynamicArray import DynamicArray
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import math
class Graph:
    def __init__(self):
        self.nodes = DynamicArray()  # Danh sách các đỉnh
        self.edges = DynamicArray()  # Danh sách các cạnh
    
    def add_node(self, node):
        """Thêm một đỉnh vào đồ thị"""
        if node not in self.nodes:
            # Nếu chưa tồn tại, thêm đỉnh vào cuối danh sách nodes
            self.nodes.append(node)
    
    def add_edge(self, source, target, weight):
        """Thêm một cạnh có trọng số vào đồ thị"""
        self.edges.append((source, target, weight))

    def _rescale_layout_custom(self, pos_dict, scale=Decimal('1.0'), center=None): # GIỮ NGUYÊN TÊN THAM SỐ
        """
        Rescale và đặt lại vị trí các nút.
        1. Dịch chuyển tâm của layout hiện tại về gốc (0,0).
        2. Scale layout sao cho giá trị tọa độ tuyệt đối lớn nhất bằng `scale`.
        3. Dịch chuyển layout đã scale đến `center`.

        pos_dict: Dictionary {node: [Decimal(x), Decimal(y)]}
        scale: Decimal, giá trị tuyệt đối lớn nhất của tọa độ sau khi scale (bán kính layout quanh tâm).
        center: List/Tuple [Decimal(cx), Decimal(cy)], tâm cuối cùng của layout.
        """
        if not pos_dict: 
            return {}

        # Xử lý tham số center
        if center is None:
            # Mặc định tâm là (0.5, 0.5) nếu người dùng không cung cấp
            # Điều này ngầm định layout cuối cùng sẽ nằm trong khung [0,1]x[0,1] nếu scale là 0.5
            processed_center = [Decimal('0.5'), Decimal('0.5')] 
        else:
            try:
                processed_center = [Decimal(str(c_val)) for c_val in center]
                if len(processed_center) != 2: # Giả sử làm việc trong không gian 2D
                    # print("Cảnh báo: Tham số 'center' không hợp lệ, sử dụng giá trị mặc định.")
                    processed_center = [Decimal('0.5'), Decimal('0.5')]
            except (TypeError, InvalidOperation):
                # print("Cảnh báo: Lỗi chuyển đổi 'center', sử dụng giá trị mặc định.")
                processed_center = [Decimal('0.5'), Decimal('0.5')]
        
        # Xử lý tham số scale
        try:
            processed_scale = Decimal(str(scale))
            if processed_scale <= Decimal('0'):
                # print("Cảnh báo: Tham số 'scale' phải dương, sử dụng giá trị mặc định 1.0.")
                processed_scale = Decimal('1.0')
        except (TypeError, InvalidOperation):
            # print("Cảnh báo: Lỗi chuyển đổi 'scale', sử dụng giá trị mặc định 1.0.")
            processed_scale = Decimal('1.0')


        node_keys = DynamicArray() 
        pos_values_da = DynamicArray()
        
        valid_coord_count = 0
        for node, coords_original in pos_dict.items():
            node_keys.append(node)
            temp_coord_da = DynamicArray(initial_capacity=2)
            try:
                if isinstance(coords_original, (list, tuple)) and len(coords_original) == 2:
                    temp_coord_da.append(Decimal(str(coords_original[0])))
                    temp_coord_da.append(Decimal(str(coords_original[1])))
                    valid_coord_count +=1
                else:
                    # print(f"Cảnh báo: Tọa độ không hợp lệ cho nút {node} trong rescale: {coords_original}. Dùng (0,0).")
                    temp_coord_da.append(Decimal('0.0'))
                    temp_coord_da.append(Decimal('0.0'))
            except (TypeError, InvalidOperation, IndexError) as e:
                 # print(f"Cảnh báo: Lỗi chuyển đổi tọa độ cho nút {node}: {coords_original}. Lỗi: {e}. Dùng (0,0).")
                 temp_coord_da.clear() 
                 temp_coord_da.append(Decimal('0.0'))
                 temp_coord_da.append(Decimal('0.0'))
            pos_values_da.append(temp_coord_da)

        if valid_coord_count == 0 and pos_values_da.size > 0 :
             rescaled_pos_dict_error = {}
             for i in range(node_keys.size):
                 node = node_keys[i]
                 rescaled_pos_dict_error[node] = [processed_center[0], processed_center[1]] # Sử dụng processed_center
             return rescaled_pos_dict_error
        elif pos_values_da.size == 0:
            return {}

        # 1. Tính tâm hiện tại (mean) của các điểm
        mean_x = Decimal('0.0')
        mean_y = Decimal('0.0')
        for i in range(pos_values_da.size): # Chỉ lặp trên các tọa độ đã được xác thực là có 2 phần tử
            mean_x += pos_values_da[i][0]
            mean_y += pos_values_da[i][1]
        
        if valid_coord_count > 0: # Đảm bảo không chia cho 0
            mean_x /= Decimal(str(valid_coord_count))
            mean_y /= Decimal(str(valid_coord_count))
        # Nếu valid_coord_count là 0 (không có điểm hợp lệ), mean_x, mean_y vẫn là 0.

        # 2. Dịch chuyển tất cả các điểm sao cho tâm mới là (0,0)
        # Cập nhật trực tiếp trên pos_values_da
        for i in range(pos_values_da.size):
            pos_values_da[i][0] -= mean_x
            pos_values_da[i][1] -= mean_y

        # 3. Tìm giá trị tọa độ tuyệt đối lớn nhất (lim) sau khi đã dịch về tâm
        lim = Decimal('0.0')
        if pos_values_da.size > 0:
            for i in range(pos_values_da.size):
                lim = max(lim, abs(pos_values_da[i][0]), abs(pos_values_da[i][1]))
        
        if lim < Decimal('1e-9'): 
            lim = Decimal('1.0') # Nếu tất cả các điểm ở gốc, không scale (hoặc scale bằng 1)

        # 4. Scale tất cả các điểm sao cho giá trị tuyệt đối lớn nhất bằng processed_scale
        # và 5. Dịch chuyển đến processed_center
        rescaled_pos_dict = {}
        for i in range(node_keys.size): 
            node = node_keys[i]
            
            # Scale
            scaled_x = pos_values_da[i][0] * processed_scale / lim
            scaled_y = pos_values_da[i][1] * processed_scale / lim
            
            # Dịch chuyển đến tâm cuối cùng
            final_x = scaled_x + processed_center[0]
            final_y = scaled_y + processed_center[1]
            
            rescaled_pos_dict[node] = [final_x, final_y] 
            
        return rescaled_pos_dict

    def _resolve_overlaps(self, pos, node_size=0.1):
        """Giải quyết chồng chéo giữa các nút. `pos` là dict các tọa độ Decimal."""
        movement = True
        node_size = Decimal(str(node_size))
        
        while movement:
            movement = False
            for i in range(self.nodes.size):
                for j in range(i + 1, self.nodes.size):
                    node1, node2 = self.nodes[i], self.nodes[j]
                    delta_x = pos[node2][0] - pos[node1][0]
                    delta_y = pos[node2][1] - pos[node1][1]
                    
                    dist_sq = delta_x * delta_x + delta_y * delta_y
                    if dist_sq > Decimal('0'):
                        dist = dist_sq.sqrt()
                        if dist < node_size:
                            movement = True
                            factor = (node_size - dist) / (Decimal('2.0') * dist)
                            dx = delta_x * factor
                            dy = delta_y * factor
                            pos[node1][0] -= dx
                            pos[node1][1] -= dy
                            pos[node2][0] += dx
                            pos[node2][1] += dy
    
    # Cập nhật phương thức spring_layout trong class Graph
    def spring_layout(self, k=None, iterations=100, seed=None, min_dist=0.01, 
                 border_margin=0.1, scale=0.5, center=None, dim=2, repulsion_strength=Decimal('0.5')):
        """Thuật toán Fruchterman-Reingold cho layout đồ thị
        
        Parameters:
        -----------
        dim : int
            Số chiều của layout (2 hoặc 3)
        k : float or None
            Khoảng cách lý tưởng giữa các nút
        iterations : int
            Số lần lặp tối đa
        scale : float
            Tỷ lệ của layout cuối cùng
        center : list, optional (default=[0.5, 0.5])
            Tâm của layout
        """
        min_dist = Decimal(str(min_dist))
        border_margin = Decimal(str(border_margin))
        scale = Decimal(str(scale))
        repulsion_strength = Decimal(str(repulsion_strength))

        if center is None:
            center = [0.5, 0.5]
        if k is None:
            # Cải thiện công thức tính k
            k = Decimal('0.8') * (Decimal('1.0') / Decimal(str(self.nodes.size ** 0.5)))

        # Khởi tạo vị trí ban đầu theo hình tròn
        pos = {}
        for i, node in enumerate(self.nodes):
            if dim == 2:
                theta = Decimal(str(2 * math.pi * i / self.nodes.size))
                r = Decimal('0.5') * Decimal(str(scale))
                pos[node] = [
                    Decimal(str(center[0])) + r * Decimal(str(math.cos(float(theta)))),
                    Decimal(str(center[1])) + r * Decimal(str(math.sin(float(theta))))
                ]

        # Tính nhiệt độ ban đầu dựa trên kích thước layout
        if self.nodes.size > 0:
            min_x = min(p[0] for p in pos.values())
            max_x = max(p[0] for p in pos.values())
            min_y = min(p[1] for p in pos.values())
            max_y = max(p[1] for p in pos.values())
            t = max(max_x - min_x, max_y - min_y) * Decimal('0.1')
            if t == Decimal('0'):
                t = Decimal('0.1')
        else:
            t = Decimal('0.1')

        # Tính dt cho làm mát tuyến tính
        #dt = t / Decimal(str(iterations + 1))

        # Vòng lặp chính
        for iter_num in range(iterations):
            # Khởi tạo vector dịch chuyển cho mỗi nút
            disp = {node: [Decimal('0'), Decimal('0')] for node in self.nodes}
            
            # Tính lực đẩy giữa tất cả các cặp nút
            for i in range(self.nodes.size):
                for j in range(i + 1, self.nodes.size):
                    delta_x = pos[self.nodes[j]][0] - pos[self.nodes[i]][0]
                    delta_y = pos[self.nodes[j]][1] - pos[self.nodes[i]][1]
                    dist_sq = delta_x * delta_x + delta_y * delta_y
                    
                    if dist_sq > Decimal('0'):
                        dist = dist_sq.sqrt()
                        # Công thức lực đẩy chuẩn: k^2/d^2
                        force = (k * k / (dist * dist)) * repulsion_strength
                        
                        dx = delta_x * force / dist
                        dy = delta_y * force / dist
                        
                        disp[self.nodes[i]][0] -= dx
                        disp[self.nodes[i]][1] -= dy
                        disp[self.nodes[j]][0] += dx
                        disp[self.nodes[j]][1] += dy

            # Tính lực kéo cho các cạnh
            for source, target, weight in self.edges:
                delta_x = pos[target][0] - pos[source][0]
                delta_y = pos[target][1] - pos[source][1]
                dist_sq = delta_x * delta_x + delta_y * delta_y
                
                if dist_sq > Decimal('0'):
                    dist = dist_sq.sqrt()
                    # Công thức lực kéo chuẩn: d^2/k
                    force = dist / k
                    
                    # Điều chỉnh lực kéo theo trọng số cạnh
                    weight_decimal = Decimal(str(abs(weight)))
                    force *= weight_decimal / self.max_weight if hasattr(self, 'max_weight') else Decimal('1.0')
                    
                    dx = delta_x * force / dist
                    dy = delta_y * force / dist
                    
                    disp[source][0] += dx
                    disp[source][1] += dy
                    disp[target][0] -= dx
                    disp[target][1] -= dy

            # Cập nhật vị trí
            for node in self.nodes:
                dx, dy = disp[node]
                dist_sq = dx * dx + dy * dy
                if dist_sq > Decimal('0'):
                    dist = dist_sq.sqrt()
                    dx = dx * min(dist, t) / dist
                    dy = dy * min(dist, t) / dist
                    pos[node][0] += dx
                    pos[node][1] += dy

            # Làm mát tuyến tính
            t = self._adaptive_cooling(t, iter_num, iterations)
            if t == Decimal('0'):
                break

        # Sau khi hoàn thành vòng lặp, rescale layout về khoảng [0,1]
        pos = self._rescale_layout_custom(pos, scale=scale, center=center)
        
        # Giải quyết chồng chéo nút (optional)
        self._resolve_overlaps(pos, node_size=0.1)
        
        return pos
    
    def _adaptive_cooling(self, t, iteration, total_iterations):
        """Cooling schedule thích ứng"""
        # Chuyển các hằng số float sang Decimal
        factor_early = Decimal('0.98')
        factor_mid = Decimal('0.95')
        factor_late = Decimal('0.85')

        if iteration < total_iterations * 0.25: # total_iterations * 0.25 có thể là float
                                                # nên phép so sánh này vẫn ổn
            return t * factor_early  # Làm mát chậm ở giai đoạn đầu (Decimal * Decimal)
        elif iteration < total_iterations * 0.75:
            return t * factor_mid  # Làm mát bình thường ở giai đoạn giữa (Decimal * Decimal)
        else:
            return t * factor_late  # Làm mát nhanh ở giai đoạn cuối (Decimal * Decimal)