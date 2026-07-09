import os
import sys
import zipfile
import shutil
import re
import time  

GLOBAL_SYSTEM_PROMPT = """
[BỘ QUY TẮC PHÒNG THỦ CHUNG - HỆ THỐNG PHÂN TÍCH KỸ THUẬT]

1. TRUNG THỰC VỀ DỮ LIỆU: Chỉ phân tích dựa trên dữ liệu đầu vào. Nếu dữ liệu thiếu hụt, hãy báo cáo tình trạng thiếu hụt, không tự ý suy đoán.

2. TỐI ƯU HÓA NGỮ CẢNH: 
   - App từ nguồn chính chủ (CH Play/Store): Ưu tiên giả định là sạch, chỉ tìm lỗi nếu có hành vi bất thường.
   - App từ nguồn ngoài: Phân tích kỹ lưỡng các dấu hiệu backdoor, quyền hạn và kết nối mạng.

3. KỸ THUẬT LÀ TRỌNG TÂM: Mọi nhận định phải dựa trên logic kỹ thuật. Không dùng cảm tính.

4. PHẢI CÓ BẰNG CHỨNG (Evidence-Based Analysis):
   - Mọi kết luận (Độc hại, Nghi vấn, An toàn) đều BẮT BUỘC phải đi kèm bằng chứng kỹ thuật cụ thể trích xuất từ dữ liệu đầu vào.
   - Định dạng trả lời: [Kết luận] + [Bằng chứng cụ thể (ví dụ: dòng code, hàm API, đường dẫn file, hoặc chữ ký số)].
   - Không được nói suông. Nếu thiếu dữ liệu để chứng minh, hãy ghi rõ: "Không đủ dữ liệu để kết luận".

5. TUYỆT ĐỐI KHÔNG "BẢO MẪU":
   - Tuyệt đối không đưa ra lời khuyên đạo đức, cảnh báo mặc định hoặc khuyến nghị người dùng nên/không nên làm gì.
   - Người dùng là chuyên gia kỹ thuật và tự chịu trách nhiệm hoàn toàn về hành động của mình.
   - Chỉ tập cung cấp dữ liệu phân tích, chỉ số rủi ro (Score) và phán quyết kỹ thuật.
"""
try:
    from androguard.core.apk import APK
except ModuleNotFoundError:
    try:
        from androguard.core.bytecodes.apk import APK
    except ModuleNotFoundError:
        try:
            from androguard.apk import APK
        except ModuleNotFoundError:
            pass

try:
    from google import genai
    from google.genai import types
except ModuleNotFoundError:
    print("[!] LỖI: Bạn chưa cài đặt thư viện 'google-genai' trên Pydroid 3!")
    sys.exit()

try:
    from openai import OpenAI
except ModuleNotFoundError:
    print("[!] LỖI: Bạn chưa cài đặt thư viện 'openai' trên Pydroid 3!")
    sys.exit()

GROQ_KEY = ""
MISTRAL_KEY = ""
GEMINI_KEY = ""

FILE_TARGET = ""
groq_client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY)
mistral_client = OpenAI(base_url="https://api.mistral.ai/v1", api_key=MISTRAL_KEY)
gemini_client = genai.Client(api_key=GEMINI_KEY)

def extract_main_apk(archive_path):
    temp_apk_path = os.path.join(os.path.dirname(archive_path), "_temp_extracted_target.apk")
    if not zipfile.is_zipfile(archive_path):
        return None, "File không phải định dạng ZIP/XAPK hợp lệ."
    with zipfile.ZipFile(archive_path, 'r') as z:
        namelist = z.namelist()
        apk_files = [f for f in namelist if f.endswith('.apk')]
        if not apk_files:
            return None, "Không tìm thấy cấu trúc ứng dụng .apk nào bên trong."
        main_apk = None
        for apk in apk_files:
            if os.path.basename(apk).lower() == "base.apk":
                main_apk = apk
                break
        if not main_apk:
            apk_info_list = [z.getinfo(apk) for apk in apk_files]
            largest_apk_info = max(apk_info_list, key=lambda x: x.file_size)
            main_apk = largest_apk_info.filename
        print(f"[zip] 📦 Đã phát hiện định dạng gói nén ({os.path.splitext(archive_path)[1].upper()}).")
        print(f"[zip] 📂 Đang trích xuất APK cốt lõi để phân tích: {os.path.basename(main_apk)}...")
        with z.open(main_apk) as source, open(temp_apk_path, "wb") as target:
            shutil.copyfileobj(source, target)
    return temp_apk_path, None

