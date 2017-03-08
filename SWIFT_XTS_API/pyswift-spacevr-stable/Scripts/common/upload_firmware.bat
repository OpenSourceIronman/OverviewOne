@echo off

if [%1] == [] (
	if exist C:\Python27\python.exe (
		C:\Python27\python.exe %~dp0\upload_firmware.py
	) else if exist D:\Python27\python.exe (
		D:\Python27\python.exe %~dp0\upload_firmware.py
	) else if exist E:\Python27\python.exe (
		E:\Python27\python.exe %~dp0\upload_firmware.py
	) else if exist F:\Python27\python.exe (
		F:\Python27\python.exe %~dp0\upload_firmware.py
	)
) else (
	if exist C:\Python27\python.exe (
		C:\Python27\python.exe %~dp0\upload_firmware.py --release %1
	) else if exist D:\Python27\python.exe (
		D:\Python27\python.exe %~dp0\upload_firmware.py --release %1
	) else if exist D:\Python27\python.exe (
		E:\Python27\python.exe %~dp0\upload_firmware.py --release %1
	) else if exist D:\Python27\python.exe (
		F:\Python27\python.exe %~dp0\upload_firmware.py --release %1
	)
)

timeout /t 10
