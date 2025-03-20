from pathlib import Path
import pandas as pd

# updated handling of candidate lists
import xml.etree.ElementTree as ET


def extract_elected_candidates(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    namespaces = {
        "": "urn:oasis:names:tc:evs:schema:eml",
        "ds": "http://www.w3.org/2000/09/xmldsig#",
        "kr": "http://www.kiesraad.nl/extensions",
        "xal": "urn:oasis:names:tc:ciq:xsdschema:xAL:2.0",
        "xnl": "urn:oasis:names:tc:ciq:xsdschema:xNL:2.0",
    }

    # get metadata
    (
        managing_authority,
        managing_authority_id,
        election_id,
        election_date,
        election_domain,
        contest_id,
        contest_name,
    ) = extract_metadata(namespaces, root)

    results = []
    current_affiliation = None

    for selection in root.findall(".//Selection", namespaces):
        affiliation = selection.find("AffiliationIdentifier", namespaces)
        if affiliation is not None:
            current_affiliation = affiliation.attrib["Id"]

        candidate = selection.find("Candidate", namespaces)
        if candidate is not None:
            candidate_id = candidate.find("CandidateIdentifier", namespaces).attrib[
                "Id"
            ]
            candidate_name_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:FirstName", namespaces
            )
            candidate_surname_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:LastName", namespaces
            )
            candidate_initials_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:NameLine[@NameType='Initials']",
                namespaces,
            )
            candidate_prefix_element = candidate.find(
                "CandidateFullName/xnl:PersonName/xnl:NamePrefix", namespaces
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
                    "managing_authority": managing_authority,
                    "managing_authority_id": managing_authority_id,
                    "election_id": election_id,
                    "election_domain": election_domain,
                    "election_date": election_date,
                    "contest_id": contest_id,
                    "contest_name": contest_name,
                    "party_id": current_affiliation,
                    "candidate_id": candidate_id,
                    "initials": candidate_initials,
                    "first_name": candidate_name,
                    "prefix": candidate_prefix,
                    "last_name": candidate_surname,
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

    (
        managing_authority,
        managing_authority_id,
        election_id,
        election_date,
        election_domain,
        contest_id,
        contest_name,
    ) = extract_metadata(namespaces, root)

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
                    "managing_authority_id": managing_authority_id,
                    "contest_id": contest_id,
                    "contest_name": contest_name,
                    "party_name": affiliation_name,
                    "party_id": affiliation_id,
                    "candidate_id": candidate_id,
                    "initials": initials,
                    "first_name": first_name,
                    "prefix": name_prefix,
                    "last_name": last_name,
                    "gender": gender,
                    "locality": locality,
                }
            )

    return candidate_info_list


def extract_metadata(namespaces, root):
    managing_authority_element = root.find(
        ".//ManagingAuthority/AuthorityIdentifier", namespaces
    )
    managing_authority = (
        managing_authority_element.text
        if managing_authority_element is not None
        else ""
    )
    managing_authority_id = (
        managing_authority_element.get("Id")
        if managing_authority_element is not None
        else ""
    )

    contest_element = root.find(".//Contest", namespaces)
    contest_id = (
        contest_element.find("ContestIdentifier", namespaces).get("Id")
        if contest_element is not None
        else ""
    )
    contest_name_element = contest_element.find(
        "ContestIdentifier/ContestName", namespaces
    )
    contest_name = contest_name_element.text if contest_name_element is not None else ""

    election_element = root.find(".//Election/ElectionIdentifier", namespaces)
    election_id = election_element.get("Id")
    election_date = election_element.find("kr:ElectionDate", namespaces).text
    election_domain = election_element.find("kr:ElectionDomain", namespaces).text
    return (
        managing_authority,
        managing_authority_id,
        election_id,
        election_date,
        election_domain,
        contest_id,
        contest_name,
    )


