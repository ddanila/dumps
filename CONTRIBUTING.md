# Conventions

How sets are laid out and documented in this repository. Run
`python3 tools/check.py` before committing. CI runs the same checks on every
push.

## Layout

- **One folder per physical device**: `<maker>/<device>/`. A device with
  several boards or chips gets subfolders, e.g.
  `nokia/data-modem-2400-2400/controller-810244e/` and
  `robotron/pc1715/mb001/`. Don't create sibling top-level sets for chips of
  the same device. If a chip turns out to belong to an existing device, move
  it there.
- **Unattributed sets** go under `unknown/<short-name>/`. Move them once the
  device is identified.
- Folder names describe the hardware. Dates and inventory IDs go in the
  manifest and README, not the folder name. Some older folders still carry
  dates.
- Inside a set:
  - the dump files, named after the label or position, e.g. `chip10-810237c.bin`;
  - `manifest.json` (machine-readable record);
  - `README.md`;
  - optional `SHA256SUMS`, `evidence/` (raw reader logs and session
    metadata, kept unchanged), `photos/`, `analysis/` and `emulation/`.
- **Investigations** that span several sets, such as reader faults or blank
  records, go in the top-level `analysis/`.

## README

1. **Title and opening paragraph**: what the chip or firmware is and what it
   belongs to. Include identification, its role, and anything notable, such as
   a version banner or a recovered table.
2. Then sections such as Identification, Contents, and **Acquisition**.
3. Acquisition mechanics go **only** in the Acquisition section and the
   manifest. That covers read counts ("two matching reads"), reader and
   profile names, voltages and command lines. They don't go in the opening
   paragraph or in the root README.
4. Keep uncertainty statements precise and say them once. Name what is not
   established; don't repeat general disclaimers in every paragraph.

The root README lists each set under a category with one line about what the
firmware is. A device folder with several subfolders gets a short index README
with a table of its subfolders.

## manifest.json

There is no strict schema yet, but `tools/check.py` relies on these rules:

- Every hash of a preserved file is a `"sha256"` key in an object that names
  the file with `"file"` (preferred), `"filename"` or `"image"`, relative to
  the manifest. A single-image manifest may leave the name out.
- Hashes of things outside the repository sit next to a `"url"` or `"session"`
  key, or under a key containing `reader`, `public`, `comparison` or
  `reference`. Examples are public reference ROMs, reader binaries and
  captures kept in local sessions.
- Record the date, the source device and board position, the chip marking
  as reported, and the session identifier.

## Checksums and paths

- `SHA256SUMS` covers dumps, evidence and manifests. **Don't include
  `README.md`**, because README edits would then break verification.
- Write session locations relative to the workspace (`dosravi/sessions/<name>`,
  `rom-programmers/sessions/<name>`), never as `/home/<user>/…` or
  `/Users/<user>/…`. Raw logs under `evidence/` are kept byte-for-byte and are
  exempt.
- Owner photos that aren't committed are referenced by file name only.

## What not to commit

From the root README: exact matches of firmware already in public collections
(including after padding or layout conversion) and all-FF captures stay in
local sessions. Unverified captures can be recorded in a manifest without
their binaries, as in `unknown/beckman-du7-hs-20261107/`.
