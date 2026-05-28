# Device Support

## Supported Devices

This client has been tested with:

| Device | PRODUCT_CODE | FW Code | Notes |
|---|---|---|---|
| SEKO PoolDose Double | PDPR1H1HAW100 | 539187 | |
| SEKO PoolDose Double Spa | PDPR1H04AW100 | 539292 | |
| SEKO POOLDOSE pH+ORP CF Group Wi-Fi | PDPR1H1HAW102 | 539187 | Alias for PDPR1H1HAW100 mapping |
| SEKO PoolDose pH | PDPH1H1HAW100 | 539176 | pH-only device |
| BWT MEDO CONNECT Wi-Fi | PDPH1H1HAW1B0 | 539494 | Based on SEKO PoolDose pH mapping |
| VÁGNER POOL VA DOS BASIC | PDHC1H1HAR1V0 | 539224 | |
| VÁGNER POOL VA DOS EXACT | PDHC1H1HAR1V1 | 539224 | Alias for PDPR1H1HAR1V0 mapping |

Other SEKO or VÁGNER POOL models may work but are untested. The client uses JSON mapping files to adapt to different device models and firmware versions (see e.g. `src/pooldose/mappings/model_PDPR1H1HAW100_FW539187.json`).

> **Note:** The JSON files in the mappings directory define the device-specific data keys and their human-readable names for different PoolDose models and firmware versions.

## How to Request Support for a New Device

If your device is not yet supported, please help us by creating a GitHub issue and providing the following information:

1. **Run low-level analysis and share the output files:**
    - Use the following curl commands. 
    - Replace the IP address and DeviceId (get the id from the header of the instantvalues.json file, e.g., '012345679_DEVICE') as needed:
    
    - Download debug config info:
      ```bash
      curl http://<YOUR_DEVICE_IP>/api/v1/debug/config/info -o debuginfo.json
      ```
      **Important:** Before uploading, open `debuginfo.json` and remove any WiFi credentials.
    - Download instant values
      ```bash
      curl --location --request POST http://<YOUR_DEVICE_IP>/api/v1/DWI/getInstantValues -o instantvalues.json
      ```
    - Download device language strings
      ```bash
      curl --location http://<YOUR_DEVICE_IP>/api/v1/DWI/getDeviceLanguage --data-raw '{"DeviceId":"YOUR_DEVICE_ID","LANG":"en"}' -o strings.json
      ```
2. **Optional: Run the analyzer and share the output:**
    - Run this command if you set up python-pooldose already:
      ```bash
      pooldose --host <YOUR_DEVICE_IP> --analyze
      ```
    - Copy and paste the full output into your issue (remove any sensitive data).

3. **Create a GitHub issue:**
    - Attach the the 3 JSON files from above.
    - Optionally attach the analyzer output if available.
    - This will help us add support for your device faster!
