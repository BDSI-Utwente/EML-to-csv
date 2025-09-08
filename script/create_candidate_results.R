library(tidyverse)
conflicted::conflicts_prefer(dplyr::filter)

path <- "data/clean/PS2023_8-9-2025"

combine_candidate_data <- function(path) {
    # note that for the 2023 data, contest_name is NA in provinces with a single district,
    # and the province name (election_domain) before that. We'll fill in NA's with
    # election_domain to try and standardize
    candidates <- vroom::vroom(file.path(path, "candidates.csv"), show_col_types = FALSE, progress = FALSE) |>
        mutate(contest_name = coalesce(contest_name, election_domain))

    # note that votes are reported in total for the election domain (reporting_unit_id == "TOTAL"),
    # and per reporting_unit. In provinces with multiple electoral districts
    # (contest_id == "alle"), these units are the electoral districts. In
    # provinces with a single district (contest_id == "geen" for 2023,
    # contest_id == "1" for 2019, 2015), the units are councils. Furthermore, the
    # 2015 water board elections use specific contest_id's even though for these
    # elections there is always just a single electoral district per election domain.
    #
    # That leaves us with several problems:
    # - in provinces with multiple districts, there is no direct match between
    #   districts in the candidate data (contest_name, contest_id),
    #   and districts in the votes data (reporting_unit_id, reporting_unit_name).
    #   That said, it looks like we can derive the link from patterns in the names
    #   as both names include the name of the electoral district. E.g.,
    #   contest_name: "'s-Gravenhage" <-> reporting_unit_name: "Kieskring 's-Gavenhage".
    # - in provinces with a single district, we'll want to aggregate vote counts
    #   (or use the total reporting units).
    # - water board elections (election_id == "AB....") always have a single district.
    #
    # In addition, we'll have to add the contest name for single-district vote
    # data if it wasn't specified to match candidate data.
    votes <- vroom::vroom(file.path(path, "votes.csv"), show_col_types = FALSE, progress = FALSE) |>
        # party totals are listed as NA candidate_id
        filter(reporting_unit_id != "TOTAL", !is.na(candidate_id))
    .votes_single_districts <- votes |>
        # WS2015 uses different contest_id's for each kieskring - but all AB elections
        # are single district elections anyway, so just filter for that
        filter(contest_id %in% c("geen", "1") | str_starts(election_id, "AB")) |>
        summarize(valid_votes = sum(valid_votes), .by = c(election_id, party_id, candidate_id, election_domain, contest_name)) |>
        mutate(contest_name = coalesce(contest_name, election_domain)) |>
        select(-election_domain)
    .votes_multiple_districts <- votes |>
        # exclude all AB elections
        filter(contest_id == "alle", !str_starts(election_id, "AB")) |>
        select(election_id, reporting_unit_name, party_id, candidate_id, valid_votes) |>
        # derive contest name from reporting_unit_name
        mutate(contest_name = stringr::str_remove(reporting_unit_name, "Kieskring ") |> stringr::str_trim())
    .votes_per_district <- bind_rows(.votes_single_districts, .votes_multiple_districts)

    # we can now join votes onto candidates one-to-one
    candidates_with_votes <- candidates |> left_join(.votes_per_district, by = join_by(election_id, contest_name, party_id, candidate_id))

    # check our work
    candidates_without_votes <- candidates_with_votes |> filter(is.na(valid_votes))
    if (nrow(candidates_without_votes) > 0) {
        cat("Warning: missing vote data in", path, "\n")
        print(candidates_without_votes)
    }


    elected <- vroom::vroom(file.path(path, "elected.csv"), show_col_types = FALSE, progress = FALSE) |>
        # candidate_id for elected candidates is not the same as the ids used in
        # the candidate list, so we might as well ignore it. Theoretically, we
        # should be able to match on either id or short_code depending on if the
        # province has a single or multiple districts, but we might as well match
        # on province, party, and candidate name and cross our fingers there are
        # no collisions.
        select(
            election_id, party_id,
            initials, first_name, prefix, last_name
        ) |>
        # mark all entries in this list as elected
        mutate(elected = TRUE)

    candidates_with_results <- candidates_with_votes |>
        left_join(elected, by = join_by(election_id, party_id, initials, first_name, prefix, last_name)) |>
        # anyone not explicitly marked as elected is not elected
        mutate(elected = replace_na(elected, FALSE))

    n_elected <- nrow(elected)
    candidates_elected <- candidates_with_results |>
        filter(elected) |>
        distinct(election_id, party_id, initials, first_name, prefix, last_name)
    n_elected_candidates <- nrow(candidates_elected)
    candidates_missing <- anti_join(elected, candidates_elected, by = join_by(election_id, party_id, initials, first_name, prefix, last_name))

    if (n_elected != n_elected_candidates) {
        # print warning with number of elected
        cat("Warning: number of elected candidates does not match number of candidates with votes in", path, ": ", n_elected, "vs.", n_elected_candidates, "\n")
    }

    if (nrow(candidates_missing) > 0) {
        cat("Warning: missing candidate data in", path, "\n")
        print(candidates_missing)
    }

    candidates_with_results
}

# # for each subfolder of data/clean, run combine_candidate_data, and store the results
# subdirs <- list.dirs("data/clean", FALSE)[-1]
# for (dir in subdirs) {
#     cat("Processing", dir, "...", "\n")
#     candidate_votes_per_election_domain <- combine_candidate_data(file.path("data", "clean", dir))

#     write_csv(candidate_votes_per_election_domain, file.path("data", "clean", dir, paste0(dir, "_combined.csv")))
# }
combine_candidate_data(path) |> write_csv("data/clean/PS2023_2025-09-08_combined.csv")
