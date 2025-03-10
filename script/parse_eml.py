from pathlib import Path
import datetime as dt
import sys
import xmltodict
import pandas as pd

# updated handling of candidate lists
import xml.etree.ElementTree as ET


def read_eml(path: Path):
    """Convert EML file to dictionary"""

    try:
        return xmltodict.parse(path.read_text(encoding="utf-8"))

    except UnicodeDecodeError as e:
        print(path.name)
        print(e)
        return None


def get_id_and_date():
    """Get identifier and date of election"""

    paths = SOURCE.glob("**/Verkiezingsdefinitie*.xml")
    for path in paths:

        data = read_eml(path)
        election = data["EML"]["ElectionEvent"]["Election"]
        identifier = election["ElectionIdentifier"]["@Id"]
        date = election["ElectionIdentifier"]["kr:ElectionDate"]
        return (identifier, date)


def parse_election_data(data):
    """Parse election data and store results per station as CSV"""

    if pd.isnull(data):
        return []

    rows_aggregates = []
    rows_per_candidate = []
    rows_turnout = []
    rows_elected = []

    contest = data["EML"]["Count"]["Election"]["Contests"]["Contest"]
    election_id = data["EML"]["Count"]["Election"]["ElectionIdentifier"]["@Id"]

    try:
        contest_name = data["EML"]["Count"]["Election"]["ElectionIdentifier"][
            "ElectionName"
        ]
    except KeyError:
        contest_name = None

    try:
        if not contest_name:
            contest_name = contest["ContestIdentifier"]["ContestName"]
    except KeyError:
        contest_name = None

    try:
        managing_authority = data["EML"]["ManagingAuthority"]["AuthorityIdentifier"][
            "#text"
        ]
    except KeyError:
        managing_authority = None

    # base row template
    item = {
        "contest_name": contest_name,
        "managing_authority": managing_authority,
        "election_id": election_id,
    }

    # total row template
    total_item = item.copy()
    total_item["station_id"] = "TOTAL"
    total_item["station_name"] = "TOTAL"

    # extract top level totals
    total = contest["TotalVotes"]
    try:
        results = total["Selection"]
    except TypeError:
        results = []

    # party votes
    row_aggregate = total_item.copy()
    for result in results:
        if "AffiliationIdentifier" in result.keys():
            party_name = result["AffiliationIdentifier"]["RegisteredName"]
            party_id = result["AffiliationIdentifier"]["@Id"]
            if pd.isnull(party_name):
                party_name = party_id
            votes = int(result["ValidVotes"])
            row_aggregate[party_name] = votes

        # candidate votes
        elif PER_CANDIDATE.lower() in ["y", "yes"]:
            row_cand = total_item.copy()
            row_cand["party_name"] = party_name
            row_cand["party_id"] = party_id
            candidate_id = result["Candidate"]["CandidateIdentifier"]["@Id"]
            row_cand["candidate_identifier"] = candidate_id
            row_cand["votes"] = result["ValidVotes"]
            rows_per_candidate.append(row_cand)

    rows_aggregates.append(row_aggregate)

    # turnout, counted, rejected, invalid votes
    if TURNOUT.lower() in ["y", "yes"]:
        turnout_row = total_item.copy()

        try:
            turnout_row["cast"] = int(total["Cast"])
            turnout_row["counted"] = int(total["TotalCounted"])

            try:
                for rejected in total["RejectedVotes"]:
                    turnout_row["rejected: " + rejected["@ReasonCode"]] = int(
                        rejected["#text"]
                    )
            except KeyError:
                pass

            try:
                for uncounted in total["UncountedVotes"]:
                    turnout_row["uncounted: " + uncounted["@ReasonCode"]] = int(
                        uncounted["#text"]
                    )
            except KeyError:
                pass

            rows_turnout.append(turnout_row)

        except TypeError:
            pass

    # start per station votes
    try:
        stations = contest["ReportingUnitVotes"]
    except KeyError:
        stations = []
        rows_aggregates = [
            {
                "contest_name": contest_name,
                "managing_authority": managing_authority,
                "station_name": None,
                "station_id": None,
            }
        ]

    for station in stations:
        row_item = item.copy()

        try:
            row_item["station_id"] = station["ReportingUnitIdentifier"]["@Id"]
        except TypeError:
            row_item["station_id"] = None

        try:
            row_item["station_name"] = station["ReportingUnitIdentifier"]["#text"]
        except TypeError:
            row_item["station_name"] = None

        try:
            results = station["Selection"]
        except TypeError:
            results = []

        row_aggregate = row_item.copy()
        for result in results:

            if "AffiliationIdentifier" in result.keys():
                party_name = result["AffiliationIdentifier"]["RegisteredName"]
                party_id = result["AffiliationIdentifier"]["@Id"]
                if pd.isnull(party_name):
                    party_name = party_id
                votes = int(result["ValidVotes"])
                row_aggregate[party_name] = votes

            elif PER_CANDIDATE.lower() in ["y", "yes"]:
                row_cand = item.copy()
                row_cand["party_name"] = party_name
                row_cand["party_id"] = party_id
                candidate_id = result["Candidate"]["CandidateIdentifier"]["@Id"]
                row_cand["candidate_identifier"] = candidate_id
                row_cand["votes"] = result["ValidVotes"]
                rows_per_candidate.append(row_cand)

        rows_aggregates.append(row_aggregate)

        if TURNOUT.lower() in ["y", "yes"]:
            turnout_row = row_item.copy()

            try:
                turnout_row["cast"] = int(station["Cast"])
                turnout_row["counted"] = int(station["TotalCounted"])

                try:
                    for rejected in station["RejectedVotes"]:
                        turnout_row["rejected: " + rejected["@ReasonCode"]] = int(
                            rejected["#text"]
                        )
                except KeyError:
                    pass

                try:
                    for uncounted in station["UncountedVotes"]:
                        turnout_row["uncounted: " + uncounted["@ReasonCode"]] = int(
                            uncounted["#text"]
                        )
                except KeyError:
                    pass

                rows_turnout.append(turnout_row)

            except TypeError:
                pass

    return (
        rows_aggregates,
        rows_per_candidate,
        rows_turnout,
        contest_name,
        managing_authority,
    )


