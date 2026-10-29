# Meet your Enigma machine

Turn a message into a secret-looking string of letters, then recover it with the same settings. The laptop controls the machine; your Shrike Fi performs the cipher work.

## Start with just three actions

1. **Connect:** plug in your flashed board, close Arduino Serial Monitor, click **Refresh**, choose the USB port, then **Connect**. Wait for verification.
2. **Type:** leave the settings at I–II–III, Window AAA, Ring AAA, and an empty plugboard. Enter `HELLOWORLD` in **Input Message**.
3. **Encrypt:** click **Encrypt**. You should see `ILBDAAMTAZ` in the output.

Now replace the input with `ILBDAAMTAZ` and click **Decrypt**, keeping the settings unchanged. Welcome back, `HELLOWORLD`!

If your board has not been installed yet, start with the [setup guide](BUILD_AND_USE.md). After Python setup on macOS, double-click `Launch Enigma.command` to open the app.

## Find your way around the controls

The controls are dropdown menus rather than round, draggable dials. Click a dropdown to choose a value, or focus it and use the up/down arrow keys. You do not need to change every control to use the machine.

Read the three configuration rows as **left wheel, middle wheel, right wheel**. Each row has three choices:

| Control | Think of it as… | First experiment |
| --- | --- | --- |
| Rotor | Which scrambling wheel is installed. Pick three different wheels from I–V; order matters. | Keep I, II, III. |
| Window | The letter visible through that wheel's window before a message starts. | Change only the right Window from A to B. |
| Ring | The internal wiring offset relative to the wheel's letter markings. This is a separate part of the key. | Leave all rings at A until you are comfortable. |

**Initial windows are your starting key. Final positions are the result of movement.** Do not copy final positions into the Window menus to decrypt. Every Encrypt or Decrypt starts again from the visible initial settings.

For everyday use you need **Connect**, the input box, and **Encrypt/Decrypt**. The other buttons have specific jobs:

| Button | When to use it |
| --- | --- |
| Apply Configuration | Send settings without processing a message. Encrypt and Decrypt already apply the visible settings automatically. |
| Reset Board | Return both the board and visible settings to I–II–III, AAA windows, AAA rings, and no plugs. |
| Hardware Self-test | Check known answers on the FPGA when troubleshooting. |
| Clear | Clear message text; this is different from resetting the machine settings. |

## Plugboard: connect letters in pairs

Imagine a cable between **A** and **B**. That pair swaps A with B in both directions before the signal enters the rotors, and again after it returns. Letters without a cable pass through this stage unchanged. The complete machine still scrambles them through its rotors.

### Add your first cable

1. Start with the default settings and click **Clear All** in the Plugboard section if any pairs are listed.
2. Click **+ Add Pair**.
3. Type `AB` — exactly two letters, without a space or dash — and confirm the dialog.
4. Check that `AB` appears in the pair list.
5. Encrypt `HELLOWORLD`. With I–II–III, Window AAA and Ring AAA, the output should now be **`ILADBBMTBZ`**.
6. Put that output into the input box and click **Decrypt**, leaving `AB` in place. You get `HELLOWORLD` back.

To add a second cable, click **+ Add Pair** again and enter `CD`. With pairs `AB` and `CD`, the same message becomes **`ILACBBMTBE`**. Keep both pairs when decrypting.

### Pair rules and editing

- Each letter can have only one partner. With `AB` present, `AC` cannot be added because A is already connected.
- `BA` is the same cable as `AB`, so do not add both.
- `AA` does not connect two different letters and is invalid.
- Use letters A–Z. Add one pair per dialog, up to 13 disjoint pairs.
- To remove a cable, click its row in the list, then **- Remove**.
- **Clear All** removes all plugboard pairs. It does not reset the rotor, Window or Ring menus.
- An empty plugboard is valid and is the easiest place to start.

Changing a plug can affect letters other than those named in the pair: the plugboard acts on both the incoming letter and the letter returning from the rotors.

## Three experiments to try

### 1. One letter, several answers

Reset the board, type `AAAAA`, and Encrypt. The result is **`BDZGO`**. The same input letter produces different output letters because the wheels step before each letter. Encrypt again without changing settings: the answer repeats because each message starts from the same initial windows.

### 2. Change one part of the key

Encrypt `HELLOWORLD` with the defaults and write down the output. Change only the right Window to B and encrypt again. Compare the results. Decrypt the new output first with Window AAA, then with AAB. Only the matching starting settings recover the original message.

Try the same experiment with a Ring setting or one plugboard pair. Change one thing at a time so you can see its effect.

### 3. Send a friend a puzzle

Agree on a key card, then exchange ciphertext:

```text
Rotor order (left → right): I / II / III
Initial windows:           A / A / A
Rings:                     A / A / A
Plugboard pairs:            AB, CD
```

Send a short message such as `MEET AT NOON`. Your friend enters the same key card and clicks Decrypt. As a challenge, give them three possible right-window letters and let them discover which one works. This is a manual puzzle; the app does not perform automatic Bombe-style key searches.

## What happens to your text?

Messages can contain up to **512 ASCII characters**. Lowercase becomes uppercase. Spaces, digits, punctuation and line breaks stay in place and do not advance the wheels. Emoji and accented letters are not accepted. Decryption recovers the uppercase version of the original message.

## When you get stuck

| What you see | What to try |
| --- | --- |
| No board in the port menu | Check the USB data cable, reconnect, then Refresh. The port name may change. |
| Port busy or connection fails | Close Arduino Serial Monitor and other serial programs. Check that firmware and LittleFS were both installed. |
| Decryption gives the wrong message | Match rotor order, rings, original windows and every plugboard pair. Use initial windows, not final positions. |
| Duplicate rotor error | Select three different rotor numbers. |
| Plugboard pair rejected | Check that both letters are different and neither already appears in another pair. |
| Hardware or transport error | Follow the displayed error, reconnect, and reapply settings before trying again. |

Enigma is a historical cipher for learning and experimentation. Use modern encryption for private information.
