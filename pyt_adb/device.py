"""
Module quản lý thiết bị Android khi kết nối qua ADB
"""

import os
import re
import time
from typing import Dict, List, Optional, Union, Tuple

from .adb import ADB
from .exceptions import DeviceNotFoundError, ADBError


class Device:
    """
    Lớp quản lý thiết bị Android
    """
    
    def __init__(self, serial: str = None, adb_path: str = None):
        """
        Khởi tạo đối tượng thiết bị
        
        Args:
            serial: Số serial của thiết bị để kết nối. Nếu None, sử dụng thiết bị mặc định
            adb_path: Đường dẫn đến thực thi ADB. Nếu None, sử dụng biến môi trường PATH
        """
        self.serial = serial
        self.adb = ADB(adb_path=adb_path, serial=serial)
        self._verify_device()
        
    def _verify_device(self):
        """Kiểm tra xem thiết bị có tồn tại và kết nối không"""
        devices = self.adb.devices()
        
        if not devices:
            raise DeviceNotFoundError("Không tìm thấy thiết bị nào được kết nối")
        
        # Nếu không chỉ định serial, sử dụng thiết bị đầu tiên
        if not self.serial:
            self.serial = devices[0]['serial']
            self.adb.serial = self.serial
            return
        
        # Kiểm tra thiết bị với serial đã chỉ định có tồn tại không
        serials = [device['serial'] for device in devices]
        if self.serial not in serials:
            raise DeviceNotFoundError(f"Không tìm thấy thiết bị với serial '{self.serial}'")
    
    def get_model(self) -> str:
        """
        Lấy tên model của thiết bị
        
        Returns:
            Tên model của thiết bị
        """
        return self.adb.shell("getprop", "ro.product.model")
    
    def get_android_version(self) -> str:
        """
        Lấy phiên bản Android của thiết bị
        
        Returns:
            Phiên bản Android
        """
        return self.adb.shell("getprop", "ro.build.version.release")
    
    def get_api_level(self) -> str:
        """
        Lấy mức API của thiết bị
        
        Returns:
            Mức API
        """
        return self.adb.shell("getprop", "ro.build.version.sdk")
    
    def get_battery_info(self) -> Dict[str, str]:
        """
        Lấy thông tin pin của thiết bị
        
        Returns:
            Dict chứa thông tin pin
        """
        battery_info = {}
        output = self.adb.shell("dumpsys", "battery")
        
        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                battery_info[key.strip()] = value.strip()
                
        return battery_info
    
    def get_screen_resolution(self) -> Tuple[int, int]:
        """
        Lấy độ phân giải màn hình
        
        Returns:
            Tuple (width, height) chứa chiều rộng và chiều cao màn hình
        """
        output = self.adb.shell("wm", "size")
        match = re.search(r"Physical size: (\d+)x(\d+)", output)
        
        if match:
            width, height = match.groups()
            return int(width), int(height)
        else:
            raise ADBError("Không thể lấy thông tin độ phân giải màn hình")
    
    def get_installed_packages(self) -> List[str]:
        """
        Lấy danh sách các package đã cài đặt
        
        Returns:
            Danh sách tên các package
        """
        output = self.adb.shell("pm", "list", "packages")
        packages = []
        
        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("package:"):
                packages.append(line[8:])  # Bỏ "package:" ở đầu
                
        return packages
    
    def is_package_installed(self, package_name: str) -> bool:
        """
        Kiểm tra xem một package có được cài đặt không
        
        Args:
            package_name: Tên package cần kiểm tra
            
        Returns:
            True nếu package đã được cài đặt, False nếu không
        """
        packages = self.get_installed_packages()
        return package_name in packages
    
    def take_screenshot(self, local_path: str) -> str:
        """
        Chụp ảnh màn hình và lưu về máy tính
        
        Args:
            local_path: Đường dẫn cục bộ để lưu ảnh chụp màn hình
            
        Returns:
            Đường dẫn đến file ảnh chụp màn hình
        """
        remote_path = "/sdcard/screenshot.png"
        self.adb.shell("screencap", "-p", remote_path)
        self.adb.pull(remote_path, local_path)
        self.adb.shell("rm", remote_path)
        return local_path
    
    def record_screen(self, local_path: str, time_limit: int = 30, bit_rate: int = 4000000) -> str:
        """
        Quay video màn hình và lưu về máy tính
        
        Args:
            local_path: Đường dẫn cục bộ để lưu video
            time_limit: Thời gian quay tối đa (giây)
            bit_rate: Bit rate cho video (bit/giây)
            
        Returns:
            Đường dẫn đến file video
        """
        remote_path = "/sdcard/screenrecord.mp4"
        
        # Bắt đầu quay video
        cmd = [
            "screenrecord", 
            "--time-limit", str(time_limit),
            "--bit-rate", str(bit_rate),
            remote_path
        ]
        
        # Quay video với thời gian giới hạn
        self.adb.shell(*cmd)
        
        # Kéo về máy tính
        self.adb.pull(remote_path, local_path)
        self.adb.shell("rm", remote_path)
        return local_path
    
    def input_text(self, text: str) -> str:
        """
        Nhập văn bản vào thiết bị
        
        Args:
            text: Văn bản cần nhập
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.adb.shell("input", "text", text)
    
    def tap(self, x: int, y: int) -> str:
        """
        Nhấn vào tọa độ trên màn hình
        
        Args:
            x: Tọa độ X
            y: Tọa độ Y
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.adb.shell("input", "tap", str(x), str(y))
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> str:
        """
        Vuốt từ tọa độ (x1, y1) đến (x2, y2)
        
        Args:
            x1: Tọa độ X bắt đầu
            y1: Tọa độ Y bắt đầu
            x2: Tọa độ X kết thúc
            y2: Tọa độ Y kết thúc
            duration: Thời gian vuốt (mili giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.adb.shell("input", "swipe", 
                              str(x1), str(y1), str(x2), str(y2), str(duration))
    
    def press_key(self, keycode: int) -> str:
        """
        Nhấn phím với mã phím Android
        
        Args:
            keycode: Mã phím Android (xem KeyEvent class Android)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.adb.shell("input", "keyevent", str(keycode))
    
    def press_back(self) -> str:
        """Nhấn nút Back"""
        return self.press_key(4)
    
    def press_home(self) -> str:
        """Nhấn nút Home"""
        return self.press_key(3)
    
    def press_menu(self) -> str:
        """Nhấn nút Menu"""
        return self.press_key(82)
    
    def press_power(self) -> str:
        """Nhấn nút nguồn"""
        return self.press_key(26)
    
    def clear_app_data(self, package_name: str) -> str:
        """
        Xóa dữ liệu ứng dụng
        
        Args:
            package_name: Tên package của ứng dụng
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.adb.shell("pm", "clear", package_name)
    
    def get_logcat(self, filters: str = None, time_limit: int = 10) -> str:
        """
        Lấy log từ thiết bị
        
        Args:
            filters: Bộ lọc logcat (ví dụ: 'ActivityManager:I *:S')
            time_limit: Thời gian tối đa để lấy log (giây)
            
        Returns:
            Nội dung log
        """
        cmd = ["logcat"]
        if filters:
            cmd.extend(filters.split())
            
        # Đặt timeout cho lệnh logcat
        return self.adb.shell(*cmd, timeout=time_limit)
    
    def reboot(self, mode: str = None) -> str:
        """
        Khởi động lại thiết bị
        
        Args:
            mode: Chế độ khởi động lại ('bootloader', 'recovery', hoặc None cho khởi động bình thường)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        cmd = ["reboot"]
        if mode:
            cmd.append(mode)
            
        return self.adb.run_command(*cmd)
    
    def get_ip_address(self) -> str:
        """
        Lấy địa chỉ IP của thiết bị
        
        Returns:
            Địa chỉ IP
        """
        output = self.adb.shell("ip", "addr", "show", "wlan0")
        match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", output)
        
        if match:
            return match.group(1)
        else:
            raise ADBError("Không thể lấy địa chỉ IP của thiết bị")
    
    def connect_wifi(self, ip_address: str, port: int = 5555) -> str:
        """
        Kết nối đến thiết bị qua wifi
        
        Args:
            ip_address: Địa chỉ IP của thiết bị
            port: Cổng để kết nối (mặc định 5555)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        # Đảm bảo cổng TCP/IP được mở trên thiết bị
        self.adb.run_command("tcpip", str(port))
        time.sleep(1)  # Chờ thiết bị chuyển sang chế độ tcpip
        
        # Kết nối đến thiết bị qua wifi
        return self.adb.run_command("connect", f"{ip_address}:{port}")