def process_files():
    """Process data files with local election results"""

    identifier, date = get_id_and_date()

    paths = SOURCE.glob("**/Telling*_*.xml")
    paths = [p for p in paths if "kieskring" not in str(p).lower()]
    print("Processing data files...")
    for index, path in enumerate(paths):
        print(f"\r[{index + 1}/{len(paths)}]: {path}\t\t", end=None)

        name = path.name.split(".")[0]

        data = read_eml(path)
        (
            rows_aggregates,
            rows_per_candidate,
            rows_turnout,
            contest_name,
            managing_authority,
        ) = parse_election_data(data)

        if PER_CANDIDATE.lower() in ["y", "yes"]:
            filename = "{} per candidate.csv".format(name)
            df = pd.DataFrame(rows_per_candidate)
            df.to_csv(str(VOTE_COUNTS / filename), index=False, encoding="utf-8")

        if TURNOUT.lower() in ["y", "yes"]:
            filename = "{} turnout.csv".format(name)
            df = pd.DataFrame(rows_turnout)
            df.to_csv(str(VOTE_COUNTS / filename), index=False, encoding="utf-8")

        filename = "{} aggregate.csv".format(name)
        df = pd.DataFrame(rows_aggregates)
        first_cols = [
            "contest_name",
            "managing_authority",
            "station_name",
            "station_id",
        ]
        columns = first_cols + [c for c in df.columns if c not in first_cols]
        df = df[columns]
        df.to_csv(str(VOTE_COUNTS / filename), index=False, encoding="utf-8")


def extract_elected_candidates(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    ns = {
        "": "urn:oasis:names:tc:evs:schema:eml",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
        "kr": "http://www.kiesraad.nl/extensions",
        "xal": "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0",
        "xnl": "urn:oasis:names:tc:ciq:xsdschema:xNL:2.0",
    }

    election_identifier = root.find(".//ElectionIdentifier", ns).attrib["Id"]

    results = []
    current_affiliation = None

    for selection in root.findall(".//Selection", ns):
        affiliation = selection.find("AffiliationIdentifier", ns)
        if affiliation is not None:
            current_affiliation = affiliation.attrib["Id"]

        candidate = selection.find("Candidate", ns)
        if candidate is not None:
            candidate_id = candidate.find("CandidateIdentifier", ns).attrib["Id"]
            candidate_name_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:FirstName", ns
            )
            candidate_surname_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:LastName", ns
            )
            candidate_initials_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:NameLine[@NameType='Initials']",
                ns,
            )
            candidate_prefix_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:NamePrefix", ns
            )

            candidate_name = (
                candidate_name_element.text
                if candidate_name_element is not None
                else ""
            )
            candidate_surname = (
                candidate_surname_element.text
                if candidate_surname_element is not None
                else ""
            )
            candidate_initials = (
                candidate_initials_element.text
                if candidate_initials_element is not None
                else ""
            )
            candidate_prefix = (
                candidate_prefix_element.text
                if candidate_prefix_element is not None
                else ""
            )

            results.append(
                {
                    "ElectionIdentifier": election_identifier,
                    "AffiliationIdentifier": current_affiliation,
                    "CandidateIdentifier": candidate_id,
                    "Initials": candidate_initials,
                    "FirstName": candidate_name,
                    "Prefix": candidate_prefix,
                    "LastName": candidate_surname,
                }
            )

    return results