class SmartApkExtractor:
    def __init__(self, apk_path):
        print(f"[+] ⚙️ Đang mổ xẻ cấu trúc file bằng Androguard...")
        self.apk = APK(apk_path)
        self.apk_path = apk_path
    
    def get_summary(self):
        exported_activities = []
        for activity in self.apk.get_activities():
            try:
                if self.apk.is_activity_exported(activity): exported_activities.append(activity)
            except: pass

        is_signed = False
        sig_schemes = []
        certificates_info = []
        
        try:
            is_signed = self.apk.is_signed()
            if self.apk.is_signed_v1(): sig_schemes.append("V1 (Jar Signing)")
            if self.apk.is_signed_v2(): sig_schemes.append("V2 (Full APK)")
            if self.apk.is_signed_v3(): sig_schemes.append("V3 (Anti-Tamper)")
            
            for cert in self.apk.get_certificates():
                issuer_str = ""
                if hasattr(cert, 'issuer'):
                    if hasattr(cert.issuer, 'human_friendly'): issuer_str = cert.issuer.human_friendly
                    elif hasattr(cert.issuer, 'native'):
                        nat = cert.issuer.native
                        issuer_str = ", ".join([f"{k}={v}" for k, v in nat.items()]) if isinstance(nat, dict) else str(nat)
                    if not issuer_str: issuer_str = str(cert.issuer)

                subject_str = ""
                if hasattr(cert, 'subject'):
                    if hasattr(cert.subject, 'human_friendly'): subject_str = cert.subject.human_friendly
                    elif hasattr(cert.subject, 'native'):
                        nat = cert.subject.native
                        subject_str = ", ".join([f"{k}={v}" for k, v in nat.items()]) if isinstance(nat, dict) else str(nat)
                    if not subject_str: subject_str = str(cert.subject)

                serial = str(cert.serial_number) if hasattr(cert, 'serial_number') else "Không rõ"
                sha256_fp = getattr(cert, "sha256", "Không rõ")
                if callable(sha256_fp): sha256_fp = sha256_fp().hex()

                certificates_info.append({
                    "issuer": issuer_str if issuer_str else "Không rõ",
                    "subject": subject_str if subject_str else "Không rõ",
                    "serial_number": serial,
                    "sha256_fingerprint": sha256_fp
                })
        except Exception:
            pass

        print(f"[+] 🔍 Đang quét sâu các tệp thực thi nội bộ để tìm từ khóa mã độc...")
        android_signatures = {
            "Thực thi lệnh hệ thống ẩn (Shell/Root)": r"(Runtime\.getRuntime\(\)\.exec|ProcessBuilder|/system/bin/sh|\bsu\b)",
            "Tải và thực thi mã độc động (Dex Injection)": r"(DexClassLoader|PathClassLoader|dalvik\.system)",
            "Can thiệp tin nhắn SMS ngầm (SMS Spy)": r"(SmsManager|sendTextMessage|\bRECEIVE_SMS\b)",
            "Thu thập thông tin định danh thiết bị (Spyware)": r"(getDeviceId|getSubscriberId|getSimSerialNumber|TelephonyManager)",
            "Kết nối mạng lén lút / Giao tiếp C2 Server": r"(java\.net\.URL|java\.net\.Socket|HttpURLConnection|OkHttpClient)",
            "Ghi âm / Quay phim ngầm (Trojan/Spy)": r"(MediaRecorder|Camera\.open|AudioRecord)"
        }
        
        code_scan_alerts = []
        try:
            with zipfile.ZipFile(self.apk_path, 'r') as z:
                for file_name in z.namelist():
                    if any(file_name.endswith(ext) for ext in ['.dex', '.sh', '.py', '.js']):
                        with z.open(file_name) as f:
                            content = f.read(5 * 1024 * 1024).decode('utf-8', errors='ignore')
                        
                        for rule_name, pattern in android_signatures.items():
                            matches = re.findall(pattern, content)
                            if matches:
                                code_scan_alerts.append({
                                    "internal_file": file_name,
                                    "rule": rule_name,
                                    "detected_keywords": list(set(matches))[:5]
                                })
        except Exception as e:
            print(f"[!] Lỗi khi quét mã nguồn nội bộ APK: {e}")

        return {
            "package_name": self.apk.get_package(),
            "target_sdk": self.apk.get_target_sdk_version(),
            "min_sdk": self.apk.get_min_sdk_version(),
            "permissions": self.apk.get_permissions(),
            "exported_activities": exported_activities,
            "services_count": len(self.apk.get_services()),
            "receivers_count": len(self.apk.get_receivers()),
            "is_signed": is_signed,
            "signature_schemes_found": sig_schemes,
            "certificates_detailed_info": certificates_info,
            "code_scan_alerts": code_scan_alerts
        }

