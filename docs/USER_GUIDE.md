# Your first Enigma message

## Connect

Connect your flashed Shrike Fi by USB and open the app. Close Arduino Serial Monitor first. Click **Refresh**, choose your board's port, then **Connect**. Wait for verification to finish. If the board is not flashed yet, follow [installation](BUILD_AND_USE.md).

## Try a message

1. Choose rotors **I, II, III** from left to right.
2. Set all three **Window** letters to **A**, and all three **Ring** letters to **A**. Leave the plugboard empty.
3. Enter **HELLOWORLD** in Input Message and click **Encrypt**.
4. The output should be **ILBDAAMTAZ**.
5. Put **ILBDAAMTAZ** in Input Message and click **Decrypt**, keeping those same settings. You should get **HELLOWORLD** back.

Encrypt and Decrypt automatically apply the visible settings. You do not need to click Apply Configuration first. Apply Configuration is useful when you only want to send settings to the board.

## What the settings mean

| Control | Meaning |
| --- | --- |
| Rotors | Three different letter-scrambling wheels, chosen from I–V. Their left-to-right order matters. |
| Window | The starting letter shown on each wheel. These are the starting positions for every message. |
| Ring | The offset of each wheel's internal wiring relative to its letter markings. Leave these at A while learning. |
| Plugboard | Optional letter swaps before and after the wheels. Add AB to swap A with B. Each letter can appear in only one pair; leave it empty for the first example. |
| Final positions | Where the wheels ended after processing. These are information only: keep the original Window settings to decrypt. |
| Reset Board | Restores I–II–III, AAA windows, AAA rings, and an empty plugboard on the board and in the interface. |
| Hardware Self-test | Checks known answers on the FPGA to help confirm the board is working. |

## Exchange a message

The recipient needs the same rotor order, rings, **initial** windows and plugboard pairs. Copy all of these settings before encrypting. The same settings undo the transformation because Enigma is reciprocal. Every click starts a fresh message at your selected initial windows; it does not continue from the displayed final positions.

Messages can contain up to 512 ASCII characters. Lowercase becomes uppercase. Spaces, digits, punctuation and line breaks stay in place and do not move the wheels. Emoji and accented letters are not accepted.

## If something goes wrong

- No port: check the USB data cable, then Refresh. Port names can change after reconnecting.
- Cannot connect: close other serial programs and confirm firmware and LittleFS were both flashed using the installation guide.
- Wrong decrypted text: check every setting, especially the original windows and rotor order.
- Duplicate rotor or plugboard error: choose three different rotors and use each plugboard letter only once.
- Board error: follow the displayed error; reconnect and reapply settings before retrying. The app requires working FPGA hardware.

This is a historical cipher demonstrator. Use modern encryption for private information.
