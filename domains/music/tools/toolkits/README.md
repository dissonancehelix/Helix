# system/vendor

Third-party SDKs, cloned libraries, and source mirrors live here when Helix needs local reference code.

Vendor code is optional/local provenance. It is not design authority, and tools should treat it as replaceable input unless a tool manifest says otherwise.

Large generated builds, nested `.git` folders, caches, and downloaded binaries should stay untracked.
