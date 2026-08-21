import pandas as pd

def write_audit_report(records, filename="audit_report.csv"):
    df = pd.DataFrame(records)
    df.to_csv(filename, index=False)
    return filename