class HeuristicSourceScanner:
    def __init__(self, filepath):
        self.filepath = filepath
        self.signatures = {
            "Thực thi mã ẩn / Lệnh hệ thống độc hại": r"(os\.system|subprocess\.|eval\(|exec\(|popen|cmd)",
            "Mã hóa giấu vết độc hại (Obfuscation)": r"(base64\.b64decode|hex\.decode|getattr|zlib\.decompress)",
            "Kết nối mạng lén lút (Backdoor/Shell)": r"(socket\.socket|requests\.get|urllib\.request|curl|wget)",
            "Địa chỉ IP cứng bên ngoài": r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
            "Hành vi xóa/Phá hủy tệp hệ thống": r"(rm -rf|os\.remove|os\.rmdir|chmod 777)"
        }

    def scan(self):
        findings = []
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for line_num, content in enumerate(lines, 1):
                stripped = content.strip()
                if stripped.startswith("#") or not stripped: continue
                for rule_name, pattern in self.signatures.items():
                    if re.search(pattern, stripped):
                        findings.append({
                            "line": line_num,
                            "rule": rule_name,
                            "code_snippet": stripped[:100]
                        })
            return lines, findings
        except Exception as e:
            print(f"[!] Lỗi đọc tệp mã nguồn: {e}")
            return None, []

class Gatekeeper:
    def __init__(self, data, is_code=False):
        self.data = data
        self.is_code = is_code
        self.score = 0
        self.reasons = []

    def evaluate(self):
        if self.is_code:
            alerts = self.data.get('heuristic_alerts', [])
            self.score = len(alerts) * 2
            if self.score > 0:
                self.reasons.append(f"Phát hiện {len(alerts)} lỗ hổng/hành vi mã lệnh nhạy cảm.")
            return self.score >= 4
        else:
            if not self.data.get('is_signed', True):
                self.score += 10
                self.reasons.append("🚨 CỰC KỲ NGUY HIỂM: Ứng dụng KHÔNG CÓ CHỮ KÝ SỐ!")
            
            certs = self.data.get('certificates_detailed_info', [])
            for c in certs:
                issuer_lower = c['issuer'].lower()
                if "debug" in issuer_lower or "testkey" in issuer_lower or "android" in issuer_lower:
                    self.score += 8
                    self.reasons.append(f"🚨 PHÁT HIỆN CHỮ KÝ LẬU: Sử dụng Testkey/Debug key nghiệp dư ({c['issuer']})!")
                    break

            dangerous_perms = ["android.permission.SEND_SMS", "android.permission.READ_SMS", "android.permission.RECEIVE_SMS", "android.permission.BIND_ACCESSIBILITY_SERVICE"]
            for perm in self.data.get('permissions', []):
                if perm in dangerous_perms:
                    self.score += 5
                    self.reasons.append(f"Yêu cầu quyền nhạy cảm: {perm.split('.')[-1]}")
            
            code_alerts = self.data.get('code_scan_alerts', [])
            if code_alerts:
                self.score += len(code_alerts) * 2
                self.reasons.append(f"🔥 CẢNH BÁO CODE: Phát hiện {len(code_alerts)} file nội bộ chứa từ khóa API nguy hiểm.")

            return self.score >= 5

