from local_binaries import AndroidBinaries

if __name__ == "__main__":
    device_id = "your_id" #oneplus
    phone = AndroidBinaries(
        visual=True
    )
    print(phone.adb) #print adb path  ***/adb
    print(phone.scrcpy) #print scrcpy path ***/scrcpy
    print(phone.device_id) #print device id RF8M827WX7H