import sap_client
import synchronization
import audit

def main():

    print("Starting equipment synchronization...\n")
    client = sap_client.SAPClient()

    print("Pulling iBase records from SAP...")
    ibase_df = client.get_ibase_records()
    print(f"Pulled {len(ibase_df)} iBase records.\n")

    print("Pulling work reports from SAP...")
    work_report_df = client.get_work_reports()
    print(f"Pulled {len(work_report_df)} work reports.\n")

    print("Synchronizing equipment locations...\n")
    results = synchronization.synchronize(
        ibase_df,
        work_report_df,
        client
    )

    audit.write_audit_report(results["audit_records"])
    # Display results
    print("Synchronization complete.\n")
    print(f"Records processed:  {results['processed']}")
    print(f"Matches:            {results['matches']}")
    print(f"Discrepancies:      {results['discrepancies']}")
    print(f"Missing in iBase:   {results['missing_in_ibase']}")
    print(f"Errors:             {results['errors']}")
    print("\nAudit report written to audit_report.csv")

if __name__ == "__main__":
    main()