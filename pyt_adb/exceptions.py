"""
Các lớp ngoại lệ cho thư viện PyADB
"""

class ADBError(Exception):
    """Lớp lỗi cơ bản cho các lỗi ADB"""
    pass


class ADBTimeoutError(ADBError):
    """Lỗi khi thao tác ADB bị timeout"""
    pass


class DeviceNotFoundError(ADBError):
    """Lỗi khi không tìm thấy thiết bị"""
    pass


class CommandFailedError(ADBError):
    """Lỗi khi lệnh ADB thất bại"""
    
    def __init__(self, cmd, returncode, stdout, stderr):
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        message = f"Command '{cmd}' failed with return code {returncode}\nStderr: {stderr}"
        super().__init__(message)