import sap_client

def normalize(loc):
    if loc is None:
        return None
    return str(loc).strip().lower()

def synchronize(ibase_df, work_report_df):
    ibase_lookup = ibase_df.set_index("ObjectID")

    matches = 0
    discrepancies = 0
    missing_in_ibase = 0
    errors = 0

    audit_records = []

    work_report_df = work_report_df.sort_values(
        "lastChangeDateTime",
        ascending=False
    )

    work_report_df = work_report_df.dropna(
        subset=["equipmentId"]
    )

    work_report_df = work_report_df.drop_duplicates(
        "equipmentId"
    )

    for _, work_report in work_report_df.iterrows():
        equipment_id = work_report["equipmentId"]
        if equipment_id not in ibase_lookup.index:
            missing_in_ibase += 1
            audit_records.append({
                "equipment_id": equipment_id,
                "location_sap": work_report.get("location"),
                "location_ibase": None,
                "result": "MISSING_IN_IBASE"
            })
            continue

        ibase_location = ibase_lookup.loc[
            equipment_id,
            "AddressLine1"
        ]
        sap_location = work_report["location"]

        normalized_sap = normalize(sap_location)
        normalized_ibase = normalize(ibase_location)

        if normalized_sap is None:
            errors += 1
            audit_records.append({
                "equipment_id": equipment_id,
                "location_sap": None,
                "location_ibase": ibase_location,
                "result": "ERROR",
                "error": "SAP location is missing"
            })
            continue

        if normalized_sap == normalized_ibase:
            matches += 1
            audit_records.append({
                "equipment_id": equipment_id,
                "location_sap": sap_location,
                "location_ibase": ibase_location,
                "result": "MATCH"
            })
            continue

        # Locations differ
        discrepancies += 1

        try:
            sap_client.update_ibase_location(
                equipment_id,
                sap_location
            )

            audit_records.append({
                "equipment_id": equipment_id,
                "location_sap": sap_location,
                "location_ibase": ibase_location,
                "result": "UPDATED"
            })
        except Exception as err:
            errors += 1

            audit_records.append({
                "equipment_id": equipment_id,
                "location_sap": sap_location,
                "location_ibase": ibase_location,
                "result": "UPDATE_ERROR",
                "error": str(err)
            })

    return {
        "processed": len(work_report_df),
        "matches": matches,
        "discrepancies": discrepancies,
        "missing_in_ibase": missing_in_ibase,
        "errors": errors,
        "audit_records": audit_records
    }