def extract_candidate_info(xml_file_path):
    # Define the namespaces
    namespaces = {
        "": "urn:oasis:names:tc:evs:schema:eml",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
        "kr": "http://www.kiesraad.nl/extensions",
        "xal": "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0",
        "xnl": "urn:oasis:names:tc:ciq:xsdschema:xNL:2.0",
    }

    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    candidate_info_list = []

    managing_authority_element = root.find(
        ".//ManagingAuthority/AuthorityIdentifier", namespaces
    )
    managing_authority = (
        managing_authority_element.text
        if managing_authority_element is not None
        else ""
    )

    election_element = root.find(".//Election/ElectionIdentifier", namespaces)
    election_id = election_element.get("Id")
    election_date = election_element.find("kr:ElectionDate", namespaces).text
    election_domain = election_element.find("kr:ElectionDomain", namespaces).text

    # Extract the required information
    for affiliation in root.findall(".//Affiliation", namespaces):
        affiliation_id = affiliation.find("AffiliationIdentifier", namespaces).get("Id")
        affiliation_name_element = affiliation.find(
            "AffiliationIdentifier/RegisteredName", namespaces
        )
        affiliation_name = (
            affiliation_name_element.text
            if affiliation_name_element is not None
            else "N/A"
        )

        for candidate in affiliation.findall("Candidate", namespaces):
            candidate_id = candidate.find("CandidateIdentifier", namespaces).get("Id")
            first_name_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:FirstName", namespaces
            )
            name_prefix_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:NamePrefix", namespaces
            )
            last_name_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:LastName", namespaces
            )
            initials_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:NameLine[@NameType='Initials']",
                namespaces,
            )
            first_name = (
                first_name_element.text if first_name_element is not None else ""
            )
            name_prefix = (
                name_prefix_element.text if name_prefix_element is not None else ""
            )
            last_name = last_name_element.text if last_name_element is not None else ""
            initials = initials_element.text if initials_element is not None else ""

            gender_element = candidate.find("Gender", namespaces)
            gender = gender_element.text if gender_element is not None else ""

            locality_element = candidate.find(
                "QualifyingAddress/xal:Locality/xal:LocalityName", namespaces
            )
            locality = locality_element.text if locality_element is not None else ""

            candidate_info_list.append(
                {
                    "election_id": election_id,
                    "election_domain": election_domain,
                    "election_date": election_date,
                    "managing_authority": managing_authority,
                    "party_name": affiliation_name,
                    "party_id": affiliation_id,
                    "candidate_identifier": candidate_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "initials": initials,
                    "prefix": name_prefix,
                    "gender": gender,
                    "locality": locality,
                }
            )

    return candidate_info_list


def create_candidate_list():
    """Create list with candidate details"""

    candidates = []
    elected = []

    paths = list(SOURCE.glob("**/Kandidatenlijsten_*.xml"))
    print("Processing candidate lists...")
    for index, path in enumerate(paths):
        print(f"\r[{index + 1}/{len(paths)}]: {path}\t\t", end=None)
        candidates.extend(extract_candidate_info(path))
    print("Done!")

    paths = list(SOURCE.glob("**/Resultaat_*.xml"))
    print("Processing elected candidates...")
    for index, path in enumerate(paths):
        print(f"\r[{index + 1}/{len(paths)}]: {path}\t\t", end=None)
        elected.extend(extract_elected_candidates(path))
    print("Done!")

    print("\nWriting candidate lists to csv...")
    df = pd.DataFrame(candidates)
    path = TARGET / "candidates.csv"
    df.to_csv(str(path), index=False, encoding="utf-8")

    print("Writing elected candidates to csv...")
    df = pd.DataFrame(elected)
    path = TARGET / "elected.csv"
    df.to_csv(str(path), index=False, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        SOURCE = Path(sys.argv[1])
        TARGET = Path(sys.argv[2])
    else:
        SOURCE = Path(input("Path to eml data files folder: "))
        TARGET = Path(input("Path to output folder: "))

    CONFIRM = input(
        f"Reading data files from {SOURCE.resolve()}, and storing processed .csv files in {TARGET.resolve()}.\n\nIs this correct? (y/N)"
    )
    if not CONFIRM in ["yes", "y"]:
        print("Ok, bye!")
        exit()

    VOTE_COUNTS = TARGET / "vote_counts"
    VOTE_COUNTS.mkdir(exist_ok=True, parents=True)

    print("\nDo you also want to create a csv with results per candidate?")
    print("This will take up more disk space (~1GB)\n")
    PER_CANDIDATE = input("Per candidate (y/n): ")

    print(
        "\nDo you also want to create a csv with turnout, uncounted, and rejected votes?"
    )
    print("This will take up more disk space (~100MB)\n")
    TURNOUT = input("Turnout (y/n): ")

    start = dt.datetime.now()

    if PER_CANDIDATE in ["yes", "y"]:
        create_candidate_list()

    process_files()

    duration = dt.datetime.now() - start
    print("Duration: {} seconds".format(round(duration.total_seconds())))
