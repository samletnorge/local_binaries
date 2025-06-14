import os
import platform
import subprocess
class AndroidBinaries:
    """
    A class to manage paths to Android-related binaries like ADB and Scrcpy.
    This class automatically detects the operating system and sets the paths accordingly.
    It supports Linux, Windows, and macOS (Darwin).
    
    Attributes:
        device_id (str): The ID of the connected Android device. auto-detect if not provided.
        os_type (str): The type of operating system ('linux', 'windows', 'darwin'). auto-detect defaults to the 
    
    output:
        adb (str): Path to the ADB binary.
        scrcpy (str): Path to the Scrcpy binary.
        device_id (str): The ID of the connected Android device, if provided or auto-detected.
        
    Methods:
        __init__(device_id: str = None, os_type: str = None): Initializes the class and sets paths based on OS.
        device_id: Returns the device ID of the connected Android device.
        
    Raises:
        ValueError: If an unsupported OS type is provided.
        TypeError: If the device_id is not a string.
        TypeError: If the os_type is not a string.
    
    Usage:
    >>> adb_binaries = AndroidBinaries(device_id="1234567890abcdef", os_type="linux")
    >>> print(adb_binaries.adb)  # Outputs the path to the ADB binary
    >>> print(adb_binaries.scrcpy)  # Outputs the path to the Scrcpy binary
    >>> print(adb_binaries.device_id)  # Outputs the device ID
    >>> adb_binaries = AndroidBinaries()  # Automatically detects OS and sets paths
        >>> print(adb_binaries.adb)  # Outputs the path to the ADB binary based on detected OS
        >>> print(adb_binaries.scrcpy)  # Outputs the path to the Scrcpy binary based on detected OS
        >>> print(adb_binaries.device_id)  # Outputs the device ID
    """
    def __init__(self, device_id: str = None, os_type: str = None, visual: bool = True):
        self.device_id = device_id
        self.os_type = os_type
        self.arch = platform.machine()
        
        # Auto-detect OS if not specified but allow manual override
        if self.os_type is not None:
            if not isinstance(self.os_type, str):
                raise TypeError("os_type must be a string")
        else:
            self.os_type = platform.system().lower()
            print(f"Auto-detected OS type: {self.os_type}")

        if self.os_type == "windows":
            self.adb = os.path.join(os.path.dirname(__file__), "windows", "platform-tools", "adb.exe")
            self.scrcpy = os.path.join(os.path.dirname(__file__), "windows", f"scrcpy-windows-{self.arch}-v3.2", "scrcpy.exe")
        elif self.os_type == "darwin":
            self.adb = os.path.join(os.path.dirname(__file__), "darwin", "platform-tools", "adb")
            self.scrcpy = os.path.join(os.path.dirname(__file__), "darwin", "scrcpy-darwin-v3.2", "scrcpy")
        elif self.os_type == "linux":
            self.adb = os.path.join(os.path.dirname(__file__), "linux", "platform-tools", "adb")
            self.scrcpy = os.path.join(os.path.dirname(__file__), "linux", f"scrcpy-linux-{self.arch}-v3.2", "scrcpy")
        else:
            raise ValueError(f"Unsupported OS type: {self.os_type}")
        
        # Auto-detect device ID with ADB if not provided
        if device_id is None:
            try:
                result = subprocess.run([self.adb, "devices"], capture_output=True, text=True)
                devices = result.stdout.splitlines()
                
                if len(devices) > 1:
                    self.device_id = devices[1].split()[0]  # Get the first device ID
                    print(f"Detected device: {self.device_id}")
                    try: 
                        if visual:
                            # TODO: make this more general. ghostty is specific for me
                            subprocess.run(["pkill", "ghostty"], shell=False)
                            
                            subprocess.run(self.open_window("scrcpy",command=self.scrcpy), shell=True, check=True)  # starting 
                            print('running, starting....live replay')
                            
                            # android_strean_path = os.path.join(os.path.dirname(__file__), "writers", "android.py")
                            # android_strean_command = f"python3 {android_strean_path}"
                            # subprocess.run(self.open_window("android - live replay",command=android_strean_command), shell=True, check=True)  # starting scrcpy: if device connected
                    except Exception as e:
                        raise ValueError(f'did not open scrcpy because: {e}')
                else:
                    raise ValueError("No devices found. Please connect an Android device.")
            except Exception as e:
                self.device_id = None
                print(f"Error detecting device ID: {e}")
        else:
            if not isinstance(device_id, str):
                raise TypeError("device_id must be a string")
            self.device_id = device_id
            
    def open_window(self, window_name, command):
        """
        Opens a new terminal window with the specified command.
        Args:
            window_name (str): The title of the new terminal window.
            command (str): The command to execute in the new terminal window.
        Returns:
            str: The command to open a new terminal window with the specified command.
        """
        if self.os_type == "windows":
            return f"start cmd /k title {window_name} && {command}"
        elif self.os_type == "darwin":
            return f"""osascript -e 'tell application "Terminal" to do script "{command}"'"""
        elif self.os_type == "linux": # TODO: make this work specifically for me who has ghosttty
            return f"""ghostty --title={window_name} -e 'sh -c "{command}; exec sh"' &"""
        else:
            return f"xterm -title '{window_name}' -hold -e {command} &"
