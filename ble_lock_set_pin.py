#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ble_lock_set_pin.py  —  смена PIN  (jtmspro, BLE-Gateway)
• автоматически достаёт SKDm/SKDs + IV из capture.pcapng
• формирует TLV (01-id 02-pwd 03-permanent 04-CRC16)
• шифрует AES-CTR (ключ = AES_ECB(local_key, SKDm‖SKDs) ⊕ SKDs‖SKDm)
• шлёт DP unlock_method_delete + unlock_method_create
"""
import struct, time, base64, json, crcmod, pyshark
from Crypto.Cipher import AES
from Crypto.Util import Counter
from tuya_connector import TuyaOpenAPI

# -------------- настройки Tuya -------------
API_ENDPOINT = "https://openapi.tuyaeu.com"
ACCESS_ID    = ""
ACCESS_KEY   = ""
DEVICE_ID    = ""
LOCAL_KEY    = b""      # 16-байтовый из /devices
# -------------- параметры PIN --------------
PASSWORD_ID  = 1
NEW_PIN      = "124578"                 # 6-цифр
PASSWORD_NAME = "API-PIN"
# -------------- pcap -----------------------
PCAP_FILE    = "capture.pcapng"         # ваш полный дамп
# -------------------------------------------

crc16 = crcmod.mkCrcFun(0x11021, initCrc=0xFFFF, xorOut=0x0000)

def extract_session_keys(pcap):
    """Возвращает SKDm, SKDs, iv_counter из LL_ENC_* пакетов."""
    SKDm = SKDs = IVm = IVs = None
    for pkt in pyshark.FileCapture(pcap, display_filter="btle.ll"):
        op = int(pkt.btle.ll_control_opcode.show)    # 3=ENC_REQ, 4=ENC_RSP
        if op == 3:   # LL_ENC_REQ
            SKDm = bytes.fromhex(pkt.btle.skd_m.replace(':',''))
            IVm  = bytes.fromhex(pkt.btle.iv_m.replace(':',''))
        elif op == 4: # LL_ENC_RSP
            SKDs = bytes.fromhex(pkt.btle.skd_s.replace(':',''))
            IVs  = bytes.fromhex(pkt.btle.iv_s.replace(':',''))
            break
    if None in (SKDm, SKDs, IVm, IVs):
        raise RuntimeError("Не найдено LL_ENC_REQ/RSP в pcap")
    iv_counter = IVs + IVm                # 8-байтный старт счётчика
    return SKDm, SKDs, iv_counter

def build_cipher_key(skd_m, skd_s):
    tmp = AES.new(LOCAL_KEY, AES.MODE_ECB).encrypt(skd_m + skd_s)
    return bytes(a ^ b for a, b in zip(tmp, skd_s + skd_m))

def build_tlv(pwd_id, pin):
    tlv  = b"\x01\x01" + bytes([pwd_id])
    tlv += b"\x02\x06" + pin.encode()
    tlv += b"\x03\x01\x01"
    tlv += b"\x04\x02" + struct.pack(">H", crc16(tlv))
    return tlv

def encrypt_payload(tlv, iv_counter, key):
    ctr_init = int.from_bytes(iv_counter[:4], "big")
    ctr = Counter.new(128, initial_value=ctr_init)
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    return iv_counter[:4] + cipher.encrypt(tlv)

def main():
    SKDm, SKDs, iv_counter = extract_session_keys(PCAP_FILE)
    key = build_cipher_key(SKDm, SKDs)
    tlv = build_tlv(PASSWORD_ID, NEW_PIN)
    cipher_part = encrypt_payload(tlv, iv_counter, key)
    frame_prefix = b"\x31\x40\x05\x12"
    payload = frame_prefix + cipher_part
    b64_value = base64.b64encode(payload).decode()

    openapi = TuyaOpenAPI(API_ENDPOINT, ACCESS_ID, ACCESS_KEY)
    openapi.connect()

    # delete
    openapi.post(f"/v1.0/devices/{DEVICE_ID}/commands", {
        "commands":[{"code":"unlock_method_delete",
                     "value":{"password_id":PASSWORD_ID}}]})
    time.sleep(1)

    # create (зашифрованный payload)
    resp = openapi.post(f"/v1.0/devices/{DEVICE_ID}/commands", {
        "commands":[{"code":"unlock_method_create","value":b64_value}]})
    print("create resp:", json.dumps(resp,indent=2,ensure_ascii=False))

    # Проверяем DP
    time.sleep(5)
    status = openapi.get(f"/v1.0/devices/{DEVICE_ID}/status")
    dp_val = next((x["value"] for x in status["result"]
                   if x["code"]=="unlock_password"),0)
    if dp_val:
        print("🎉 PIN", NEW_PIN, "применён.")
    else:
        print("⚠ DP ещё 0 – подождите синхронизации или проверьте данные.")

if __name__ == "__main__":
    import time
    main()
