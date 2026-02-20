# 🔐 Authentication System Guide

Sistem authentication dengan role-based access control (RBAC) yang offline-first.

## Overview

- ✅ **Offline-First**: Token disimpan di localStorage browser
- ✅ **Role-Based**: 3 role berbeda (Siswa, Guru, Admin)
- ✅ **Secure**: Password hashing dengan SHA256
- ✅ **Simple**: Demo credentials untuk testing

## Demo Credentials

### Siswa
- Username: `siswa`
- Password: `siswa123`

### Guru
- Username: `guru`
- Password: `guru123`

### Admin
- Username: `admin`
- Password: `admin123`

## Architecture

```
Landing Page → Login Modal → Role-based Dashboard
```

Token disimpan di localStorage dan divalidasi di setiap request.

Lihat [WEB_UI_ARCHITECTURE.md](../WEB_UI_ARCHITECTURE.md) untuk detail teknis.
