📘 [🇷🇺 Russian](README.ru.md)

✅ What the script `ble_lock_set_pin.py` does
The script automatically changes the PIN code of the lock using a BLE capture (`pcapng`) that contains the handshake:

Extracts SKDm, SKDs and IV from `capture.pcapng`.

Forms a TLV with the new PIN and calculates CRC16.

Encrypts using AES-CTR, like in the Tuya Smart app.

Sends `delete` and `create` commands via Tuya OpenAPI.

Verifies successful PIN installation via DP `unlock_password`.

📦 1. How to prepare the BLE capture
Every time you want to change the PIN:

Start Wireshark

Capture for 5–10 seconds after the lock connects to the Tuya Smart app.

\-----------Important: you must start capturing **before** turning on the lock!-------------

Save the file as `capture.pcapng` and place it next to the script.

\--------⚠️ Important: the file **must** be named exactly `capture.pcapng` — the script expects this name.--------
If you want to use a different name — just replace `"capture.pcapng"` in the script.

🛠️ 2. What to configure in the script — I’ve already done it, just double-check it —
In `ble_lock_set_pin.py`:

```
ACCESS_ID    = "..."      # Your API ID from Tuya  
ACCESS_KEY   = "..."      # Your Secret Key  
DEVICE_ID    = "..."      # The device (lock) ID  
LOCAL_KEY    = b"..."     # 16-byte local_key of the lock  
NEW_PIN      = "124578"   # New PIN code (6 digits)  
PASSWORD_ID  = 1          # Slot ID, usually 1  
```

Everything else is automated, no need to touch it.
All steps are marked in the code as STEP 1, STEP 2, etc. with detailed comments.

📥 3. Install dependencies (if not yet installed)
\-------------Run once in the console:-------------------

Each command is separate — run one by one in the command line. First install the dependencies, then go to the folder with the files.

Python 3.10.11 was used — but the script should work from Python 3.7 to 3.12 (not tested, but by code it should).

To check your version:

python --version


If the version is wrong, remove it completely including all folders in your user profile — go to your username folder on the disk, find `AppData`, and delete the Python folder. Then reboot and install the required version.

Dependencies:


pip install tuya-connector-python pycryptodome crcmod   # First command, mandatory

pip install pyshark   # PyShark / TShark — the script uses pyshark.  
                      # You need Wireshark/TShark installed on your PC (runtime is enough).  
                      # If TShark is not in PATH, PyShark will throw an error.  
                      # ----“Install Wireshark ≥ 3.4 and make sure TShark is accessible from command line.”----

pip install tuya-iot-py-sdk   # Tuya SDK — not required for this script, but I had it installed, might be helpful

pip install rich             # 🌈 rich — pretty log output in the console

pip install ipython          # 🧠 ipython — interactive Python shell. Very convenient for testing and live script editing.


\----------Capture file-----------

Must include both packets: `LL_ENC_REQ` / `LL_ENC_RSP`.

Default name: `capture.pcapng`; if using another name — change `PCAP_FILE`.

🚀 4. How to run


python ble_lock_set_pin.py


(Obviously in the console, run: `cd path_to_folder` then `python ble_lock_set_pin.py`)

If everything goes well, you will see:

\-------------  LOCAL\_KEY  --------------

Must be 16 bytes, no spaces, in the format `b"..."`.

If you're using another lock — you must replace it with its local\_key.

\------------------------------Limitations--------------------------------

The lock must be online at the time the script runs.
🎉 PIN applied — enter 124578 on the lock!

📌 Summary:

| What            | Required                        |
| --------------- | ------------------------------- |
| 🔁 New PIN      | Set `NEW_PIN` in the script     |
| 📄 New capture  | `capture.pcapng` next to script |
| 📦 Dependencies | See above                       |
| 💬 Language     | Python 3.10.11                  |

---
License
This project is licensed under the MIT License. See LICENSE for details.


