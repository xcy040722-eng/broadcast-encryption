# Draft upstream issue — gmssl-python 2.2.2 ctypes ABI mismatch with recent GmSSL

> Draft only. Do not submit without reviewing the exact upstream repository state and removing project-specific wording.

## Suggested title

`gmssl-python 2.2.2: Sm2Key and Sm4Gcm ctypes layouts can under-allocate against recent native GmSSL`

## Environment

```text
OS:            Windows 11 / WSL2 / Ubuntu 24.04.4 LTS
Python:        3.12.3
GmSSL native:  3.3.0-dev.1183, commit 24ae4827
GmSSL-Python:  2.2.2
Architecture:  x86_64
```

## Summary

With `gmssl-python==2.2.2` and the native GmSSL commit above, SM2 and SM4-GCM operations can appear to succeed but the Python process later terminates with `Segmentation fault (core dumped)`.

The issue is reproducible as a ctypes ABI size mismatch: Python allocates smaller `Structure` objects than native GmSSL expects, then native functions receive `byref(self)` and can write past the Python object.

## Observed sizes

| structure | ctypes | native C `sizeof` |
|---|---:|---:|
| Sm2Point / Sm3 / Sm4 / Sm4Ctr / Ghash | matched | matched |
| `Sm2Key` | **96** | **128** |
| `Sm4Gcm` | **288** | **296** |

For the tested native headers:

- `SM4_GCM_CTX` includes a trailing `uint64_t encedlen`;
- `SM2_KEY.public_key` uses a 96-byte `SM2_Z256_POINT`, while the Python binding used a 64-byte affine `Sm2Point` in this environment.

## Failure behavior

A minimal process can print successful results for SM3, SM2 and SM4-GCM and then crash only after the final operation/process teardown:

```text
gmssl-python   : 2.2.2
GmSSL native   : GmSSL 3.3.0-dev.1183
ctypes Sm4Gcm  : 288 bytes
step1 rand_bytes ... ok
...
step5 Sm4Gcm decrypt ... ok
ALL STEPS PASSED
Segmentation fault (core dumped)
```

The delayed crash location is nondeterministic because the overwrite corrupts heap/object state earlier and may be detected on a later allocation/free.

## Local compatibility fix that removes the crash

Equivalent layout changes:

```diff
 class Sm4Gcm(Structure):
     _fields_ = [
         ...,
         ("maclen", c_size_t),
+        ("encedlen", c_uint64),
     ]

+class Sm2Z256Point(Structure):
+    _fields_ = [
+        ("X", c_uint64 * 4),
+        ("Y", c_uint64 * 4),
+        ("Z", c_uint64 * 4),
+    ]
+
 class Sm2Key(Structure):
-    _fields_ = [("public_key", Sm2Point), ("private_key", c_uint8 * 32)]
+    _fields_ = [("public_key", Sm2Z256Point), ("private_key", c_uint8 * 32)]
```

After the layout changes:

```text
sizeof(Sm2Key) = 128
sizeof(Sm4Gcm) = 296
```

and repeated real SM2 encrypt/decrypt plus SM4-GCM file round trips exit cleanly.

## Additional observation

`Sm2Signature` also appeared to have a native/ctypes layout discrepancy in the same environment.  It was not needed for the reproducer above and should be audited separately rather than inferred from these two fixes.

## Requested upstream action

Please consider:

1. auditing ctypes structure definitions against the current public GmSSL headers;
2. adding CI that compares/validates structure sizes for the supported native GmSSL version(s);
3. documenting a supported native-GmSSL ↔ GmSSL-Python compatibility matrix or pin;
4. ensuring package/release combinations cannot silently expose undersized structures to native `byref()` calls.

## Reproducer material to attach before submitting

Before filing upstream, attach or inline:

- minimal Python reproducer;
- tiny C program printing `sizeof(SM2_KEY)` and `sizeof(SM4_GCM_CTX)`;
- exact `git rev-parse HEAD` for native GmSSL;
- `pip show gmssl-python` output;
- patched and unpatched process exit codes.
