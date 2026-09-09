import openpyxl
import sys

def main():
    wb = openpyxl.load_workbook('example/Register to participate UII Sandbox 2026_ Empowering Glocal Citizens(1-3).xlsx')
    ws = wb.active
    headers = [str(cell.value) for cell in ws[1]]
    
    with open('headers.txt', 'w', encoding='utf-8') as f:
        for i, header in enumerate(headers):
            f.write(f"Column {i+1}: {header}\n")

if __name__ == '__main__':
    main()
