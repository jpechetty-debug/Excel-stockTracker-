import os
import win32com.client
import time

file_path = os.path.abspath("../IOS_Master_Tracker_Filled_13.xlsx")

try:
    print("Opening Excel...")
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    
    wb = excel.Workbooks.Open(file_path)
    
    print("Refreshing data connections and pivot tables...")
    wb.RefreshAll()
    
    # Need to wait briefly for async refreshes to complete
    excel.CalculateUntilAsyncQueriesDone()
    
    print("Calculating formulas...")
    excel.CalculateFull()
    
    print("Saving workbook...")
    wb.Save()
    wb.Close(SaveChanges=True)
    excel.Quit()
    print("Dashboard refreshed and saved successfully.")
except Exception as e:
    print(f"Error: {e}")
    try:
        excel.Quit()
    except:
        pass
