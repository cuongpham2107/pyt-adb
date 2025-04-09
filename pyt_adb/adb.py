"""
Module chính cho ADB - Android Debug Bridge
"""

import os
import re
import subprocess
import time
from typing import List, Optional, Dict, Union, Tuple

from .exceptions import ADBError, ADBTimeoutError, DeviceNotFoundError, CommandFailedError


class ADB:
    """
    Lớp chính để giao tiếp với Android Debug Bridge (ADB)
    """
    
    def __init__(self, adb_path: str = None, serial: str = None):
        """
        Khởi tạo đối tượng ADB
        
        Args:
            adb_path: Đường dẫn đến thực thi ADB. Nếu None, sử dụng biến môi trường PATH
            serial: Số serial của thiết bị để kết nối. Nếu None, sử dụng thiết bị mặc định
        """
        self.adb_path = adb_path or "adb"
        self.serial = serial
        self._check_adb()
    
    def _check_adb(self):
        """Kiểm tra ADB có thể thực thi được hay không"""
        try:
            self.run_command("version")
        except Exception as e:
            raise ADBError(f"Không thể thực thi ADB. Hãy chắc chắn ADB đã được cài đặt và trong PATH: {e}")
    
    def run_command(self, *args: str, timeout: int = 30) -> str:
        """
        Chạy lệnh ADB và trả về kết quả
        
        Args:
            args: Các đối số cho lệnh ADB
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
            
        Raises:
            ADBTimeoutError: Nếu lệnh bị timeout
            CommandFailedError: Nếu lệnh trả về lỗi
        """
        cmd = [self.adb_path]
        
        # Thêm số serial thiết bị nếu có
        if self.serial:
            cmd.extend(["-s", self.serial])
        
        # Thêm các đối số lệnh
        cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                raise CommandFailedError(
                    cmd=" ".join(cmd),
                    returncode=result.returncode,
                    stdout=result.stdout,
                    stderr=result.stderr
                )
            
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise ADBTimeoutError(f"Lệnh ADB bị timeout sau {timeout} giây: {' '.join(cmd)}")
    
    def devices(self) -> List[Dict[str, str]]:
        """
        Lấy danh sách các thiết bị đã kết nối
        
        Returns:
            Danh sách các thiết bị, mỗi thiết bị là một dict với các key 'serial' và 'status'
        """
        result = self.run_command("devices")
        devices_list = []
        
        lines = result.strip().split('\n')[1:]  # Bỏ qua dòng tiêu đề
        for line in lines:
            if not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) >= 2:
                devices_list.append({
                    'serial': parts[0].strip(),
                    'status': parts[1].strip()
                })
        
        return devices_list
    
    def shell(self, *args: str, timeout: int = 30) -> str:
        """
        Chạy lệnh ADB shell
        
        Args:
            args: Các đối số cho lệnh shell
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.run_command("shell", *args, timeout=timeout)
    
    def push(self, local: str, remote: str, timeout: int = 60) -> str:
        """
        Đẩy file từ máy tính lên thiết bị
        
        Args:
            local: Đường dẫn file cục bộ
            remote: Đường dẫn đích trên thiết bị
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.run_command("push", local, remote, timeout=timeout)
    
    def pull(self, remote: str, local: str, timeout: int = 60) -> str:
        """
        Kéo file từ thiết bị về máy tính
        
        Args:
            remote: Đường dẫn file trên thiết bị
            local: Đường dẫn đích cục bộ
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.run_command("pull", remote, local, timeout=timeout)
    
    def install(self, apk_path: str, reinstall: bool = False, timeout: int = 180) -> str:
        """
        Cài đặt ứng dụng APK lên thiết bị
        
        Args:
            apk_path: Đường dẫn đến file APK
            reinstall: Cài đặt lại nếu ứng dụng đã tồn tại
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        args = ["install"]
        if reinstall:
            args.append("-r")
        args.append(apk_path)
        return self.run_command(*args, timeout=timeout)
    
    def uninstall(self, package_name: str, keep_data: bool = False, timeout: int = 30) -> str:
        """
        Gỡ cài đặt ứng dụng khỏi thiết bị
        
        Args:
            package_name: Tên package của ứng dụng
            keep_data: Giữ lại dữ liệu và bộ nhớ cache
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        args = ["uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package_name)
        return self.run_command(*args, timeout=timeout)
    
    def start_app(self, package_name: str, activity_name: str = None, timeout: int = 30) -> str:
        """
        Khởi động ứng dụng trên thiết bị
        
        Args:
            package_name: Tên package của ứng dụng
            activity_name: Tên activity để khởi động (nếu không cung cấp sẽ dùng activity mặc định)
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        if activity_name:
            component = f"{package_name}/{activity_name}"
        else:
            component = package_name
            
        return self.shell("am", "start", "-n", component, timeout=timeout)
    
    def stop_app(self, package_name: str, timeout: int = 30) -> str:
        """
        Dừng ứng dụng trên thiết bị
        
        Args:
            package_name: Tên package của ứng dụng
            timeout: Thời gian timeout cho lệnh (giây)
            
        Returns:
            Kết quả stdout từ lệnh
        """
        return self.shell("am", "force-stop", package_name, timeout=timeout)
    
    def get_device_info(self) -> Dict[str, str]:
        """
        Lấy thông tin về thiết bị
        
        Returns:
            Dict chứa thông tin thiết bị
        """
        info = {}
        
        # Lấy thông tin thiết bị
        prop_lines = self.shell("getprop").split("\n")
        for line in prop_lines:
            match = re.match(r'\[([^]]+)\]:\s*\[([^]]*)\]', line)
            if match:
                key, value = match.groups()
                info[key] = value
        
        # Lấy thông tin bộ nhớ
        mem_info = self.shell("cat", "/proc/meminfo")
        for line in mem_info.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                info[f"mem.{key.strip()}"] = value.strip()
        
        return info