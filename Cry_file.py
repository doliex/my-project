import os
from cryptography.fernet import Fernet, InvalidToken

def encrypt_file_inplace(filename, key):
    try:
        f = Fernet(key)
        with open(filename, 'rb') as file:
            file_data = file.read()
        
        encrypted_data = f.encrypt(file_data)
        
        with open(filename, 'wb') as file:
            file.write(encrypted_data)
        print(f"[*] THÀNH CÔNG! Đã mã hóa: {filename}")
        
    except Exception as e:
        print(f"[!] LỖI KHI MÃ HÓA: {e}")

def decrypt_file_inplace(filename, key):
    try:
        f = Fernet(key)
        with open(filename, 'rb') as file:
            encrypted_data = file.read()
            
        decrypted_data = f.decrypt(encrypted_data)
        
        with open(filename, 'wb') as file:
            file.write(decrypted_data)
        print(f"[*] THÀNH CÔNG! Đã giải mã: {filename}")
        
    except ValueError:
        print("[!] LỖI: Định dạng Key không hợp lệ (Phải là chuỗi chuẩn 44 ký tự)!")
    except InvalidToken:
        print("[!] LỖI: Key sai hoặc dữ liệu file đã bị hỏng vĩnh viễn!")
    except Exception as e:
        print(f"[!] LỖI KHI GIẢI MÃ: {e}")

def main():
    print("--- CÔNG CỤ MÃ HÓA & GIẢI MÃ (bản 2.0) ---")
    print("Gõ 'stop' ở bất kỳ bước nào để thoát.\n")

    while True:
        # Tự động dọn dẹp khoảng trắng và dấu ngoặc kép thừa
        filename = input("\nNhập đường dẫn/tên file: ").strip().strip('"').strip("'")
        if filename.lower() == 'stop':
            break
        
        if not os.path.exists(filename):
            print(f"[!] Không tìm thấy '{filename}'. Hãy kiểm tra lại đường dẫn!")
            continue
            
        if not os.path.isfile(filename):
            print(f"[!] '{filename}' là một thư mục! Bạn phải nhập tên một file cụ thể.")
            continue

        action = input("Chọn hành động (encrypt/decrypt): ").strip().lower()
        if action == 'stop':
            break

        if action == 'encrypt':
            key = Fernet.generate_key()
            print(f"\n[!] >>> KEY CỦA BẠN LÀ: {key.decode()} <<<")
            print("(HÃY COPY VÀ LƯU LẠI NGAY! NẾU MẤT KEY LÀ MẤT FILE)\n")
            encrypt_file_inplace(filename, key)
            
        elif action == 'decrypt':
            key_input = input("Nhập key giải mã: ").strip()
            if key_input.lower() == 'stop':
                break
            # Chuyển string thành bytes để giải mã
            decrypt_file_inplace(filename, key_input.encode())
            
        else:
            print("[!] Hành động không hợp lệ. Chỉ gõ 'encrypt' hoặc 'decrypt'.")
        print("-" * 45)

if __name__ == "__main__":
    main()