def call_gemini_analyst(prompt, system_instruction):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system_instruction)
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                if attempt < max_retries - 1:
                    wait_time = 15 * (attempt + 1)
                    print(f"[!] Đang nghẽn API Gemini ở tầng Analyst (429). Đang retry sau {wait_time} giây... (Lần {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"\n[🚨 CRITICAL] Đã thử Gemini {max_retries} lần đều thất bại do Rate Limit!")
                    print("[⚡ SYSTEM] Đang chuyển giao lập tức sang cho Groq gánh thay...")
            else:
                if attempt < max_retries - 1:
                    print(f"[!] Lỗi API Gemini ({error_str}). Đang thử lại sau 3 giây... (Lần {attempt+1}/{max_retries})")
                    time.sleep(3)
                else:
                    print(f"\n[🚨 CRITICAL] Đã thử Gemini {max_retries} lần đều dính lỗi hệ thống khác!")
                    print("[⚡ SYSTEM] Đang chuyển giao lập tức sang cho Groq gánh thay...")
                    
    try:
        res = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        )
        return "⚠️ [BÁO CÁO THAY THẾ CHUYÊN SÂU TỪ GROQ LLAMA 3.3 - DO GEMINI LỖI QUÁ 5 LẦN]\n" + res.choices[0].message.content
    except Exception as groq_err:
        return f"❌ THẤT BẠI TOÀN DIỆN: Cả Gemini (lỗi quá 5 lần) và Groq dự phòng đều không kết nối được: {groq_err}"

