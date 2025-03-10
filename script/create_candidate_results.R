library(tidyverse)
conflicts_prefer(dplyr::filter)

# get from commandline, because we can.
DATA_DIR <- commandArgs(trailingOnly = TRUE)[1]
DATA_DIR <- "data/clean/PS2023"

result_files <- dir(
    DATA_DIR,
    pattern = ".*per candidate.csv$",
    full.names = TRUE,
    recursive = TRUE
)

results <- result_files |>
    map(~ vroom::vroom(.x, show_col_types = FALSE, progress = FALSE),
        .progress = TRUE
    ) |>
    list_rbind() |>
    filter(station_id == "TOTAL") |>
    select(-starts_with("station_")) |>
    summarize(votes = sum(votes), .by = c(election_id, party_id, candidate_identifier))

candidate_files <- dir(
    DATA_DIR,
    pattern = "candidates.csv$",
    full.names = TRUE,
    recursive = TRUE
)

candidates <- candidate_files |>
    map(~ vroom::vroom(.x, show_col_types = FALSE, progress = FALSE),
        .progress = TRUE
    ) |>
    list_rbind()

elected_files <- dir(
    DATA_DIR,
    pattern = "elected.csv$",
    full.names = TRUE,
    recursive = TRUE
)

elected <- elected_files |>
    map(~ vroom::vroom(.x, show_col_types = FALSE, progress = FALSE),
        .progress = TRUE
    ) |>
    list_rbind() |>
    mutate(elected = TRUE)

candidate_results <- candidates |>
    left_join(results, by = join_by(election_id, party_id, candidate_identifier)) |>
    left_join(elected, by = join_by(election_id == ElectionIdentifier, party_id == AffiliationIdentifier, candidate_identifier == CandidateIdentifier)) |>
    mutate(elected = replace_na(elected, FALSE))


# check if we're missing anything!
anti_join(candidates, results, by = join_by(election_id, party_id, candidate_identifier))
anti_join(results, candidates, by = join_by(election_id, party_id, candidate_identifier))
anti_join(elected, candidates, by = join_by(ElectionIdentifier == election_id, AffiliationIdentifier == party_id, CandidateIdentifier == candidate_identifier))

# elected only contains the elected candidates, so we can't check for missing candidates there.
# anti_join(candidates, elected, by = join_by(election_id == ElectionIdentifier, party_id == AffiliationIdentifier, candidate_identifier == CandidateIdentifier))

write_csv(candidate_results, file.path(DATA_DIR, "candidate_results_PS2023.csv"))