def extract_votes(xml_file_path):
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

    # Extract metadata
    (
        managing_authority,
        managing_authority_id,
        election_id,
        election_date,
        election_domain,
        contest_id,
        contest_name,
    ) = extract_metadata(namespaces, root)

    candidate_votes = []

    # reporting unit values for non-total vote lines
    reporting_unit_name = "TOTAL"
    reporting_unit_id = "TOTAL"

    def __parse_candidate_list(sub_root):
        affiliation_id = None
        registered_name = None

        # Iterate through all Selection elements
        for selection in sub_root.findall(".//Selection", namespaces):
            # Extract AffiliationIdentifier and RegisteredName
            affiliation_id_element = selection.find("AffiliationIdentifier", namespaces)
            if affiliation_id_element is not None:
                affiliation_id = affiliation_id_element.get("Id")
                registered_name_element = selection.find(
                    "AffiliationIdentifier/RegisteredName", namespaces
                )
                registered_name = (
                    registered_name_element.text
                    if registered_name_element is not None
                    else None
                )

            # Extract CandidateIdentifier
            candidate_id_element = selection.find(
                "Candidate/CandidateIdentifier", namespaces
            )
            candidate_id = (
                candidate_id_element.get("Id")
                if candidate_id_element is not None
                else None
            )

            candidate_short_code = (
                candidate_id_element.get("ShortCode")
                if candidate_id_element is not None
                else None
            )

            # Extract ValidVotes
            valid_votes_element = selection.find("ValidVotes", namespaces)
            valid_votes = (
                int(valid_votes_element.text)
                if valid_votes_element is not None
                else None
            )

            # Append the extracted data to the list
            candidate_votes.append(
                {
                    "managing_authority": managing_authority,
                    "managing_authority_id": managing_authority_id,
                    "election_id": election_id,
                    "election_domain": election_domain,
                    "election_date": election_date,
                    "contest_id": contest_id,
                    "contest_name": contest_name,
                    "reporting_unit_name": reporting_unit_name,
                    "reporting_unit_id": reporting_unit_id,
                    "party_id": affiliation_id,
                    "party_name": registered_name,
                    "candidate_id": candidate_id,
                    "candidate_shortcode": candidate_short_code,
                    "valid_votes": valid_votes,
                }
            )

    # total votes
    total_votes_element = root.find(".//TotalVotes", namespaces)
    if total_votes_element is not None:
        __parse_candidate_list(total_votes_element)

    # per reporting unit
    for reporting_unit in root.findall(".//ReportingUnitVotes", namespaces):
        reporting_unit_element = reporting_unit.find(
            "ReportingUnitIdentifier", namespaces
        )
        reporting_unit_name = reporting_unit_element.text
        reporting_unit_id = reporting_unit_element.get("Id")
        __parse_candidate_list(reporting_unit)

    return candidate_votes


def create_candidate_list(source_dir: Path, target_dir: Path):
    """Create list with candidate details"""

    candidates = []
    elected = []
    votes = []

    paths = list(source_dir.glob("**/Kandidatenlijsten_*.xml"))
    print("Processing candidate lists...")
    for index, path in enumerate(paths):
        print(f"\r[{index + 1}/{len(paths)}]: {path}\t\t", end=None)
        candidates.extend(extract_candidate_info(path))
    print("Done!")

    paths = list(source_dir.glob("**/Resultaat_*.xml"))
    print("Processing elected candidates...")
    for index, path in enumerate(paths):
        print(f"\r[{index + 1}/{len(paths)}]: {path}\t\t", end=None)
        elected.extend(extract_elected_candidates(path))
    print("Done!")

    paths = list(source_dir.glob("**/Totaaltelling_*.xml"))
    print("Processing total vote counts...")
    for index, path in enumerate(paths):
        print(f"\r[{index + 1}/{len(paths)}]: {path}\t\t", end=None)
        votes.extend(extract_votes(path))
    print("Done!")

    print("\nWriting candidate lists to csv...")
    df = pd.DataFrame(candidates)
    path = target_dir / "candidates.csv"
    df.to_csv(str(path), index=False, encoding="utf-8")

    print("Writing elected candidates to csv...")
    df = pd.DataFrame(elected)
    path = target_dir / "elected.csv"
    df.to_csv(str(path), index=False, encoding="utf-8")

    print("Writing total votes to csv...")
    df = pd.DataFrame(votes)
    path = target_dir / "votes.csv"
    df.to_csv(str(path), index=False, encoding="utf-8")

    print("Done!")