def call_mistral_critic(prompt, system_instruction):
    try:
        response = mistral_client.chat.completions.create(
            model="mistral-large-latest",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Thất bại tại lớp lọc Critic (Mistral AI): {e}"

def call_groq_judge(prompt, system_instruction):
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Thất bại tại lớp lọc Judge tối cao (Groq): {e}"

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   HỆ THỐNG SOC TRUNG TÂM - QUÉT APK & MÃ NGUỒN ĐỘC HẠI   ")
    print("="*60)

    if not os.path.exists(FILE_TARGET):
        print(f"[!] LỖI: Không tìm thấy file tại đường dẫn: {FILE_TARGET}")
        sys.exit()

    ext = os.path.splitext(FILE_TARGET)[1].lower()
    is_code_file = ext in ['.py', '.sh', '.php', '.txt', '.js', '.java', '.cs']

    is_temporary_file = False
    scan_path = FILE_TARGET
    payload_data = {}
    
    instruction_analyst = ""
    instruction_judge = ""

    try:
        if is_code_file:
            print(f"[+] 🔍 Phát hiện tệp mã nguồn script. Đang chạy bộ quét mã độc tĩnh...")
            scanner = HeuristicSourceScanner(FILE_TARGET)
            raw_lines, alerts = scanner.scan()
            if raw_lines is None: sys.exit()
            
            payload_data = {
                "file_name": os.path.basename(FILE_TARGET),
                "heuristic_alerts": alerts,
                "raw_source_code": "".join(raw_lines)
            }
            gatekeeper = Gatekeeper(payload_data, is_code=True)
            is_high_risk = gatekeeper.evaluate()

            print(f"\n[📊] KẾT QUẢ QUÉT NHANH MÃ NGUỒN FILE TĨNH:")
            print(f" ├─ Tổng số dòng lệnh: {len(raw_lines)}")
            print(f" └─ Phát hiện nghi vấn: {len(alerts)} cờ đỏ cảnh báo")
            if alerts:
                print("\n[🚨] CÁC DÒNG CODE NGHI CHỨA MÃ ĐỘC TRÊN MÀN HÌNH:")
                for a in alerts:
                    print(f" ├─ [Dòng {a['line']}] [{a['rule']}]: {a['code_snippet']}")

            instruction_analyst = GLOBAL_SYSTEM_PROMPT + "\n" + (
                "Bạn là Chuyên gia Phân tích Mã độc chuyên đánh giá mã nguồn (Source Code). Hãy xem kỹ đoạn code được gửi "
                "and danh sách cờ đỏ phát hiện. Giải thích chi tiết xem đoạn code này có chứa hành vi backdoor, đánh cắp dữ liệu, "
                "hoặc phá hoại hệ thống hay không bằng tiếng Việt."
            )
            instruction_judge = GLOBAL_SYSTEM_PROMPT + "\n" + (
                "Bạn là Thẩm phán trưởng SOC chuyên đánh giá mã nguồn. Dựa trên báo cáo, mọi phán quyết phải tuân thủ nghiêm ngặt quy trình logic sau:\n"
                "1. VẬT CHỨNG (Evidence): Liệt kê chính xác dữ liệu thô (dòng code, hàm API, hành vi hệ thống nghi vấn) bị bắt quả tang từ đầu vào.\n"
                "2. LUẬN CỨ (Analysis): Phân tích logic tại sao vật chứng trên vi phạm nguyên tắc an toàn thông tin. Tuyệt đối không suy đoán ngoài dữ liệu.\n"
                "3. GIẢI THÍCH ĐIỂM SỐ: Nêu rõ lý do cộng/trừ điểm rủi ro chi tiết dựa trên từng luận điểm kỹ thuật cụ thể.\n"
                "4. PHÁN QUYẾT (Verdict): Đưa ra trạng thái duy nhất (ĐỘC HẠI / AN TOÀN / NGHI VẤN) và Điểm rủi ro tổng kết (thang điểm từ 0/10 đến 10/10).\n"
                "Tuyệt đối KHÔNG sử dụng ngôn ngữ cảm tính, không đưa ra lời khuyên hay cảnh báo bảo mẫu cho người dùng. Nếu thiếu dữ liệu để chứng minh, phán quyết là 'Không thể kết luận'."
            )

        else:
            if FILE_TARGET.endswith(('.xapk', '.zip', '.apks')):
                extracted_apk, error = extract_main_apk(FILE_TARGET)
                if error:
                    print(f"[!] LỖI PHÂN RÃ FILE: {error}")
                    sys.exit()
                scan_path = extracted_apk
                is_temporary_file = True

            extractor = SmartApkExtractor(scan_path)
            payload_data = extractor.get_summary()
            gatekeeper = Gatekeeper(payload_data, is_code=False)
            is_high_risk = gatekeeper.evaluate()

            print(f"\n[📊] KẾT QUẢ PHÂN TÍCH CHỮ KÝ SỐ CHI TIẾT:")
            print(f" ├─ Trạng thái: {'Đã được ký bảo mật' if payload_data['is_signed'] else 'KHÔNG CÓ CHỮ KÝ'}")
            if payload_data['signature_schemes_found']:
                print(f" ├─ Công nghệ mã hóa: {', '.join(payload_data['signature_schemes_found'])}")
            
            if payload_data['certificates_detailed_info']:
                for idx, cert in enumerate(payload_data['certificates_detailed_info'], 1):
                    print(f" ├─ Chứng chỉ #{idx}:")
                    print(f" │   ├── 👤 Người phát hành (Issuer) : {cert['issuer']}")
                    print(f" │   ├── 🎯 Đối tượng ký (Subject)  : {cert['subject']}")
                    print(f" │   ├── 🔢 Số Serial               : {cert['serial_number']}")
                    print(f" │   └── 🔑 Mã Vân tay SHA256        : {cert['sha256_fingerprint']}")
            
            if payload_data['code_scan_alerts']:
                print(f"\n[🚨] KẾT QUẢ QUÉT TỪ KHÓA MÃ NGUỒN NỘI BỘ APK:")
                for alert in payload_data['code_scan_alerts']:
                    print(f" ├─ File: {alert['internal_file']}")
                    print(f" │   ├── 🛑 Nhóm hành vi : {alert['rule']}")
                    print(f" │   └── 🔑 Từ khóa dính : {', '.join(alert['detected_keywords'])}")

            instruction_analyst = GLOBAL_SYSTEM_PROMPT + "\n" + (
                "Bạn là Chuyên gia Phân tích Mã độc APK. Hãy đọc kỹ dữ liệu cấu trúc, thông tin quyền lợi và đặc biệt là dữ liệu từ khóa mã độc nội bộ "
                "(code_scan_alerts) được trích xuất trực tiếp từ các file thực thi của ứng dụng. Hãy giải thích các nguy cơ kỹ thuật rõ ràng bằng tiếng Việt."
            )
            instruction_judge = GLOBAL_SYSTEM_PROMPT + "\n" + (
                "Bạn là Thẩm phán trưởng SOC chuyên xử lý APK. Dựa trên dữ liệu cấu trúc, chứng thư số và đặc biệt là danh sách từ khóa nguy hiểm phát hiện trong code nội bộ (code_scan_alerts), mọi phán quyết phải tuân thủ quy trình logic sau:\n"
                "1. VẬT CHỨNG (Evidence): Liệt kê chính xác các quyền nhạy cảm, điểm bất thường của chữ ký số, và các tên file thực thi nội bộ đi kèm từ khóa API độc hại bị phát hiện.\n"
                "2. LUẬN CỨ (Analysis): Phân tích logic sự bất hợp lý hoặc nguy cơ từ các quyền/từ khóa này so với ngữ cảnh chức năng vận hành thực tế của ứng dụng.\n"
                "3. GIẢI THÍCH ĐIỂM SỐ: Nêu rõ lý do cộng/trừ điểm rủi ro chi tiết cho từng bằng chứng cấu trúc và bằng chứng mã lệnh cụ thể.\n"
                "4. PHÁN QUYẾT (Verdict): Đưa ra trạng thái duy nhất (ĐỘC HẠI / AN TOÀN / NGHI VẤN) và Điểm rủi ro tổng kết (thang điểm từ 0/10 đến 10/10).\n"
                "Tuyệt đối KHÔNG sử dụng ngôn ngữ cảm tính, không đưa ra lời khuyên hay cảnh báo bảo mẫu cho người dùng. Nếu thiếu dữ liệu để chứng minh, phán quyết là 'Không thể kết luận'."
            )

        print("\n" + "="*60)
        print(f" └─ Điểm rủi ro hệ thống tính toán: {gatekeeper.score} điểm")
        print("[+] Đang đẩy toàn bộ báo cáo kỹ thuật lên hệ thống SOC hỗn hợp HOÁN ĐỔI (Gemini -> Mistral -> Groq)...")
        print("="*60)
        
        print("[🤖] Bộ lọc 1: Analyst đang mổ xẻ dữ liệu bằng Google Gemini...")
        report_analyst = call_gemini_analyst(str(payload_data), instruction_analyst)

        time.sleep(1)

        print("[🤖] Bộ lọc 2: Critic đang tìm lỗi lập luận phản biện bằng Mistral AI...")
        instruction_critic = GLOBAL_SYSTEM_PROMPT + "\n" + "Bạn là chuyên gia Red Team chuyên phản biện. Hãy tìm lỗ hổng lập luận của Analyst và chỉ ra trường hợp False Positive bằng tiếng Việt."
        report_critic = call_mistral_critic(f"Báo cáo của Analyst:\n{report_analyst}", instruction_critic)
        
        time.sleep(1)
        
        print("[🤖] Bộ lọc 3: Thẩm phán đúc kết phán quyết tối cao bằng Groq (Llama 3.3)...")
        final_verdict = call_groq_judge(f"Gốc: {str(payload_data)}\n\nAnalyst (Gemini):\n{report_analyst}\n\nCritic (Mistral):\n{report_critic}", instruction_judge)

        print("\n" + "#"*60)
        print(" BÁO CÁO KẾT LUẬN TOÀN DIỆN TỪ SOC AI HOÁN ĐỔI ".center(60, "#"))
        print("#"*60)
        print(final_verdict)
        print("\n" + "#"*60)

    except Exception as e:
        print(f"\n[!] Hệ thống gặp lỗi khi xử lý luồng AI: {e}")
        
    finally:
        if is_temporary_file and os.path.exists(scan_path):
            try:
                os.remove(scan_path)
                print("[zip] 🧹 Đã dọn dẹp file trích xuất tạm thời sạch sẽ.")
            except Exception:
                pass
