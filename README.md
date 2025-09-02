# LotoJung - Lottery Number Management System

## Overview
LotoJung เป็นระบบจัดการหมายเลขล็อตเตอรี่ที่ออกแบบมาเพื่อการบริหารจัดการหมายเลขที่ถูกบล็อก และการสร้าง permutations อัตโนมัติ

## Features
- 🎯 **Auto-detection**: ตรวจจับประเภทหมายเลขอัตโนมัติจากความยาว (2หลัก/3หลัก)
- 🔄 **Permutation Generation**: สร้าง permutations ทั้งหมดอัตโนมัติ
- 🗂️ **Field Management**: จัดการตาม field types (2_top, 2_bottom, 3_top, tote)
- 🧹 **Bulk Operations**: เพิ่ม/ลบข้อมูลจำนวนมาก
- 🔒 **Admin Interface**: หน้าจัดการสำหรับผู้ดูแลระบบ

## System Requirements
- Python 3.8+
- Flask Framework
- SQLite Database
- Bootstrap 5 UI

## Quick Start
```bash
cd lotoryjung_app
python3 app.py
```
เข้าใช้งานที่: http://localhost:5002

## Documentation
- 📋 [System Design](docs/DESIGN.md) - ข้อมูลการออกแบบระบบ
- 🏗️ [Project Structure](docs/STRUCTURE.md) - โครงสร้างไฟล์และโฟลเดอร์
- ⚙️ [Installation Guide](docs/INSTALLATION.md) - คู่มือการติดตั้ง
- 📈 [Development Progress](docs/PROGRESS.md) - ความคืบหน้าการพัฒนา

## License
MIT License

---
*Last Updated: September 2, 2025*
