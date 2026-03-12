import csv
from io import StringIO

def create_csv_holder(operatedrows, headers):
    """Create a CSV holder for the results"""
    csv_holder = StringIO()
    writer = csv.DictWriter(csv_holder, fieldnames=headers)
    writer.writeheader()
    for row in operatedrows:
        writer.writerow(row)
    csv_holder.seek(0)  # Reset pointer to the beginning
    return csv_holder.getvalue()