library(tidyverse)
conflicts_prefer(dplyr::filter)

path <- "data/clean/PS2019"

combine_candidate_data <- function(path) {
    candidates <- vroom::vroom(file.path(path, "candidates.csv"), show_col_types = FALSE, progress = FALSE)
    elected <- vroom::vroom(file.path(path, "elected.csv"), show_col_types = FALSE, progress = FALSE) |>
        dplyr::transmute(
            election_id,
            election_domain, contest_id, party_id,
            initials, first_name, prefix, last_name,
            candidate_id_elected = candidate_id, elected = TRUE
        )

    votes <- vroom::vroom(file.path(path, "votes.csv"), show_col_types = FALSE, progress = FALSE) |>
        filter(reporting_unit_name != "TOTAL", !is.na(candidate_id)) |>
        summarize(valid_votes = sum(valid_votes), .by = c(election_id, election_domain, contest_id, party_id, candidate_id))

    candidate_votes_per_election_domain <- candidates |>
        left_join(votes,
            by = join_by(election_id, election_domain, contest_id, party_id, candidate_id)
        ) |>
        left_join(elected,
            by = join_by(election_id, election_domain, party_id, initials, first_name, prefix, last_name)
        ) |>
        mutate(elected = replace_na(elected, FALSE))
    
    
    n_elected = nrow(elected)
    candidates_elected <- candidate_votes_per_election_domain |> filter(elected) |> distinct(election_id, election_domain, party_id, initials, first_name, prefix, last_name)
    n_elected_candidates = nrow(candidates_elected)
    candidates_missing <- anti_join(elected, candidates_elected, by = join_by(election_id, election_domain, party_id, initials, first_name, prefix, last_name))
    
    if (n_elected != n_elected_candidates) {
        # print warning with number of elected 
        cat("Warning: number of elected candidates does not match number of candidates with votes in", path, ": ", n_elected, "vs.", n_elected_candidates, "\n")
    }
    
    if (nrow(candidates_missing) > 0) {
        cat("Warning: missing candidate data in", path, "\n")
        print(candidates_missing)
    }

    candidate_votes_per_election_domain
}

# for each subfolder of data/clean, run combine_candidate_data, and store the results
subdirs <- list.dirs("data/clean", FALSE)[-1]
for (dir in subdirs) {
    cat("Processing", dir, "...", "\n")
    candidate_votes_per_election_domain <- combine_candidate_data(file.path("data", "clean", dir))
    
    write_csv(candidate_votes_per_election_domain, file.path("data", "clean", dir, paste0(dir, "_combined.csv")))
}
